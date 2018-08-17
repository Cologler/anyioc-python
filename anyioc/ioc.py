# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod
from typing import Any
from enum import Enum
from inspect import signature, Parameter


class LifeTime(Enum):
    transient = 0
    scoped = 1
    singleton = 2


class IServiceInfo:
    @abstractmethod
    def get(self, provider) -> Any:
        raise NotImplementedError


class ServiceInfo(IServiceInfo):
    def __init__(self, key, factory, lifetime):

        sign = signature(factory)
        if not sign.parameters:
            factory = lambda _: factory()
        elif len(sign.parameters) == 1:
            arg_0 = list(sign.parameters.values())[0]
            if arg_0.kind != Parameter.POSITIONAL_OR_KEYWORD:
                raise TypeError('1st parameter of factory must be a positional parameter.')
        else:
            raise TypeError('factory has too many parameters.')

        self._key = key
        self._factory = factory
        self._lifetime = lifetime

    def get(self, provider):
        if self._lifetime == LifeTime.transient:
            return self._factory(provider)
        if self._lifetime == LifeTime.singleton:
            provider = provider._root_provider
        cache = provider._cache
        if self._key not in cache:
            cache[self._key] = self._factory(provider)
        return cache[self._key]


class ProviderServiceInfo(IServiceInfo):
    def get(self, provider):
        return provider


class IServiceProvider:
    @abstractmethod
    def get(self, key) -> Any:
        '''
        get a service by key.
        '''
        raise NotImplementedError

    @abstractmethod
    def scope(self):
        '''
        create a scoped service provider for get scoped services.
        '''
        raise NotImplementedError


class ServiceProvider(IServiceProvider):

    def __init__(self):
        self._services = {}
        self._cache = {}
        self._root_provider = self
        self._services['ioc'] = ProviderServiceInfo()

    def register_singleton(self, key, factory):
        '''
        register a singleton service factory by key.
        '''
        self._services[key] = ServiceInfo(key, factory, LifeTime.singleton)

    def register_scoped(self, key, factory):
        '''
        register a scoped service factory by key.
        '''
        self._services[key] = ServiceInfo(key, factory, LifeTime.scoped)

    def register_transient(self, key, factory):
        '''
        register a transient service factory by key.
        '''
        self._services[key] = ServiceInfo(key, factory, LifeTime.transient)

    def get(self, key):
        return self._services[key].get(self)

    def scope(self):
        return ScopedServiceProvider(self)


class ScopedServiceProvider(IServiceProvider):
    def __init__(self, root_provider):
        self._cache = {}
        self._root_provider = root_provider

    def get(self, key):
        return self._root_provider._services[key].get(self)

    def scope(self):
        return ScopedServiceProvider(self._root_provider)
