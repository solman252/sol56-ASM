import importlib
import pkgutil

modules = {}
__all__ = []

for _, name, ispkg in pkgutil.iter_modules(__path__):
    if not ispkg:
        modules[name] = importlib.import_module(f"{__name__}.{name}")
        __all__.append(name)