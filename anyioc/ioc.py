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

from .err import ServiceNotFoundError


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
            self._factory = lambda _: factory()
        elif len(sign.parameters) == 1:
            arg_0 = list(sign.parameters.values())[0]
            if arg_0.kind != Parameter.POSITIONAL_OR_KEYWORD:
                raise TypeError('1st parameter of factory must be a positional parameter.')
            self._factory = factory
        else:
            raise TypeError('factory has too many parameters.')

        self._key = key
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
    def __getitem__(self, key):
        raise NotImplementedError

    def get(self, key, d=None) -> Any:
        '''
        get a service by key.
        '''
        try:
            return self[key]
        except ServiceNotFoundError as err:
            if len(err.resolve_chain) == 1:
                return d
            raise

    @abstractmethod
    def scope(self):
        '''
        create a scoped service provider for get scoped services.
        '''
        raise NotImplementedError

    def _get(self, services, key):
        service_info = services.get(key)
        if service_info is None:
            raise ServiceNotFoundError(key)
        try:
            return service_info.get(self)
        except ServiceNotFoundError as err:
            raise ServiceNotFoundError(key, *err.resolve_chain)


class ServiceProvider(IServiceProvider):

    def __init__(self):
        self._services = {}
        self._cache = {}
        self._root_provider = self
        self._services['ioc'] = ProviderServiceInfo()

    def register_service_info(self, key, service_info: IServiceInfo):
        '''
        register a IServiceInfo by key.
        '''
        if not isinstance(service_info, IServiceInfo):
            raise TypeError('service_info must be instance of IServiceInfo.')
        self._services[key] = service_info

    def register(self, key, factory, lifetime):
        '''
        register a service factory by key.
        '''
        return self.register_service_info(key, ServiceInfo(key, factory, lifetime))

    def register_singleton(self, key, factory):
        '''
        register a singleton service factory by key.
        '''
        return self.register(key, factory, LifeTime.singleton)

    def register_scoped(self, key, factory):
        '''
        register a scoped service factory by key.
        '''
        return self.register(key, factory, LifeTime.scoped)

    def register_transient(self, key, factory):
        '''
        register a transient service factory by key.
        '''
        return self.register(key, factory, LifeTime.transient)

    def __getitem__(self, key):
        return self._get(self._services, key)

    def scope(self):
        return ScopedServiceProvider(self)


class ScopedServiceProvider(IServiceProvider):
    def __init__(self, root_provider):
        self._cache = {}
        self._root_provider = root_provider

    def __getitem__(self, key):
        return self._get(self._root_provider._services, key)

    def scope(self):
        return ScopedServiceProvider(self._root_provider)
