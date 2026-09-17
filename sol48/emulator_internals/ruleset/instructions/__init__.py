import importlib, pkgutil, types

modules: dict[str,types.ModuleType] = {}
__all__ = []

for _, name, ispkg in pkgutil.iter_modules(__path__):
    if not ispkg:
        module = importlib.import_module(f'{__name__}.{name}')
        modules[name] = module
        __all__.append(name)