# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod
from typing import List

from .err import ServiceNotFoundError
from .ioc_service_info import ValueServiceInfo, ServiceInfo, LifeTime

class IServiceInfoResolver:
    def get(self, provider, key):
        '''
        get the `IServiceInfo` from resolver.
        '''
        raise ServiceNotFoundError(key)

    def __add__(self, other):
        new_resolver = ServiceInfoChainResolver()
        new_resolver.chain.append(self)
        new_resolver.append(other)
        return new_resolver

    def cache(self):
        '''
        return a `CacheServiceInfoResolver`.
        '''
        return CacheServiceInfoResolver(self)


class ServiceInfoChainResolver(IServiceInfoResolver):
    '''
    the chain resolver
    '''
    def __init__(self, *resolvers):
        self.chain: List[IServiceInfoResolver] = list(resolvers)

    def get(self, provider, key):
        for resolver in self.chain:
            try:
                return resolver.get(provider, key)
            except ServiceNotFoundError:
                pass
        return super().get(provider, key)

    def append(self, other):
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
    NOTE:
    if a `IServiceInfo` is affect by `provider`, you should not cache it.
    `CacheServiceInfoResolver` only cache by the `key` and ignore the `provider` arguments.
    '''
    def __init__(self, base_resolver: IServiceInfoResolver):
        super().__init__()
        self._base_resolver = base_resolver
        self._cache = {}

    def get(self, provider, key):
        try:
            return self._cache[key]
        except KeyError:
            pass
        service_info = self._base_resolver.get(provider, key)
        self._cache[key] = service_info
        return service_info

    def cache(self):
        return self


class ImportServiceInfoResolver(IServiceInfoResolver):
    def get(self, provider, key):
        import importlib
        if isinstance(key, str):
            try:
                module = importlib.import_module(key)
                return ValueServiceInfo(module)
            except TypeError:
                pass
            except ModuleNotFoundError:
                pass
        return super().get(provider, key)


class TypesServiceInfoResolver(IServiceInfoResolver):
    inject_by = None

    def get(self, provider, key):
        if isinstance(key, type):
            factory = self.inject_by(key) if self.inject_by else key
            return ServiceInfo(None, key, factory, LifeTime.transient)
        return super().get(provider, key)


class TypeNameServiceInfoResolver(IServiceInfoResolver):
    inject_by = None

    def _get_type(self, key):
        if isinstance(key, str):
            for klass in object.__subclasses__():
                if getattr(klass, '__name__', None) == key:
                    return klass
        # None

    def get(self, provider, key):
        klass = self._get_type(str)
        if klass is not None:
            factory = self.inject_by(klass) if self.inject_by else klass
            return ServiceInfo(None, key, factory, LifeTime.transient)
        return super().get(provider, key)
