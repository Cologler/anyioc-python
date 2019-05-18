# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# a global ioc
# ----------

import functools
import inspect

from .ioc import ServiceProvider
from .utils import inject_by_name, dispose_at_exit

ioc = ServiceProvider()
dispose_at_exit(ioc)

ioc_decorator = ioc.decorator()

ioc_singleton = ioc_decorator.singleton
ioc_scoped = ioc_decorator.scoped
ioc_transient = ioc_decorator.transient
ioc_singleton_cls = functools.partial(ioc_decorator.singleton, inject_by=inject_by_name)
ioc_scoped_cls = functools.partial(ioc_decorator.scoped, inject_by=inject_by_name)
ioc_transient_cls = functools.partial(ioc_decorator.transient, inject_by=inject_by_name)
ioc_bind = ioc_decorator.bind

# scoped global ioc

def _make_module_scoped_provider():
    from .ioc_resolver import IServiceInfoResolver
    from .ioc_service_info import ValueServiceInfo, IServiceInfo
    from .symbols import Symbols

    class ServiceProviderServiceInfoResolver(IServiceInfoResolver):
        def get(self, provider, key) -> IServiceInfo:
            return ValueServiceInfo(ServiceProvider())

    provider = ServiceProvider()
    provider[Symbols.missing_resolver].append(
        ServiceProviderServiceInfoResolver().cache(sync=True)
    )
    dispose_at_exit(provider)
    return provider

_module_scoped_provider = _make_module_scoped_provider()

def get_module_provider(module_name: str=None) -> ServiceProvider:
    '''
    get the module scoped singleton `ServiceProvider`.

    if `module_name` is `None`, use caller module name.
    '''
    if module_name is None:
        fr = inspect.getouterframes(inspect.currentframe())[1]
        mo = inspect.getmodule(fr.frame)
        module_name = mo.__name__

    return _module_scoped_provider[module_name]

def get_package_provider(package_name: str=None) -> ServiceProvider:
    '''
    get the TOP package scoped singleton `ServiceProvider`.

    if `package_name` is `None`, use caller package name.

    for example, `get_package_provider('A.B.C.D')` is equals `get_module_provider('A')`
    '''
    if package_name is None:
        fr = inspect.getouterframes(inspect.currentframe())[1]
        mo = inspect.getmodule(fr.frame)
        package_name = mo.__name__

    package_name = package_name.partition('.')[0]
    return _module_scoped_provider[package_name]
