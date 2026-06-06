from glob import glob
import importlib.util
import inspect
import os
from pathlib import Path
from types import ModuleType
from typing import Union

from fastapi import APIRouter


def autodiscover(app, *module_names: Union[str, ModuleType], recursive: bool = False):
    """
    自动扫描目录并注册 FastAPI APIRouter
    """
    mod = app.__module__
    routers: list[APIRouter] = []
    _imported = set()

    def _find_routers(module):
        for _, member in inspect.getmembers(module):
            if isinstance(member, APIRouter) and member not in routers:
                routers.append(member)

    for module in module_names:
        if isinstance(module, str):
            module = importlib.import_module(module, mod)
            _imported.add(module.__file__)
        _find_routers(module)

        if recursive:
            base = Path(module.__file__).parent
            pattern = os.path.join(base, "**", "*.py")
            for path in glob(pattern, recursive=True):
                if path not in _imported:
                    name = "module"
                    if "__init__.py" in path:
                        *_, name, _ = path.split(os.sep)
                    spec = importlib.util.spec_from_file_location(name, path)
                    speckled = importlib.util.module_from_spec(spec)
                    _imported.add(path)
                    spec.loader.exec_module(speckled)
                    _find_routers(speckled)

    for router in routers:
        app.include_router(router)
