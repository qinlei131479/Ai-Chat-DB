import json
import logging
import httpx
from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc

from common.exception import MyException
from constants.code_enum import ModelTypeEnum, SysCodeEnum
from model.db_connection_pool import get_db_pool
from model.db_models import Supplier, SupplierModel
from model.serializers import model_to_dict

logger = logging.getLogger(__name__)
pool = get_db_pool()


def _merge_model_with_supplier(model: SupplierModel, supplier: Supplier) -> dict:
    """将 SupplierModel 和 Supplier 合并为前端期望的平坦结构，保持与旧接口的字段兼容性。"""
    result = model_to_dict(model)
    result['id'] = str(model.id)
    result['supplier'] = supplier.id if supplier else None
    result['supplier_name'] = supplier.name if supplier else None
    result['api_key'] = supplier.api_key if supplier else None
    result['api_domain'] = supplier.api_domain if supplier else None
    result['protocol'] = 1
    # 字段映射：default_flag('0'/'1') -> default_model(bool)
    result['default_model'] = (result.get('default_flag') == '1')
    # 字段映射：ext_config -> config（保留两个键以兼容不同调用方）
    result['config'] = result.get('ext_config')
    return result


async def query_model_list(keyword: str = None, model_type: int = None) -> List[dict]:
    with pool.get_session() as session:
        query = session.query(SupplierModel, Supplier).join(
            Supplier, SupplierModel.supplier_id == Supplier.id
        ).filter(SupplierModel.del_flag == '0')

        if keyword:
            query = query.filter(SupplierModel.name.like(f"%{keyword}%"))
        if model_type:
            query = query.filter(SupplierModel.model_type == str(model_type))

        rows = query.order_by(desc(SupplierModel.default_flag), SupplierModel.name).all()

        result = []
        for model, supplier in rows:
            result.append(_merge_model_with_supplier(model, supplier))
        return result


async def get_model_detail(model_id: int) -> dict:
    with pool.get_session() as session:
        row = session.query(SupplierModel, Supplier).join(
            Supplier, SupplierModel.supplier_id == Supplier.id
        ).filter(
            SupplierModel.id == model_id,
            SupplierModel.del_flag == '0'
        ).first()

        if not row:
            raise MyException(SysCodeEnum.PARAM_ERROR, "Model not found")

        model, supplier = row
        data = _merge_model_with_supplier(model, supplier)

        ext_config = data.get('ext_config')
        if ext_config:
            try:
                data['config_list'] = json.loads(ext_config)
            except Exception:
                data['config_list'] = []
        else:
            data['config_list'] = []
        return data


async def add_model(data: dict) -> bool:
    with pool.get_session() as session:
        supplier_id = data.get('supplier')
        model_type = str(data.get('model_type', 1))

        # 若前端传入 api_key/api_domain，同步更新对应 Supplier 记录
        supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
        if supplier:
            api_key = data.get('api_key')
            if api_key is not None:
                supplier.api_key = api_key.strip() if api_key.strip() else None
            if data.get('api_domain'):
                supplier.api_domain = data['api_domain']
            supplier.update_time = datetime.now()

        # 仅聊天模型（CHAT）在首次添加时自动设为默认
        is_default = '0'
        if model_type == ModelTypeEnum.CHAT.value[0]:
            count = session.query(SupplierModel).filter(
                SupplierModel.model_type == ModelTypeEnum.CHAT.value[0],
                SupplierModel.del_flag == '0'
            ).count()
            is_default = '1' if count == 0 else '0'

        config_list = data.get('config_list', [])
        ext_config = json.dumps(config_list) if config_list else None

        now = datetime.now()
        new_model = SupplierModel(
            supplier_id=supplier_id,
            name=data['name'],
            base_model=data['base_model'],
            model_type=model_type,
            description=data.get('description', ''),
            context_length=data.get('context_length', ''),
            default_flag=is_default,
            ext_config=ext_config,
            del_flag='0',
            create_by=data.get('create_by', 'system'),
            update_by=data.get('update_by', 'system'),
            create_time=now,
            update_time=now,
        )
        session.add(new_model)
        session.commit()
        return True


async def update_model(model_id: int, data: dict) -> bool:
    with pool.get_session() as session:
        row = session.query(SupplierModel, Supplier).join(
            Supplier, SupplierModel.supplier_id == Supplier.id
        ).filter(
            SupplierModel.id == model_id,
            SupplierModel.del_flag == '0'
        ).first()

        if not row:
            raise MyException(SysCodeEnum.PARAM_ERROR, "Model not found")

        model, supplier = row

        # 更新 SupplierModel 字段
        if 'name' in data:
            model.name = data['name']
        if 'base_model' in data:
            model.base_model = data['base_model']
        if 'model_type' in data:
            model.model_type = str(data['model_type'])
        if 'description' in data:
            model.description = data['description']
        if 'context_length' in data:
            model.context_length = data['context_length']
        if 'config_list' in data:
            model.ext_config = json.dumps(data['config_list'])

        # 若前端切换了供应商
        new_supplier_id = data.get('supplier')
        if new_supplier_id and new_supplier_id != model.supplier_id:
            model.supplier_id = new_supplier_id
            supplier = session.query(Supplier).filter(Supplier.id == new_supplier_id).first()

        model.update_by = data.get('update_by', 'system')
        model.update_time = datetime.now()

        # 同步更新 Supplier 的 api_key / api_domain
        if supplier:
            if 'api_key' in data:
                api_key = data['api_key']
                if api_key is not None and api_key.strip() == '':
                    api_key = None
                supplier.api_key = api_key
            if 'api_domain' in data:
                supplier.api_domain = data['api_domain']
            supplier.update_time = datetime.now()

        session.commit()
        return True


async def delete_model(model_id: int) -> bool:
    with pool.get_session() as session:
        model = session.query(SupplierModel).filter(
            SupplierModel.id == model_id,
            SupplierModel.del_flag == '0'
        ).first()
        if not model:
            raise MyException(SysCodeEnum.PARAM_ERROR, "Model not found")

        if model.default_flag == '1':
            raise MyException(SysCodeEnum.PARAM_ERROR, "Cannot delete default model")

        model.del_flag = '1'
        model.update_time = datetime.now()
        session.commit()
        return True


async def set_default_model(model_id: int) -> bool:
    with pool.get_session() as session:
        model = session.query(SupplierModel).filter(
            SupplierModel.id == model_id,
            SupplierModel.del_flag == '0'
        ).first()
        if not model:
            raise MyException(SysCodeEnum.PARAM_ERROR, "Model not found")

        if model.model_type != ModelTypeEnum.CHAT.value[0]:
            raise MyException(SysCodeEnum.PARAM_ERROR, "只有聊天模型才能设为默认")

        if model.default_flag == '1':
            return True

        # 取消原有默认聊天模型
        session.query(SupplierModel).filter(
            SupplierModel.default_flag == '1',
            SupplierModel.model_type == ModelTypeEnum.CHAT.value[0],
            SupplierModel.del_flag == '0'
        ).update({SupplierModel.default_flag: '0'})

        model.default_flag = '1'
        session.commit()
        return True


async def query_supplier_list() -> List[dict]:
    """查询所有可用供应商列表（id + name + api_domain + api_key）。"""
    with pool.get_session() as session:
        suppliers = session.query(Supplier).filter(
            Supplier.del_flag == '0'
        ).order_by(Supplier.id).all()
        return [
            {
                'id': s.id,
                'name': s.name,
                'api_domain': s.api_domain or '',
                'api_key': s.api_key or '',
            }
            for s in suppliers
        ]


async def get_default_model() -> Optional[dict]:
    """查询默认聊天模型，同时返回供应商的 api_key / api_domain 信息。"""
    with pool.get_session() as session:
        row = session.query(SupplierModel, Supplier).join(
            Supplier, SupplierModel.supplier_id == Supplier.id
        ).filter(
            SupplierModel.default_flag == '1',
            SupplierModel.model_type == ModelTypeEnum.CHAT.value[0],
            SupplierModel.del_flag == '0'
        ).first()

        if not row:
            return None

        model, supplier = row
        return _merge_model_with_supplier(model, supplier)


async def check_llm_status(data: dict) -> dict:
    """测试模型连接状态，supplier 字段对应 Supplier 表的 id。"""
    supplier_id = data.get('supplier', 1)
    api_key = data.get('api_key') or ''
    api_domain = data.get('api_domain', '')

    # 未传入 api_key / api_domain 时，从 Supplier 表补充
    if not api_key or not api_domain:
        with pool.get_session() as session:
            supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
            if supplier:
                api_key = api_key or supplier.api_key or ''
                api_domain = api_domain or supplier.api_domain or ''

    if not api_domain:
        return {"success": False, "message": "API 域名不能为空"}

    try:
        if supplier_id == 3:  # Ollama
            domain = api_domain
            if domain.endswith('/v1'):
                domain = domain[:-3]
            url = f"{domain}/api/tags"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=5)
                resp.raise_for_status()
                return {"success": True, "message": "连接成功"}

        if supplier_id == 1:  # OpenAI
            domain = api_domain or "https://api.openai.com/v1"
            url = f"{domain}/models"
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                return {"success": True, "message": "连接成功"}

        elif supplier_id == 4:  # vLLM
            url = f"{api_domain}/models"
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=5)
                resp.raise_for_status()
                return {"success": True, "message": "连接成功"}

        elif supplier_id == 10:  # MiniMax
            domain = api_domain
            url = f"{domain}/models"
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, headers=headers, timeout=10)
                    resp.raise_for_status()
                    return {"success": True, "message": "连接成功"}
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    try:
                        async with httpx.AsyncClient() as client:
                            base_domain = domain.replace('/v1', '')
                            resp = await client.head(base_domain, timeout=5)
                            return {"success": True, "message": "连接成功"}
                    except Exception:
                        return {"success": False, "message": "无法连接到API域名，请检查网络和域名配置"}
                elif e.response.status_code == 401:
                    return {"success": False, "message": "API Key 无效或未授权"}
                else:
                    return {"success": False, "message": f"连接失败: HTTP {e.response.status_code}"}
            except httpx.TimeoutException:
                return {"success": False, "message": "连接超时，请检查网络或API域名"}
            except httpx.ConnectError:
                return {"success": False, "message": "无法连接到服务器，请检查API域名"}
            except Exception as e:
                logger.error(f"MiniMax连接测试失败: {e}")
                return {"success": False, "message": f"连接失败: {str(e)}"}

        else:
            domain = api_domain
            url = f"{domain}/models"
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                return {"success": True, "message": "连接成功"}

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return {"success": False, "message": "API Key 无效或未授权"}
        elif e.response.status_code == 404:
            if supplier_id == 10:
                return {"success": False,
                        "message": "API 端点不存在，请检查 API 域名。MiniMax 可能需要使用完整的模型列表端点"}
            return {"success": False, "message": "API 端点不存在，请检查 API 域名"}
        else:
            return {"success": False, "message": f"连接失败: HTTP {e.response.status_code}"}
    except httpx.TimeoutException:
        return {"success": False, "message": "连接超时，请检查网络或 API 域名"}
    except httpx.ConnectError:
        return {"success": False, "message": "无法连接到服务器，请检查 API 域名"}
    except Exception as e:
        logger.error(f"测试模型连接失败: {e}")
        return {"success": False, "message": f"连接失败: {str(e)}"}


async def fetch_base_models(supplier: int, api_key: str = None, api_domain: str = None) -> List[str]:
    """拉取指定供应商的可用基础模型列表。supplier 为 Supplier 表的 id。"""
    # 未传入 api_key / api_domain 时，从 Supplier 表补充
    if not api_key or not api_domain:
        with pool.get_session() as session:
            supplier_rec = session.query(Supplier).filter(Supplier.id == supplier).first()
            if supplier_rec:
                api_key = api_key or supplier_rec.api_key
                api_domain = api_domain or supplier_rec.api_domain

    try:
        if supplier == 1:  # OpenAI
            if not api_key:
                return []
            domain = api_domain or "https://api.openai.com/v1"
            url = f"{domain}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                models = [m['id'] for m in data.get('data', []) if 'gpt' in m['id']]
                return sorted(models)

        elif supplier == 3:  # Ollama
            domain = api_domain or "http://localhost:11434"
            if domain.endswith('/v1'):
                domain = domain[:-3]
            url = f"{domain}/api/tags"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=5)
                resp.raise_for_status()
                data = resp.json()
                models = [m['name'] for m in data.get('models', [])]
                return sorted(models)

        elif supplier == 4:  # vLLM
            if not api_domain:
                return []
            url = f"{api_domain}/models"
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=5)
                resp.raise_for_status()
                data = resp.json()
                models = [m['id'] for m in data.get('data', [])]
                return sorted(models)

        elif supplier == 5:  # DeepSeek
            if not api_key:
                return []
            domain = api_domain or "https://api.deepseek.com"
            url = f"{domain}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                models = [m['id'] for m in data.get('data', [])]
                return sorted(models)

        elif supplier == 10:  # MiniMax
            if not api_key:
                return []
            domain = api_domain or "https://api.minimaxi.com/v1"
            url = f"{domain}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, headers=headers, timeout=10)
                    resp.raise_for_status()
                    data = resp.json()
                    if 'data' in data:
                        models = [m['id'] for m in data.get('data', [])]
                    else:
                        models = [m['id'] for m in data] if isinstance(data, list) else []
                    return sorted(models)
            except Exception:
                return ["MiniMax-M2.1", "abab6.5s-chat", "abab5.5-chat"]

        return []

    except Exception as e:
        logger.error(f"Failed to fetch models for supplier {supplier}: {e}")
        return []
