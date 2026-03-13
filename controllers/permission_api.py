import logging

from fastapi import APIRouter

from services.permission_service import PermissionService
from model.db_connection_pool import get_db_pool
from common.res_decorator import success_response
from common.exception import MyException
from constants.code_enum import SysCodeEnum
from model.schemas import SavePermissionRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ds_permission", tags=["权限管理"])


@router.post("/list", summary="获取权限规则列表")
async def get_permission_list():
    """获取所有权限规则"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            result = PermissionService.get_list(session)
            return success_response(result)
    except Exception as e:
        logger.error(f"获取权限列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取权限列表失败: {str(e)}")


@router.post("/save", summary="保存权限规则")
async def save_permission(body: SavePermissionRequest):
    """创建或更新权限规则"""
    try:
        data = body.model_dump()

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = PermissionService.save_permission(session, data)
            if not success:
                raise MyException(SysCodeEnum.SYSTEM_ERROR, "保存失败")
            return success_response({"message": "保存成功"})
    except MyException:
        raise
    except Exception as e:
        logger.error(f"保存权限规则失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"保存权限规则失败: {str(e)}")


@router.post("/delete/{rule_id}", summary="删除权限规则")
async def delete_permission(rule_id: int):
    """删除指定的权限规则"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = PermissionService.delete_permission(session, rule_id)
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "规则不存在")
            return success_response({"message": "删除成功"})
    except MyException:
        raise
    except Exception as e:
        logger.error(f"删除权限规则失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"删除权限规则失败: {str(e)}")
