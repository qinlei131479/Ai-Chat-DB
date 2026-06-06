import logging

from fastapi import APIRouter, Request

from common.exception import MyException
from common.res_decorator import async_json_resp
from constants.code_enum import SysCodeEnum
from model.db_connection_pool import get_db_pool
from model.schemas import SavePermissionRequest
from services.permission_service import PermissionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ds_permission", tags=["权限管理"])


@router.post("/list")
@async_json_resp
async def get_permission_list(request: Request):
    """获取权限规则列表"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            return PermissionService.get_list(session)
    except Exception as e:
        logger.error(f"获取权限列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取权限列表失败: {str(e)}")


@router.post("/save")
@async_json_resp
async def save_permission(request: Request, body: SavePermissionRequest):
    """保存权限规则"""
    try:
        data = body.model_dump()
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = PermissionService.save_permission(session, data)
            if not success:
                raise MyException(SysCodeEnum.SYSTEM_ERROR, "保存失败")
            return {"message": "保存成功"}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"保存权限规则失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"保存权限规则失败: {str(e)}")


@router.post("/delete/{rule_id}")
@async_json_resp
async def delete_permission(request: Request, rule_id: int):
    """删除权限规则"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = PermissionService.delete_permission(session, rule_id)
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "规则不存在")
            return {"message": "删除成功"}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"删除权限规则失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"删除权限规则失败: {str(e)}")
