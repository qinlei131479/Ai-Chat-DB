"""
数据源管理API
"""

import logging

from fastapi import APIRouter, Request

from common.exception import MyException
from common.permission_util import check_admin_permission
from common.res_decorator import async_json_resp
from common.token_decorator import check_token
from constants.code_enum import SysCodeEnum
from model.db_connection_pool import get_db_pool
from model.schemas import (
    CheckDatasourceRequest,
    CreateDatasourceRequest,
    DatasourceAuthRequest,
    GetFieldsByConfRequest,
    GetTablesByConfRequest,
    PreviewDataRequest,
    SaveFieldRequest,
    SaveTableRequest,
    SyncTablesRequest,
    TableRelationRequest,
    UpdateDatasourceRequest,
)
from services.datasource_service import DatasourceService
from services.user_service import get_user_info

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasource", tags=["数据服务"])


@router.get("/list")
@check_token
@async_json_resp
async def get_datasource_list(request: Request):
    """获取数据源列表"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:

            user_info = await get_user_info(request)
            datasources = DatasourceService.get_datasource_list(
                session, user_info["id"]
            )

            result = []
            for ds in datasources:
                # 解密配置信息
                configuration = ds.configuration
                if configuration:
                    try:
                        import json

                        from common.datasource_util import DatasourceConfigUtil

                        config_dict = DatasourceConfigUtil.decrypt_config(configuration)
                        configuration = json.dumps(config_dict)
                    except Exception as e:
                        logger.error(f"解密配置失败: {e}")
                        # 如果解密失败，尝试判断是否为明文（JSON或Python Dict字符串）并标准化为JSON
                        try:
                            import json

                            # 尝试作为JSON解析
                            json.loads(configuration)
                        except:
                            try:
                                import ast

                                config_dict = ast.literal_eval(configuration)
                            except:
                                # 确实无法解析，保持原样
                                pass
                result.append(
                    {
                        "id": ds.id,
                        "name": ds.name,
                        "description": ds.description,
                        "type": ds.type,
                        "type_name": ds.type_name,
                        "status": ds.status,
                        "num": ds.num,
                        "host": config_dict["host"],
                        "database": config_dict["database"],
                        "create_time": (
                            ds.create_time.isoformat() if ds.create_time else None
                        ),
                    }
                )

            return result
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取数据源列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取数据源列表失败: {str(e)}")


@router.post("/add")
@check_token
@async_json_resp
async def create_datasource(request: Request, body: CreateDatasourceRequest):
    """创建数据源（仅管理员）
    :param request: 请求对象
    :param body: 创建数据源请求体（自动从请求中解析）
    """
    # 检查管理员权限
    await check_admin_permission(request)

    try:
        data = body.model_dump()

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            user_info = await get_user_info(request)
            datasource = DatasourceService.create_datasource(
                session, data, user_info["id"]
            )

            return {
                "id": datasource.id,
                "name": datasource.name,
                "type": datasource.type,
                "status": datasource.status,
            }
    except MyException:
        raise
    except Exception as e:
        logger.error(f"创建数据源失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"创建数据源失败: {str(e)}")


@router.post("/update")
@check_token
@async_json_resp
async def update_datasource(request: Request, body: UpdateDatasourceRequest):
    """更新数据源（仅管理员）
    :param request: 请求对象
    :param body: 更新数据源请求体（自动从请求中解析）
    """
    # 检查管理员权限
    await check_admin_permission(request)

    try:
        data = body.model_dump()
        ds_id = data.get("id")
        if not ds_id:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少数据源ID")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            datasource = DatasourceService.update_datasource(session, ds_id, data)
            if not datasource:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            return {
                "id": datasource.id,
                "name": datasource.name,
            }
    except MyException:
        raise
    except Exception as e:
        logger.error(f"更新数据源失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"更新数据源失败: {str(e)}")


@router.post("/syncTables/{ds_id}")
@check_token
@async_json_resp
async def sync_tables(request: Request, ds_id: int, body: SyncTablesRequest):
    """同步数据源表和字段（仅管理员）
    :param request: 请求对象
    :param ds_id: 数据源ID（路径参数）
    :param body: 同步表请求体（自动从请求中解析）
    """
    # 检查管理员权限
    await check_admin_permission(request)

    try:
        data = body.tables if body.tables else []
        is_select_all = getattr(body, "is_select_all", False)  # 获取是否全选标志

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = DatasourceService.sync_tables(session, ds_id, data, is_select_all)
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            # 返回同步结果，包含选择的表数量信息
            return {
                "message": "同步成功",
                "table_count": len(data),
                "is_select_all": is_select_all,
            }
    except MyException:
        raise
    except Exception as e:
        logger.error(f"同步表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"同步表失败: {str(e)}")


@router.post("/delete/{ds_id}")
@check_token
@async_json_resp
async def delete_datasource(request: Request, ds_id: int):
    """删除数据源（仅管理员）"""
    # 检查管理员权限
    await check_admin_permission(request)

    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = DatasourceService.delete_datasource(session, ds_id)
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND.value, "数据源不存在")

            return {"message": "删除成功"}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"删除数据源失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"删除数据源失败: {str(e)}")


@router.post("/get/{ds_id}")
@check_token
@async_json_resp
async def get_datasource(request: Request, ds_id: int):
    """获取数据源详情"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            datasource = DatasourceService.get_datasource_by_id(session, ds_id)
            if not datasource:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            # 解密配置信息
            configuration = datasource.configuration
            if configuration:
                try:
                    import json

                    from common.datasource_util import DatasourceConfigUtil

                    config_dict = DatasourceConfigUtil.decrypt_config(configuration)
                    configuration = json.dumps(config_dict)
                except Exception as e:
                    logger.error(f"解密配置失败: {e}")
                    # 如果解密失败，尝试判断是否为明文（JSON或Python Dict字符串）并标准化为JSON
                    try:
                        import json

                        # 尝试作为JSON解析
                        json.loads(configuration)
                    except:
                        try:
                            # 尝试作为Python Dict解析 (例如 {'a': 1})
                            import ast

                            config_dict = ast.literal_eval(configuration)
                            if isinstance(config_dict, dict):
                                configuration = json.dumps(config_dict)
                        except:
                            # 确实无法解析，保持原样
                            pass

            return {
                "id": datasource.id,
                "name": datasource.name,
                "description": datasource.description,
                "type": datasource.type,
                "type_name": datasource.type_name,
                "configuration": configuration,
                "status": datasource.status,
                "num": datasource.num,
                "table_relation": datasource.table_relation,
                "create_time": (
                    datasource.create_time.isoformat()
                    if datasource.create_time
                    else None
                ),
            }
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取数据源详情失败: {e}", exc_info=True)
        raise MyException(
            SysCodeEnum.SYSTEM_ERROR.value, f"获取数据源详情失败: {str(e)}"
        )


@router.post("/check")
@check_token
@async_json_resp
async def check_datasource(request: Request, body: CheckDatasourceRequest):
    """测试数据源连接
    :param request: 请求对象
    :param body: 测试连接请求体（自动从请求中解析）
    """
    try:
        ds_id = body.id
        ds_type = body.type
        configuration = body.configuration

        # 如果提供了配置信息，直接测试
        if ds_type and configuration:
            is_connected, error_message = DatasourceService.check_connection_by_config(
                ds_type, configuration
            )
            return {"connected": is_connected, "error_message": error_message}

        # 否则根据ID获取数据源测试
        if not ds_id:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少数据源ID或配置信息")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            datasource = DatasourceService.get_datasource_by_id(session, ds_id)
            if not datasource:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            # 测试连接
            is_connected, error_message = DatasourceService.check_connection(datasource)

            return {"connected": is_connected, "error_message": error_message}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"测试连接失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR.value, f"测试连接失败: {str(e)}")


@router.post("/getTablesByConf")
@check_token
@async_json_resp
async def get_tables_by_conf(request: Request, body: GetTablesByConfRequest):
    """根据配置获取表列表
    :param request: 请求对象
    :param body: 配置请求体（自动从请求中解析）
    """
    try:
        ds_type = body.type
        configuration = body.configuration

        tables = DatasourceService.get_tables_by_config(ds_type, configuration)

        return tables
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取表列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR.value, f"获取表列表失败: {str(e)}")


@router.post("/getFieldsByConf")
@check_token
@async_json_resp
async def get_fields_by_conf(request: Request, body: GetFieldsByConfRequest):
    """根据配置获取字段列表
    :param request: 请求对象
    :param body: 配置请求体（自动从请求中解析）
    """
    try:
        ds_type = body.type
        config = body.configuration
        table_name = body.table_name
        fields = DatasourceService.get_fields_by_config(ds_type, config, table_name)
        return fields
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取字段列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取字段列表失败: {str(e)}")


@router.post("/tableList/{ds_id}")
@check_token
@async_json_resp
async def get_table_list(request: Request, ds_id: int):
    """获取数据源表列表"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            tables = DatasourceService.get_tables_by_ds_id(session, ds_id)

            result = []
            for table in tables:
                result.append(
                    {
                        "id": table.id,
                        "ds_id": table.ds_id,
                        "table_name": table.table_name,
                        "table_comment": table.table_comment,
                        "custom_comment": table.custom_comment,
                        "checked": table.checked,
                    }
                )

            return result
    except Exception as e:
        logger.error(f"获取表列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取表列表失败: {str(e)}")


@router.post("/fieldList/{table_id}")
@check_token
@async_json_resp
async def get_field_list(request: Request, table_id: int):
    """获取表字段列表"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            fields = DatasourceService.get_fields_by_table_id(session, table_id)

            result = []
            for field in fields:
                result.append(
                    {
                        "id": field.id,
                        "ds_id": field.ds_id,
                        "table_id": field.table_id,
                        "field_name": field.field_name,
                        "field_type": field.field_type,
                        "field_comment": field.field_comment,
                        "custom_comment": field.custom_comment,
                        "field_index": field.field_index,
                        "checked": field.checked,
                    }
                )

            return result
    except Exception as e:
        logger.error(f"获取字段列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取字段列表失败: {str(e)}")


@router.post("/saveTable")
@check_token
@async_json_resp
async def save_table(request: Request, body: SaveTableRequest):
    """保存表信息
    :param request: 请求对象
    :param body: 保存表请求体（自动从请求中解析）
    """
    try:
        data = body.model_dump()
        table_id = data.get("id")
        if not table_id:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少表ID")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = DatasourceService.save_table(session, data)
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "表不存在")

            return {"message": "保存成功"}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"保存表信息失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"保存表信息失败: {str(e)}")


@router.post("/saveField")
@check_token
@async_json_resp
async def save_field(request: Request, body: SaveFieldRequest):
    """保存字段信息
    :param request: 请求对象
    :param body: 保存字段请求体（自动从请求中解析）
    """
    try:
        data = body.model_dump()
        field_id = data.get("id")
        if not field_id:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少字段ID")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = DatasourceService.save_field(session, data)
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "字段不存在")

            return {"message": "保存成功"}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"保存字段信息失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"保存字段信息失败: {str(e)}")


@router.post("/previewData")
@check_token
@async_json_resp
async def preview_data(request: Request, body: PreviewDataRequest):
    """预览表数据
    :param request: 请求对象
    :param body: 预览数据请求体（自动从请求中解析）
    """
    try:
        table = body.table
        fields = body.fields if body.fields else []

        if not table or not table.get("table_name"):
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少表信息")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            preview_result = DatasourceService.preview_table_data(
                session, body.ds_id, table, fields
            )
            return preview_result
    except MyException:
        raise
    except Exception as e:
        logger.error(f"预览数据失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"预览数据失败: {str(e)}")


@router.post("/tableRelation")
@check_token
@async_json_resp
async def save_table_relation(request: Request, body: TableRelationRequest):
    """保存表关系
    :param request: 请求对象
    :param body: 表关系请求体（自动从请求中解析）
    """
    try:
        relation_data = body.relations if body.relations else []

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = DatasourceService.save_table_relation(
                session, body.ds_id, relation_data
            )
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            return {"message": "保存成功"}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"保存表关系失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"保存表关系失败: {str(e)}")


@router.post("/getTableRelation/{ds_id}")
@check_token
@async_json_resp
async def get_table_relation(request: Request, ds_id: int):
    """获取表关系"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            relation_data = DatasourceService.get_table_relation(session, ds_id)
            return relation_data or []
    except Exception as e:
        logger.error(f"获取表关系失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取表关系失败: {str(e)}")


@router.post("/getAuthorizedUsers/{datasource_id}")
@check_token
@async_json_resp
async def get_authorized_users(request: Request, datasource_id: int):
    """获取已授权用户（仅管理员）
    :param request: 请求对象
    :param datasource_id: 数据源ID
    """
    # 检查管理员权限
    await check_admin_permission(request)

    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            # 检查数据源是否存在
            datasource = DatasourceService.get_datasource_by_id(session, datasource_id)
            if not datasource:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            # 获取已授权的用户ID列表
            user_ids = DatasourceService.get_authorized_users(session, datasource_id)
            return user_ids
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取已授权用户失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取已授权用户失败: {str(e)}")


@router.post("/authorize")
@check_token
@async_json_resp
async def authorize_datasource(request: Request, body: DatasourceAuthRequest):
    """数据源授权（仅管理员）
    :param request: 请求对象
    :param body: 授权请求体（自动从请求中解析）
    """
    # 检查管理员权限
    await check_admin_permission(request)

    try:
        datasource_id = body.datasource_id
        user_ids = body.user_ids

        if not datasource_id:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少数据源ID")
        # 允许空列表，用于清空授权
        if user_ids is None:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少用户ID列表")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            # 检查数据源是否存在
            datasource = DatasourceService.get_datasource_by_id(session, datasource_id)
            if not datasource:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            # 执行授权
            success = DatasourceService.authorize_datasource(
                session, datasource_id, user_ids
            )
            if not success:
                raise MyException(SysCodeEnum.SYSTEM_ERROR, "授权失败")

            return {"message": "授权成功"}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"数据源授权失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"数据源授权失败: {str(e)}")
