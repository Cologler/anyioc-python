# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# a global ioc
# ----------

import importlib
import importlib.util
import inspect
import threading
from typing import Optional

from ._utils import dispose_at_exit, get_module_name
from .ioc import ServiceProvider

ioc = ServiceProvider()
dispose_at_exit(ioc)

# scoped global ioc

_module_scoped_providers = {}
_module_scoped_lock = threading.RLock()

def _is_module_exists(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except ModuleNotFoundError:
        return False

def _get_module_provider(module_name: str):
    'get or create module provider'

    def init_hook(provider):
        # auto init ioc
        initioc_module_name = module_name + '.init_ioc'
        if _is_module_exists(initioc_module_name):
            init_ioc = importlib.import_module(initioc_module_name)
            conf_ioc = getattr(init_ioc, 'conf_ioc', None)
            if conf_ioc is not None:
                conf_ioc(provider)

    provider = _module_scoped_providers.get(module_name)
    if provider is None:
        with _module_scoped_lock:
            provider = _module_scoped_providers.get(module_name)
            if provider is None:
                provider = ServiceProvider()
                dispose_at_exit(provider)
                _module_scoped_providers[module_name] = provider
                provider.add_init_hook(init_hook)

    return provider

def _get_caller_module_name():
    fr = inspect.getouterframes(inspect.currentframe())[2]
    return get_module_name(fr)

def get_module_provider(module_name: Optional[str]=None) -> ServiceProvider:
    '''
    get the module scoped singleton `ServiceProvider`.

    if `module_name` is `None`, use caller module name.

    if module `{module_name}.init_ioc` exists and it has a attr `conf_ioc`, will auto config like:

    ``` py
    (importlib.import_module(module_name + '.init_ioc')).conf_ioc(module_provider)
    ```
    '''
    if module_name is None:
        module_name = _get_caller_module_name()

    if not isinstance(module_name, str):
        raise TypeError

    return _get_module_provider(module_name)

def get_pkgroot_provider(pkgroot: Optional[str]=None) -> ServiceProvider:
    '''
    get the package root scoped singleton `ServiceProvider`.

    if `pkgroot` is `None`, use caller package root.

    for example, `get_pkgroot_provider('A.B.C.D')` is equals `get_module_provider('A')`
    '''
    if pkgroot is None:
        pkgroot = _get_caller_module_name()

    if not isinstance(pkgroot, str):
        raise TypeError

    pkgroot = pkgroot.partition('.')[0]
    return _get_module_provider(pkgroot)

# keep old func names:

get_namespace_provider = get_pkgroot_provider
