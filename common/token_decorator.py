import os
from datetime import datetime
from functools import wraps

import jwt
from starlette.requests import Request
from starlette.responses import JSONResponse


def check_token(f):
    """jwt token 校验注解"""

    @wraps(f)
    async def wrapper(request: Request, *args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return JSONResponse(
                {"message": "无效Token", "code": 401}, status_code=401
            )
        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1]

            payload = jwt.decode(
                token,
                key=os.getenv(
                    "JWT_SECRET_KEY", "550e8400-e29b-41d4-a716-446655440000"
                ),
                algorithms=["HS256"],
            )
            if "exp" in payload and datetime.utcfromtimestamp(
                payload["exp"]
            ) < datetime.utcnow():
                return JSONResponse(
                    {"message": "Token已过期", "code": 401}, status_code=401
                )

            request.state.user_payload = payload
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                {"message": "Token已过期", "code": 401}, status_code=401
            )
        except Exception:
            return JSONResponse(
                {"message": "无效Token", "code": 401}, status_code=401
            )

        return await f(request, *args, **kwargs)

    return wrapper
