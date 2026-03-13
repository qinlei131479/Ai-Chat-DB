import os
from datetime import datetime

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI 依赖注入：JWT token 校验，替代原 @check_token 装饰器。
    校验成功返回用户信息 dict（与原 get_user_info 返回格式一致）。
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="无效Token")

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            key=os.getenv("JWT_SECRET_KEY", "550e8400-e29b-41d4-a716-446655440000"),
            algorithms=["HS256"],
        )
        if "exp" in payload and datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token已过期")

        # JWT payload 由 generate_jwt_token() 生成，字段为 id / username / role
        return {
            "id": payload.get("id"),
            "name": payload.get("username"),
            "role": payload.get("role"),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="无效Token")
