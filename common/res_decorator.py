import json
import logging
import traceback
from datetime import date, datetime
from decimal import Decimal

import numpy as np
from pydantic import BaseModel
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from common.exception import MyException
from constants.code_enum import SysCodeEnum


class CustomJSONEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理日期、Decimal、numpy 等特殊类型"""

    def default(self, obj):
        if isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, bytes):
            try:
                return obj.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    return obj.decode("latin-1")
                except Exception:
                    return ""
        elif isinstance(obj, BaseModel):
            return obj.model_dump()
        elif isinstance(obj, (np.ndarray, np.generic)):
            return None
        elif hasattr(obj, "tolist"):
            return obj.tolist()
        return super().default(obj)


class CustomJSONResponse(JSONResponse):
    """使用 CustomJSONEncoder 的 JSON 响应类"""

    def render(self, content) -> bytes:
        return json.dumps(
            content, cls=CustomJSONEncoder, ensure_ascii=False
        ).encode("utf-8")


def success_response(data=None):
    """统一成功响应，保持与原 @async_json_resp 一致的格式"""
    return CustomJSONResponse(
        content={
            "code": SysCodeEnum.c_200.value[0],
            "msg": SysCodeEnum.c_200.value[1],
            "data": data,
        }
    )


def error_response(code: int, msg: str, data=None, status_code: int = 200):
    """统一错误响应"""
    return CustomJSONResponse(
        status_code=status_code,
        content={"code": code, "msg": msg, "data": data},
    )


def register_exception_handlers(app: FastAPI):
    """注册全局异常处理器，替代原 @async_json_resp 中的异常捕获逻辑"""

    @app.exception_handler(MyException)
    async def my_exception_handler(request: Request, exc: MyException):
        logging.warning("Business error on %s: %s", request.url.path, exc)
        return CustomJSONResponse(
            content={"code": exc.code, "msg": exc.message, "data": None}
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail, "code": exc.status_code},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        errors = []
        for error in exc.errors():
            field = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"{field}: {msg}")
        return CustomJSONResponse(
            content={
                "code": SysCodeEnum.PARAM_ERROR.value[0],
                "msg": f"参数验证失败: {'; '.join(errors)}",
                "data": None,
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logging.error("Unhandled error on %s: %s", request.url.path, exc)
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        return CustomJSONResponse(
            content={
                "code": SysCodeEnum.c_9999.value[0],
                "msg": SysCodeEnum.c_9999.value[1],
                "data": None,
            }
        )
