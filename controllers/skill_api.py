"""
技能管理 API
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from common.llm_util import get_llm
from common.res_decorator import async_json_resp
from common.sse_stream import create_sse_response
from common.token_decorator import check_token
from services.skill_service import SkillService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system/skill", tags=["技能管理"])


class GithubInstallRequest(BaseModel):
    repo: str
    skills: Optional[List[str]] = None
    scope: str = "common"


class SkillNameRequest(BaseModel):
    name: str
    scope: str = "common"


class SkillToggleRequest(BaseModel):
    name: str
    enabled: bool
    scope: str = "common"


class SkillTutorialRequest(BaseModel):
    name: str
    scope: str = "common"


def parse_skill_markdown(file_path: Path) -> dict:
    return SkillService._parse_skill_markdown(file_path)


@router.get("/list")
@check_token
@async_json_resp
async def get_skill_list(request: Request, scope: str = Query("common")):
    if scope not in ("common", "deep"):
        scope = "common"
    return SkillService.list_skills(scope=scope)


@router.post("/install/github")
@check_token
@async_json_resp
async def install_from_github(request: Request, body: GithubInstallRequest):
    try:
        scope = body.scope if body.scope in ("common", "deep") else "common"
        if not body.repo:
            return {"success": False, "message": "repo 参数不能为空"}
        return await SkillService.install_from_github(
            body.repo, body.skills, scope=scope
        )
    except Exception as e:
        logger.error(f"从 GitHub 安装技能失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.post("/install/upload")
@check_token
@async_json_resp
async def install_from_upload(
    request: Request,
    file: UploadFile = File(...),
    scope: str = Form("common"),
):
    try:
        if scope not in ("common", "deep"):
            scope = "common"
        zip_bytes = await file.read()
        filename = file.filename or "skills.zip"
        installed = SkillService.install_from_zip(zip_bytes, filename, scope=scope)
        if not installed:
            return {
                "success": False,
                "message": "zip 包中未找到有效的技能文件（需要包含 SKILL.md）",
            }
        return installed
    except Exception as e:
        logger.error(f"从 zip 安装技能失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.post("/uninstall")
@check_token
@async_json_resp
async def uninstall_skill(request: Request, body: SkillNameRequest):
    try:
        scope = body.scope if body.scope in ("common", "deep") else "common"
        if not body.name:
            return {"success": False, "message": "name 参数不能为空"}
        success = SkillService.uninstall_skill(body.name, scope=scope)
        if success:
            return {"success": True, "message": f"技能 '{body.name}' 已卸载"}
        return {"success": False, "message": f"技能 '{body.name}' 不存在或卸载失败"}
    except Exception as e:
        logger.error(f"卸载技能失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.post("/toggle")
@check_token
@async_json_resp
async def toggle_skill(request: Request, body: SkillToggleRequest):
    try:
        scope = body.scope if body.scope in ("common", "deep") else "common"
        if not body.name:
            return {"success": False, "message": "name 参数不能为空"}
        success = SkillService.toggle_skill(body.name, body.enabled, scope=scope)
        if success:
            action = "启用" if body.enabled else "禁用"
            return {"success": True, "message": f"技能 '{body.name}' 已{action}"}
        return {"success": False, "message": f"技能 '{body.name}' 不存在或操作失败"}
    except Exception as e:
        logger.error(f"切换技能状态失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.get("/preview")
@check_token
@async_json_resp
async def preview_github_repo(request: Request, repo: str = Query(...)):
    try:
        if not repo:
            return {"success": False, "message": "repo 参数不能为空"}
        return await SkillService.preview_github_repo(repo)
    except Exception as e:
        logger.error(f"预览 GitHub 仓库技能失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.get("/content")
@check_token
@async_json_resp
async def get_skill_content(
    request: Request,
    name: str = Query(...),
    scope: str = Query("common"),
):
    try:
        if scope not in ("common", "deep"):
            scope = "common"
        skill_data = SkillService.get_skill_content(name, scope=scope)
        if skill_data is not None:
            return skill_data
        return {"success": False, "message": f"技能 '{name}' 不存在或无内容"}
    except Exception as e:
        logger.error(f"获取技能详情失败: {e}", exc_info=True)
        raise


TUTORIAL_PROMPT = """你是一个技能使用指南专家。请仔细阅读以下技能文档，然后以中文输出详细的使用教程。

## 技能文档
{skill_content}

## 输出要求
请按以下格式输出（使用 Markdown 语法）：

# {skill_name} 使用教程

## 技能简介
简要介绍这个技能的功能和用途。

## 何时使用
列出适合使用此技能的场景和条件。

## 使用步骤
分步骤详细说明如何使用这个技能。

## 场景示例
提供 2-3 个具体的实际使用例子，每个例子包含：
- 场景描述
- 使用的提示词示例
- 预期效果

## 注意事项
列出使用此技能时需要注意的关键点。

请直接输出教程内容，不要有多余的开场白。
"""


@router.post("/tutorial")
@check_token
async def get_skill_tutorial(request: Request, body: SkillTutorialRequest):
    scope = body.scope if body.scope in ("common", "deep") else "common"
    if not body.name:
        return JSONResponse(
            content={"success": False, "message": "name 参数不能为空"}
        )

    skill_data = SkillService.get_skill_content(body.name, scope=scope)
    if skill_data is None:
        return JSONResponse(
            content={
                "success": False,
                "message": f"技能 '{body.name}' 不存在或无内容",
            }
        )

    skill_content = skill_data.get("content", "")
    if not skill_content:
        return JSONResponse(
            content={
                "success": False,
                "message": f"技能 '{body.name}' 内容为空",
            }
        )

    async def stream_handler(response):
        try:
            llm = get_llm(temperature=0.7)
            prompt = TUTORIAL_PROMPT.format(
                skill_name=body.name, skill_content=skill_content
            )
            async for chunk in llm.astream(prompt):
                content = chunk.content if hasattr(chunk, "content") else str(chunk)
                if content:
                    await response.write(
                        f"data: {json.dumps({'content': content})}\n\n"
                    )
            await response.write(f"data: {json.dumps({'done': True})}\n\n")
        except Exception as e:
            logger.error(f"LLM 流式调用失败: {e}", exc_info=True)
            await response.write(
                f"data: {json.dumps({'error': f'AI 生成教程失败: {str(e)}'})}\n\n"
            )

    return create_sse_response(request, stream_handler)
