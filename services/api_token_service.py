"""API Token 管理服务"""

import logging
import os
from datetime import datetime
from typing import Optional

from common.exception import MyException
from constants.code_enum import SysCodeEnum
from model.db_connection_pool import get_db_pool
from model.db_models import TApiToken, TUser
from model.schemas import PaginatedResponse
from services.auth_service import generate_plain_api_token, hash_api_token

logger = logging.getLogger(__name__)

MAX_PER_USER = int(os.getenv("API_TOKEN_MAX_PER_USER", "10"))


def _fmt_dt(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _ensure_admin_user(session, user_id: int) -> TUser:
    user = session.query(TUser).filter(TUser.id == user_id).first()
    if not user or user.role != "admin":
        raise MyException(SysCodeEnum.PARAM_ERROR, "仅管理员账号可持有 API Token")
    return user


async def create_api_token(name: str, user_id: int, created_by: int) -> dict:
    if not name or not name.strip():
        raise MyException(SysCodeEnum.c_400, "Token 名称不能为空")

    db_pool = get_db_pool()
    with db_pool.get_session() as session:
        _ensure_admin_user(session, user_id)

        count = session.query(TApiToken).filter(TApiToken.user_id == user_id).count()
        if count >= MAX_PER_USER:
            raise MyException(
                SysCodeEnum.c_400, f"每个用户最多创建 {MAX_PER_USER} 个 API Token"
            )

        plain_token = generate_plain_api_token()
        now = datetime.now()
        record = TApiToken(
            user_id=user_id,
            name=name.strip(),
            token_hash=hash_api_token(plain_token),
            token_prefix=plain_token[:12],
            status=1,
            expires_at=None,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        session.add(record)
        session.flush()

        user = session.query(TUser).filter(TUser.id == user_id).first()
        return {
            "id": record.id,
            "name": record.name,
            "token": plain_token,
            "token_prefix": record.token_prefix,
            "user_id": user_id,
            "username": user.userName if user else "",
            "created_at": _fmt_dt(record.created_at),
        }


async def query_api_token_list(
    page: int,
    size: int,
    name: Optional[str] = None,
    user_id: Optional[int] = None,
    status: Optional[int] = None,
) -> PaginatedResponse:
    db_pool = get_db_pool()
    with db_pool.get_session() as session:
        query = session.query(TApiToken)
        if name:
            query = query.filter(TApiToken.name.like(f"%{name}%"))
        if user_id is not None:
            query = query.filter(TApiToken.user_id == user_id)
        if status is not None:
            query = query.filter(TApiToken.status == status)

        total_count = query.count()
        total_pages = (total_count + size - 1) // size if size else 0
        records_db = (
            query.order_by(TApiToken.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        user_ids = {r.user_id for r in records_db} | {r.created_by for r in records_db}
        users = {
            u.id: u.userName
            for u in session.query(TUser).filter(TUser.id.in_(user_ids)).all()
        }

        records = []
        for row in records_db:
            records.append(
                {
                    "id": row.id,
                    "name": row.name,
                    "token_prefix": row.token_prefix,
                    "user_id": row.user_id,
                    "username": users.get(row.user_id, ""),
                    "status": row.status,
                    "expires_at": _fmt_dt(row.expires_at),
                    "last_used_at": _fmt_dt(row.last_used_at),
                    "created_at": _fmt_dt(row.created_at),
                    "created_by": row.created_by,
                    "created_by_name": users.get(row.created_by, ""),
                }
            )

        return PaginatedResponse(
            records=records,
            current_page=page,
            total_count=total_count,
            total_pages=total_pages,
        )


async def set_api_token_status(token_id: int, status: int) -> None:
    db_pool = get_db_pool()
    with db_pool.get_session() as session:
        record = session.query(TApiToken).filter(TApiToken.id == token_id).first()
        if not record:
            raise MyException(SysCodeEnum.DATA_NOT_FOUND, "API Token 不存在")
        record.status = status
        record.updated_at = datetime.now()


async def delete_api_token(token_id: int) -> None:
    db_pool = get_db_pool()
    with db_pool.get_session() as session:
        record = session.query(TApiToken).filter(TApiToken.id == token_id).first()
        if not record:
            raise MyException(SysCodeEnum.DATA_NOT_FOUND, "API Token 不存在")
        session.delete(record)
