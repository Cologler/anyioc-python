# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import sys
import types
from contextlib import nullcontext
from threading import RLock
from typing import Any, override

from ._bases import IServiceInfo, IServiceProvider
from ._service_info import FactoryServiceInfo, ValueServiceInfo
from ._utils import wrap_signature
from .err import ServiceNotFoundError


class IServiceInfoResolver:
    '''
    the base class for dynamic resolve `IServiceInfo`.
    '''

    def get(self, provider: IServiceProvider, key: Any, /) -> IServiceInfo[Any]:
        '''
        Get the `IServiceInfo` from resolver.
        '''
        raise ServiceNotFoundError(key)

    def __add__(self, other):
        new_resolver = ServiceInfoChainResolver()
        new_resolver.chain.append(self)
        new_resolver.append(other)
        return new_resolver

    def cache(self, *, sync=False):
        '''
        Returns a `IServiceInfoResolver` to cache all `IServiceInfo`s from this `IServiceInfoResolver`.

        All values won't dynamic update after the first resolved.
        '''
        return CacheServiceInfoResolver(self, sync=sync)


class ServiceInfoChainResolver(IServiceInfoResolver):
    '''
    A chained resolver for resolve IServiceInfos from each `IServiceInfoResolver`
    '''

    def __init__(self, *resolvers: IServiceInfoResolver):
        self.chain = list(resolvers)

    def get(self, provider, key):
        for resolver in self.chain:
            try:
                return resolver.get(provider, key)
            except ServiceNotFoundError:
                pass
        return super().get(provider, key)

    def append(self, other: IServiceInfoResolver) -> None:
        if isinstance(other, ServiceInfoChainResolver):
            self.chain.extend(other.chain)
        else:
            self.chain.append(other)

    def __add__(self, other):
        new_resolver = ServiceInfoChainResolver()
        new_resolver.chain.extend(self.chain)
        new_resolver.append(other)
        return new_resolver


class CacheServiceInfoResolver(IServiceInfoResolver):
    '''
    a helper resolver for cache values from other `IServiceInfoResolver`

    NOTE:
    if a `IServiceInfo` is affect by `provider`, you should not cache it.
    `CacheServiceInfoResolver` only cache by the `key` and ignore the `provider` arguments.
    '''

    def __init__(self, base_resolver: IServiceInfoResolver, *, sync=False):
        super().__init__()
        self._base_resolver = base_resolver
        self._cache = {}
        self._lock = RLock() if sync else nullcontext()

    def get(self, provider, key):
        try:
            return self._cache[key]
        except KeyError:
            pass
        with self._lock:
            try:
                return self._cache[key]
            except KeyError:
                pass
            service_info = self._base_resolver.get(provider, key)
            self._cache[key] = service_info
            return service_info

    def cache(self, *, sync=False):
        if sync and isinstance(self._lock, nullcontext):
            return CacheServiceInfoResolver(self, sync=sync)
        return self


class ImportServiceInfoResolver(IServiceInfoResolver):
    '''
    Dynamic resolve `IServiceInfo` if the key is a module name.

    - Relative import is not allowed;
    - If the key is `{module_name}`, only lookup modules from `sys.modules`;
    - If the key is `module::{module_name}` (startswith `module::`), the resolver will try to import it;
    '''

    @override
    def get(self, provider: IServiceProvider, key: Any, /) -> IServiceInfo[types.ModuleType]:
        if isinstance(key, str) and not key.startswith('.'): # relative import is not allows
            if key.startswith('module::'):
                module_name = key.removeprefix('module::')
                import importlib
                try:
                    module = importlib.import_module(module_name)
                    return ValueServiceInfo(module)
                except (TypeError, ModuleNotFoundError):
                    pass
            else:
                module_name = key
                if module := sys.modules.get(module_name):
                    return ValueServiceInfo(module)
        return super().get(provider, key)


class TypesServiceInfoResolver(IServiceInfoResolver):
    '''
    Dynamic resolve `IServiceInfo` if the key is a type instance.
    '''

    def get(self, provider, key):
        if isinstance(key, type):
            return FactoryServiceInfo(wrap_signature(key))
        return super().get(provider, key)


class TypeNameServiceInfoResolver(IServiceInfoResolver):
    '''
    dynamic resolve `IServiceInfo` if the key is a type name or qualname.
    '''

    def _get_type(self, key):
        if isinstance(key, str):
            for klass in object.__subclasses__():
                if getattr(klass, '__name__', None) == key:
                    return klass
                if getattr(klass, '__qualname__', None) == key:
                    return klass
        # None

    def get(self, provider, key):
        klass = self._get_type(str)
        if klass is not None:
            return FactoryServiceInfo(wrap_signature(klass))
        return super().get(provider, key)
