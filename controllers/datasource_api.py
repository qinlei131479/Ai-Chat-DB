"""
数据源管理API
"""

import logging

from fastapi import APIRouter, Depends

from common.exception import MyException
from common.permission_util import get_admin_user
from common.res_decorator import success_response
from common.token_decorator import get_current_user
from constants.code_enum import SysCodeEnum
from model.db_connection_pool import get_db_pool
from model.schemas import (
    CheckDatasourceRequest,
    CreateDatasourceRequest,
    GetFieldsByConfRequest,
    GetTablesByConfRequest,
    PreviewDataRequest,
    SaveFieldRequest,
    SaveTableRequest,
    SyncTablesRequest,
    UpdateDatasourceRequest,
)
from services.datasource_service import DatasourceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasource", tags=["数据服务"])


@router.get("/list", summary="获取数据源列表")
async def get_datasource_list(user: dict = Depends(get_current_user)):
    """获取当前用户的数据源列表"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            datasources = DatasourceService.get_datasource_list(
                session, user["id"]
            )

            result = []
            for ds in datasources:
                result.append(
                    {
                        "id": str(ds.id),
                        "name": ds.name,
                        "description": ds.description,
                        "type": ds.ds_type,
                        "status": ds.status,
                        "num": 0,
                        "host": ds.host,
                        "database": ds.ds_name,
                        "create_time": (
                            ds.create_time.isoformat() if ds.create_time else None
                        ),
                    }
                )

            return success_response(result)
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取数据源列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取数据源列表失败: {str(e)}")


@router.post("/add", summary="创建数据源")
async def create_datasource(
        body: CreateDatasourceRequest, user: dict = Depends(get_admin_user)
):
    """创建数据源（仅管理员）"""
    try:
        data = body.model_dump()
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            datasource = DatasourceService.create_datasource(
                session, data, user["id"]
            )
            return success_response(
                {
                    "id": str(datasource.id),
                    "name": datasource.name,
                    "type": datasource.ds_type,
                    "status": datasource.status,
                }
            )
    except MyException:
        raise
    except Exception as e:
        logger.error(f"创建数据源失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"创建数据源失败: {str(e)}")


@router.post("/update", summary="更新数据源")
async def update_datasource(
        body: UpdateDatasourceRequest, user: dict = Depends(get_admin_user)
):
    """更新数据源（仅管理员）"""
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

            return success_response(
                {"id": str(datasource.id), "name": datasource.name}
            )
    except MyException:
        raise
    except Exception as e:
        logger.error(f"更新数据源失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"更新数据源失败: {str(e)}")


@router.post("/syncTables/{ds_id}", summary="同步数据源表和字段")
async def sync_tables(
        ds_id: int, body: SyncTablesRequest, user: dict = Depends(get_admin_user)
):
    """将前端选择的表列表写入并同步字段（仅管理员）"""
    try:
        data = body.tables if body.tables else []
        is_select_all = getattr(body, "is_select_all", False)

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = DatasourceService.sync_tables(session, ds_id, data, is_select_all)
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            return success_response(
                {
                    "message": "同步成功",
                    "table_count": len(data),
                    "is_select_all": is_select_all,
                }
            )
    except MyException:
        raise
    except Exception as e:
        logger.error(f"同步表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"同步表失败: {str(e)}")


@router.post("/delete/{ds_id}", summary="删除数据源")
async def delete_datasource(ds_id: int, user: dict = Depends(get_admin_user)):
    """删除数据源（仅管理员）"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = DatasourceService.delete_datasource(session, ds_id)
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            return success_response({"message": "删除成功"})
    except MyException:
        raise
    except Exception as e:
        logger.error(f"删除数据源失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"删除数据源失败: {str(e)}")


@router.post("/get/{ds_id}", summary="获取数据源详情")
async def get_datasource(ds_id: int):
    """根据ID获取数据源详情，包含解密后的连接配置供编辑表单回填"""
    try:
        import json as _json
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            datasource = DatasourceService.get_datasource_by_id(session, ds_id)
            if not datasource:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            # 解密连接配置，供前端编辑表单回填
            configuration = None
            try:
                if datasource.conf_type:
                    from common.datasource_util import DatasourceConfigUtil
                    config_dict = DatasourceConfigUtil.decrypt_config(datasource.conf_type)
                    configuration = _json.dumps(config_dict, ensure_ascii=False)
            except Exception as cfg_err:
                logger.warning(f"解密数据源配置失败: {cfg_err}")

            return success_response(
                {
                    "id": str(datasource.id),
                    "name": datasource.name,
                    "description": datasource.description or "",
                    "type": datasource.ds_type,
                    "status": datasource.status,
                    "host": datasource.host or "",
                    "database": datasource.ds_name or "",
                    "configuration": configuration,
                    "create_time": (
                        datasource.create_time.isoformat()
                        if datasource.create_time
                        else None
                    ),
                }
            )
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取数据源详情失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取数据源详情失败: {str(e)}")


@router.post("/check", summary="测试数据源连接")
async def check_datasource(body: CheckDatasourceRequest):
    """测试数据源连接是否正常"""
    try:
        ds_id = body.id
        ds_type = body.type
        configuration = body.configuration

        if ds_type and configuration:
            is_connected, error_message = DatasourceService.check_connection_by_config(
                ds_type, configuration
            )
            return success_response(
                {"connected": is_connected, "error_message": error_message}
            )

        if not ds_id:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少数据源ID或配置信息")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            datasource = DatasourceService.get_datasource_by_id(session, ds_id)
            if not datasource:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            is_connected, error_message = DatasourceService.check_connection(datasource)
            return success_response(
                {"connected": is_connected, "error_message": error_message}
            )
    except MyException:
        raise
    except Exception as e:
        logger.error(f"测试连接失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"测试连接失败: {str(e)}")


@router.post("/getTablesByConf", summary="根据配置获取表列表")
async def get_tables_by_conf(body: GetTablesByConfRequest):
    """根据数据源配置获取表列表"""
    try:
        tables = DatasourceService.get_tables_by_config(body.type, body.configuration)
        return success_response(tables)
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取表列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取表列表失败: {str(e)}")


@router.post("/getFieldsByConf", summary="根据配置获取表字段列表")
async def get_fields_by_conf(body: GetFieldsByConfRequest):
    """提供数据源类型、配置、表名，直接返回字段列表"""
    try:
        fields = DatasourceService.get_fields_by_config(
            body.type, body.configuration, body.table_name
        )
        return success_response(fields)
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取字段列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取字段列表失败: {str(e)}")


@router.post("/tableList/{ds_id}", summary="获取数据源表列表")
async def get_table_list(ds_id: int):
    """获取指定数据源的所有表"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            tables = DatasourceService.get_tables_by_ds_id(session, ds_id)

            result = []
            for table in tables:
                result.append(
                    {
                        "id": str(table.id),
                        "ds_id": str(table.ds_id),
                        "table_name": table.table_name,
                        "table_comment": table.table_comment,
                        "custom_comment": table.custom_comment,
                        "checked": table.checked_flag == 1,
                    }
                )

            return success_response(result)
    except Exception as e:
        logger.error(f"获取表列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取表列表失败: {str(e)}")


@router.post("/fieldList/{table_id}", summary="获取表字段列表")
async def get_field_list(table_id: int):
    """获取指定表的所有字段"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            fields = DatasourceService.get_fields_by_table_id(session, table_id)

            result = []
            for field in fields:
                result.append(
                    {
                        "id": str(field.id),
                        "ds_id": str(field.ds_id),
                        "table_id": str(field.table_id),
                        "field_name": field.field_name,
                        "field_type": field.field_type,
                        "field_comment": field.field_comment,
                        "custom_comment": field.custom_comment,
                        "weight": field.weight,
                        "checked": True,
                    }
                )

            return success_response(result)
    except Exception as e:
        logger.error(f"获取字段列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取字段列表失败: {str(e)}")


@router.post("/saveTable", summary="保存表信息")
async def save_table(body: SaveTableRequest):
    """保存表的自定义注释等信息"""
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

            return success_response({"message": "保存成功"})
    except MyException:
        raise
    except Exception as e:
        logger.error(f"保存表信息失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"保存表信息失败: {str(e)}")


@router.post("/saveField", summary="保存字段信息")
async def save_field(body: SaveFieldRequest):
    """保存字段的自定义注释和状态等信息"""
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

            return success_response({"message": "保存成功"})
    except MyException:
        raise
    except Exception as e:
        logger.error(f"保存字段信息失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"保存字段信息失败: {str(e)}")


@router.post("/previewData", summary="预览表数据")
async def preview_data(body: PreviewDataRequest):
    """预览指定表的数据（最多100条）"""
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
            return success_response(preview_result)
    except MyException:
        raise
    except Exception as e:
        logger.error(f"预览数据失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"预览数据失败: {str(e)}")


@router.post("/getNeo4jRelation/{ds_id}", summary="获取 Neo4j 图数据库关系")
async def get_neo4j_relation(ds_id: int):
    """从 Neo4j 图数据库获取数据源的表关系数据"""
    try:
        relation_data = DatasourceService.get_neo4j_relation(ds_id)
        return success_response(relation_data or [])
    except Exception as e:
        logger.error(f"获取 Neo4j 关系失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取 Neo4j 关系失败: {str(e)}")
