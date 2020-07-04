# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# a global ioc
# ----------

import importlib
import functools
import inspect
import threading

from .ioc import ServiceProvider
from .utils import inject_by_name, dispose_at_exit, get_module_name

ioc = ServiceProvider()
dispose_at_exit(ioc)

# scoped global ioc

_module_scoped_providers = {}
_module_scoped_lock = threading.RLock()

def _get_module_provider(module_name: str):
    'get or create module provider'
    provider = _module_scoped_providers.get(module_name)
    if provider is None:
        with _module_scoped_lock:
            provider = _module_scoped_providers.get(module_name)
            if provider is None:
                provider = ServiceProvider()
                dispose_at_exit(provider)
                _module_scoped_providers[module_name] = provider

                # auto init ioc
                try:
                    init_ioc = importlib.import_module(module_name + '.init_ioc')
                except ImportError:
                    init_ioc = None
                if init_ioc is not None:
                    conf_ioc = getattr(init_ioc, 'conf_ioc', None)
                    if conf_ioc is not None:
                        conf_ioc(provider)
    return provider

def _get_caller_module_name():
    fr = inspect.getouterframes(inspect.currentframe())[2]
    return get_module_name(fr)

def get_module_provider(module_name: str=None) -> ServiceProvider:
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

def get_namespace_provider(namespace: str=None) -> ServiceProvider:
    '''
    get the namespace scoped singleton `ServiceProvider`.

    if `namespace` is `None`, use caller namespace.

    for example, `get_namespace_provider('A.B.C.D')` is equals `get_module_provider('A')`
    '''
    if namespace is None:
        namespace = _get_caller_module_name()

    if not isinstance(namespace, str):
        raise TypeError

    namespace = namespace.partition('.')[0]
    return _get_module_provider(namespace)
