"""
参数解析工具（FastAPI 版本）

FastAPI 原生支持 Pydantic Body / Query / Form / Path 参数自动解析，
因此原 @parse_params 装饰器已不再需要。

此模块仅保留向后兼容的辅助函数，供服务层手动调用。
"""
from typing import Any, Optional, Type

from pydantic import BaseModel, ValidationError

from common.exception import MyException
from constants.code_enum import SysCodeEnum


def parse_body_from_dict(data: dict, model: Type[BaseModel]) -> BaseModel:
    """从字典数据解析为 Pydantic 模型"""
    try:
        return model.model_validate(data)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"{field}: {msg}")
        raise MyException(SysCodeEnum.PARAM_ERROR, f"参数验证失败: {'; '.join(errors)}")


def convert_type(value: Any, param_name: str, param_type: Type) -> Any:
    """类型转换工具"""
    try:
        if param_type == int:
            return int(value)
        elif param_type == float:
            return float(value)
        elif param_type == bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
        elif param_type == str:
            return str(value)
        elif param_type == list:
            if isinstance(value, list):
                return value
            return [value]
        else:
            return value
    except (ValueError, TypeError) as e:
        raise MyException(
            SysCodeEnum.PARAM_ERROR, f"参数 {param_name} 类型转换失败: {str(e)}"
        )
