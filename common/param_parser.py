"""
参数解析装饰器（兼容层）
FastAPI 原生支持 Pydantic 注入；保留此装饰器供尚未迁移的端点使用。
"""
from functools import wraps
from inspect import Parameter, signature
from typing import Any, Optional, Type, get_args, get_origin, get_type_hints

from pydantic import BaseModel, ValidationError
from starlette.requests import Request

from common.exception import MyException
from constants.code_enum import SysCodeEnum


def parse_params(handler):
    """根据函数签名从请求中解析参数"""

    @wraps(handler)
    async def wrapper(request: Request, *args, **kwargs):
        sig = signature(handler)
        type_hints = get_type_hints(handler)
        parsed_kwargs = {}

        for param_name, param in sig.parameters.items():
            if param_name == "request":
                continue
            if param_name in kwargs:
                continue

            param_type = type_hints.get(param_name, str)
            if param_type is Request or (
                isinstance(param_type, type) and issubclass(param_type, Request)
            ):
                continue

            is_optional = get_origin(param_type) is type(Optional[int])
            if is_optional:
                actual_type = get_args(param_type)[0]
            else:
                actual_type = param_type

            has_default = param.default != Parameter.empty
            default_value = param.default if has_default else None
            required = not has_default and not is_optional

            if isinstance(actual_type, type) and issubclass(actual_type, BaseModel):
                parsed_kwargs[param_name] = await _parse_body(
                    request, actual_type, required
                )
            else:
                parsed_kwargs[param_name] = _parse_query_or_form(
                    request, param_name, actual_type, default_value, required
                )

        kwargs.update(parsed_kwargs)
        return await handler(request, *args, **kwargs)

    return wrapper


async def _parse_body(
    request: Request, model: Type[BaseModel], required: bool = True
) -> Optional[BaseModel]:
    try:
        data = await request.json()
        if not data and not required:
            return None
        return model.model_validate(data or {})
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            errors.append(f"{field}: {error['msg']}")
        raise MyException(
            SysCodeEnum.PARAM_ERROR, f"参数验证失败: {'; '.join(errors)}"
        )
    except Exception as e:
        raise MyException(SysCodeEnum.PARAM_ERROR, f"解析请求体失败: {str(e)}")


def _parse_query_or_form(
    request: Request,
    param_name: str,
    param_type: Type,
    default: Any = None,
    required: bool = False,
) -> Any:
    value = request.query_params.get(param_name)

    if value is None:
        path_params = getattr(request, "path_params", {}) or {}
        value = path_params.get(param_name)

    if value is None:
        if required:
            raise MyException(
                SysCodeEnum.PARAM_ERROR, f"缺少必需参数: {param_name}"
            )
        return default

    return _convert_type(value, param_name, param_type)


def _convert_type(value: Any, param_name: str, param_type: Type) -> Any:
    try:
        if param_type == int:
            return int(value)
        if param_type == float:
            return float(value)
        if param_type == bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
        if param_type == str:
            return str(value)
        if param_type == list:
            if isinstance(value, list):
                return value
            return [value]
        return value
    except (ValueError, TypeError) as e:
        raise MyException(
            SysCodeEnum.PARAM_ERROR, f"参数 {param_name} 类型转换失败: {str(e)}"
        )


async def parse_body(request: Request, model: Type[BaseModel]) -> BaseModel:
    return await _parse_body(request, model, required=True)


def parse_query(
    request: Request,
    param_name: str,
    param_type: Type,
    default: Any = None,
    required: bool = False,
) -> Any:
    return _parse_query_or_form(
        request, param_name, param_type, default, required
    )
