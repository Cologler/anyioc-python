# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod
from typing import Any, List
from contextlib import ExitStack

from .err import ServiceNotFoundError
from .symbols import Symbols
from .ioc_services import ServicesMap
from .ioc_resolver import IServiceInfoResolver, ServiceInfoChainResolver
from .ioc_service_info import (
    LifeTime,
    IServiceInfo,
    ServiceInfo,
    ProviderServiceInfo,
    ValueServiceInfo,
    GroupedServiceInfo,
    BindedServiceInfo,
    CallerFrameServiceInfo
)


class IServiceProvider:
    '''
    the base interface for `ServiceProvider`.
    '''

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

    def __init__(self, services: ServicesMap):
        super().__init__()
        self._services = services
        self._exit_stack = None
        self._services[Symbols.cache] = ValueServiceInfo({})
        self.__class__ = ServiceProvider # hack

    def _get_service_info(self, key) -> IServiceInfo:
        try:
            return self._services[key]
        except KeyError:
            pass
        # load missing resolver and resolve service info.
        resolver: IServiceInfoResolver = self._services[Symbols.missing_resolver].get(self)
        return resolver.get(self, key)

    def _get_service_info_list(self, key) -> List[IServiceInfo]:
        return self._services.get_many(key)

    def __getitem__(self, key):
        service_info = self._get_service_info(key)
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

    def get_many(self, key) -> List[Any]:
        '''
        get services by key.

        ### example

        when you registered multi services with the same key,
        you can get them all:

        ``` py
        provider.register_value('a', 1)
        provider.register_value('a', 2)
        assert provider.get_many('a') == [2, 1] # rev order
        ```
        '''
        service_infos = self._get_service_info_list(key)
        try:
            return [si.get(self) for si in service_infos]
        except ServiceNotFoundError as err:
            raise ServiceNotFoundError(key, *err.resolve_chain)

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
        register a `IServiceInfo` by key.
        '''
        if not isinstance(service_info, IServiceInfo):
            raise TypeError('service_info must be instance of IServiceInfo.')
        self._services[key] = service_info

    def register(self, key, factory, lifetime):
        '''
        register a service factory by key.

        `factory` accept a function which require one or zero parameter.
        if the count of parameter is 1, pass a `IServiceProvider` as the argument.
        '''
        return self.register_service_info(key, ServiceInfo(self, key, factory, lifetime))

    def register_singleton(self, key, factory):
        '''
        register a service factory by key.

        `factory` accept a function which require one or zero parameter.
        if the count of parameter is 1, pass a `IServiceProvider` as the argument.
        '''
        return self.register(key, factory, LifeTime.singleton)

    def register_scoped(self, key, factory):
        '''
        register a service factory by key.

        `factory` accept a function which require one or zero parameter.
        if the count of parameter is 1, pass a `IServiceProvider` as the argument.
        '''
        return self.register(key, factory, LifeTime.scoped)

    def register_transient(self, key, factory):
        '''
        register a service factory by key.

        `factory` accept a function which require one or zero parameter.
        if the count of parameter is 1, pass a `IServiceProvider` as the argument.
        '''
        return self.register(key, factory, LifeTime.transient)

    def register_value(self, key, value):
        '''
        register a value by key.

        equals `register_transient(key, lambda ioc: value)`
        '''
        return self.register_service_info(key, ValueServiceInfo(value))

    def register_group(self, key, keys: list):
        '''
        register a grouped `key` for get other `keys`.

        the `keys` can be a ref and you can update it later.

        for example:

        ``` py
        provider.register_value('str', 'name')
        provider.register_value('int', 1)
        provider.register_group('any', ['str', 'int'])
        assert provider['any'] == ('name', 1)
        ```

        equals `register_transient(key, lambda ioc: tuple(ioc[k] for k in keys))`
        '''
        sym = Symbols.get_symbol_for_group_src(key)
        self.register_value(sym, keys)
        return self.register_service_info(key, GroupedServiceInfo(keys))

    def register_bind(self, new_key, target_key):
        '''
        bind `new_key` to `target_key` so
        you can use `new_key` as key to get value from service provider.

        equals `register_transient(new_key, lambda ioc: ioc[target_key])`
        '''
        return self.register_service_info(new_key, BindedServiceInfo(target_key))

    def scope(self):
        '''
        create a scoped service provider.
        '''
        sp = ScopedServiceProvider(self._services.scope())
        self.enter(sp)
        sp.register_value(Symbols.provider_parent, self)
        return sp

    @property
    def builder(self):
        '''
        get a new `ServiceProviderBuilder` for use high level api for this `ServiceProvider`.
        '''
        from .builder import ServiceProviderBuilder
        return ServiceProviderBuilder(self)


class ServiceProvider(ScopedServiceProvider):
    '''
    the default impl for `IServiceProvider`.
    '''

    def __init__(self):
        super().__init__(ServicesMap())
        provider_service_info = ProviderServiceInfo()
        self._services[Symbols.provider] = provider_service_info
        self._services[Symbols.provider_root] = ValueServiceInfo(self)
        self._services[Symbols.provider_parent] = ValueServiceInfo(None)
        self._services[Symbols.missing_resolver] = ValueServiceInfo(ServiceInfoChainResolver())
        self._services[Symbols.caller_frame] = CallerFrameServiceInfo()
        # service alias
        self._services['ioc'] = provider_service_info
        self._services['provider'] = provider_service_info
        self._services['service_provider'] = provider_service_info
        self._services[ServiceProvider] = provider_service_info
        self._services[IServiceProvider] = provider_service_info
