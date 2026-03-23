import logging
import traceback
from typing import List, Optional

from openai import AsyncOpenAI

from model.db_connection_pool import get_db_pool
from model.db_models import Supplier, SupplierModel

logger = logging.getLogger(__name__)
pool = get_db_pool()


async def get_default_embedding_model():
    """
    获取默认的 embedding 模型配置。
    只查找 Embedding 类型的模型（model_type='2'），JOIN Supplier 表获取 api_key / api_domain。
    """
    with pool.get_session() as session:
        # 优先取标记为默认的 embedding 模型
        row = session.query(SupplierModel, Supplier).join(
            Supplier, SupplierModel.supplier_id == Supplier.id
        ).filter(
            SupplierModel.model_type == '2',
            SupplierModel.default_flag == '1',
            SupplierModel.del_flag == '0'
        ).first()

        # 无默认则取任意一个可用的 embedding 模型
        if not row:
            row = session.query(SupplierModel, Supplier).join(
                Supplier, SupplierModel.supplier_id == Supplier.id
            ).filter(
                SupplierModel.model_type == '2',
                SupplierModel.del_flag == '0'
            ).first()

        if row:
            model, supplier = row
            return {
                "supplier": supplier.id,
                "api_key": supplier.api_key,
                "api_domain": supplier.api_domain,
                "base_model": model.base_model,
            }

        # 没有配置 embedding 模型，返回 None（将使用离线本地模型）
        return None


async def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding for the given text"""
    if not text:
        return None

    model = await get_default_embedding_model()

    # 若未配置在线 embedding 模型，使用离线本地模型
    if not model:
        logger.info("No embedding model configured, falling back to local CPU model")
        from common.local_embedding import generate_embedding_local
        return await generate_embedding_local(text)

    try:
        api_key = model["api_key"] or "empty"
        base_url = model.get("api_domain") or ""

        if not base_url or not base_url.strip():
            logger.warning("API domain is empty, falling back to local CPU model")
            from common.local_embedding import generate_embedding_local
            return await generate_embedding_local(text)

        base_url = base_url.strip()
        if not base_url.startswith(("http://", "https://")):
            if base_url.startswith(("localhost", "127.0.0.1", "0.0.0.0")):
                base_url = f"http://{base_url}"
            else:
                base_url = f"https://{base_url}"

        # Ollama 需要确保 base_url 以 /v1 结尾
        if model["supplier"] == 3:
            if not base_url.endswith("/v1"):
                base_url = f"{base_url.rstrip('/')}/v1"

        async with AsyncOpenAI(api_key=api_key, base_url=base_url) as client:
            response = await client.embeddings.create(model=model["base_model"], input=text)

            if response.data:
                return response.data[0].embedding

    except Exception as e:
        traceback.print_exc()
        logger.warning(f"Failed to generate embedding with online model: {e}, falling back to local CPU model")
        from common.local_embedding import generate_embedding_local
        return await generate_embedding_local(text)

    return None
