"""
技能管理API
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends

from common.res_decorator import success_response
from common.token_decorator import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system/skill", tags=["技能管理"])


def parse_skill_markdown(file_path: Path) -> dict:
    """解析 SKILL.md 文件，提取 front matter 中的 name 和 description"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                front_matter = parts[1].strip()
                name = None
                description = None

                for line in front_matter.split("\n"):
                    line = line.strip()
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("description:"):
                        description = (
                            line.split(":", 1)[1].strip().strip('"').strip("'")
                        )

                return {
                    "name": name or file_path.parent.name,
                    "description": description or "",
                }
    except Exception as e:
        logger.error(f"解析技能文件失败 {file_path}: {e}")

    return {"name": file_path.parent.name, "description": ""}


@router.get("/list", summary="获取技能列表")
async def get_skill_list(user: dict = Depends(get_current_user)):
    """获取深度问数技能列表"""
    try:
        current_file = Path(__file__)
        project_root = current_file.parent.parent
        skills_dir = project_root / "agent" / "deepagent" / "skills"

        skills = []

        if skills_dir.exists() and skills_dir.is_dir():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir():
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        skill_info = parse_skill_markdown(skill_file)
                        skills.append(skill_info)

        skills.sort(key=lambda x: x["name"])

        return success_response(skills)
    except Exception as e:
        logger.error(f"获取技能列表失败: {e}", exc_info=True)
        raise
