import json
import logging
import traceback
from datetime import date, datetime
from decimal import Decimal
from functools import wraps

import numpy as np
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from common.exception import MyException
from constants.code_enum import SysCodeEnum


class CustomJSONEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理日期、numpy 等特殊类型"""

    def default(self, obj):
        if isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, bytes):
            try:
                return obj.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    return obj.decode("latin-1")
                except Exception:
                    return ""
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if isinstance(obj, (np.ndarray, np.generic)):
            return None
        if hasattr(obj, "tolist"):
            return obj.tolist()
        return super().default(obj)


def _json_response(body: dict) -> JSONResponse:
    return JSONResponse(
        content=json.loads(CustomJSONEncoder().encode(body)),
    )


def async_json_resp(func):
    """异步 JSON 响应装饰器，统一 {code, msg, data} 信封"""

    @wraps(func)
    async def http_res_wrapper(request: Request, *args, **kwargs):
        data = None
        method = request.method
        path = request.url.path
        params = dict(request.query_params)
        content_type = request.headers.get("content-type", "")
        json_body = ""
        if "application/json" in content_type:
            try:
                json_body = await request.json()
            except Exception:
                json_body = {}

        try:
            data = await func(request, *args, **kwargs)
            body = {
                "code": SysCodeEnum.c_200.value[0],
                "msg": SysCodeEnum.c_200.value[1],
                "data": data,
            }
            logging.info(
                "Request Path: %s, Method: %s, Params: %s, JSON Body: %s, Response: %s",
                path,
                method,
                params,
                json_body,
                body,
            )
            return _json_response(body)

        except MyException as e:
            body = {
                "code": e.code,
                "msg": e.message,
                "data": data,
            }
            logging.info(
                "Request Path: %s, Method: %s, Params: %s, JSON Body: %s, Response: %s",
                path,
                method,
                params,
                json_body,
                body,
            )
            return _json_response(body)

        except Exception as e:
            body = {
                "code": SysCodeEnum.c_9999.value[0],
                "msg": SysCodeEnum.c_9999.value[1],
                "data": data,
            }
            logging.info(
                "Request Path: %s, Method: %s, Params: %s, JSON Body: %s, Response: %s",
                path,
                method,
                params,
                json_body,
                body,
            )
            traceback.print_exception(e)
            return _json_response(body)

    return http_res_wrapper
