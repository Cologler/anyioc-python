# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod
from typing import Any
from collections import ChainMap
from contextlib import ExitStack

from .err import ServiceNotFoundError
from .symbols import Symbols

from .ioc_service_info import (
    LifeTime,
    IServiceInfo,
    ServiceInfo,
    ProviderServiceInfo,
    ValueServiceInfo,
    CacheServiceInfo
)


class IServiceProvider:
    @abstractmethod
    def __getitem__(self, key):
        raise NotImplementedError

    @abstractmethod
    def get(self, key, d=None) -> Any:
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


class ScopedServiceProvider(IServiceProvider):

    def __init__(self, services: ChainMap):
        super().__init__()
        self._services = services
        self._cache = {}
        self._exit_stack = None

    def __getitem__(self, key):
        return self._getitem(self._services, key)

    def _getitem(self, services, key):
        service_info = services.get(key)
        if service_info is None:
            raise ServiceNotFoundError(key)
        try:
            return service_info.get(self)
        except ServiceNotFoundError as err:
            raise ServiceNotFoundError(key, *err.resolve_chain)

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

    def enter(self, context):
        '''
        enter the context.

        returns the result of the `context.__enter__()` method.
        '''
        if self._exit_stack is None:
            self._exit_stack = ExitStack()
        return self._exit_stack.enter_context(context)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self._exit_stack is not None:
            self._exit_stack.__exit__(*args)

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

    def scope(self):
        return ScopedServiceProvider(self._services.new_child())


class ServiceProvider(ScopedServiceProvider):
    def __init__(self):
        super().__init__(ChainMap())
        self._services[Symbols.provider] = ProviderServiceInfo()
        self._services[Symbols.provider_root] = ValueServiceInfo(self)
        self._services[Symbols.cache] = CacheServiceInfo()
        # service alias
        self._services['ioc'] = self._services[Symbols.provider]
        self._services['provider'] = self._services[Symbols.provider]
        self._services['service_provider'] = self._services[Symbols.provider]
