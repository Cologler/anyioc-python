# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod
from typing import Any, List, TypeVar, ContextManager, Callable, Iterable
from contextlib import ExitStack, nullcontext
from threading import RLock
from types import MappingProxyType
from logging import getLogger

from .err import ServiceNotFoundError
from .symbols import Symbols
from ._servicesmap import ServicesMap
from .ioc_resolver import IServiceInfoResolver, ServiceInfoChainResolver
from .ioc_service_info import (
    LifeTime,
    IServiceInfo,
    ServiceInfo,
    ProviderServiceInfo,
    GetAttrServiceInfo,
    ValueServiceInfo,
    GroupedServiceInfo,
    BindedServiceInfo,
    CallerFrameServiceInfo
)
from ._utils import wrap_signature as _wrap_signature

_T = TypeVar("_T")

_logger = getLogger(__name__)


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
    def get_many(self, key) -> List[Any]:
        '''
        get services by key.
        '''
        raise NotImplementedError

    @abstractmethod
    def scope(self):
        '''
        create a scoped service provider for get scoped services.
        '''
        raise NotImplementedError


class ServiceProvider(IServiceProvider):
    def __init__(self, auto_enter=False, *,
                # internal uses:
                _services: ServicesMap=None, _parent: 'ServiceProvider'=None
            ):

        self._exit_stack = None
        self._scoped_cache = {}
        self._parent = _parent

        assert (_parent is None) is (_services is None)

        if _parent is not None:
            # scope provider
            assert auto_enter is False, 'must be default value'
            self._services = _services
            self._root: ServiceProvider = _parent._root
            self._lock = nullcontext()

        else:
            # root provider
            self._services = ServicesMap()
            self._root: ServiceProvider = self
            self._lock = RLock()

            provider_service_info = ProviderServiceInfo()
            self._services[Symbols.provider] = provider_service_info
            self._services[Symbols.provider_root] = ValueServiceInfo(self)
            self._services[Symbols.provider_parent] = GetAttrServiceInfo('_parent')
            self._services[Symbols.cache] = GetAttrServiceInfo('_scoped_cache')
            self._services[Symbols.missing_resolver] = ValueServiceInfo(ServiceInfoChainResolver())
            self._services[Symbols.caller_frame] = CallerFrameServiceInfo()

            self.__init_hooks = []
            self.__init_exc = None

            # service alias
            self._services['ioc'] = provider_service_info
            self._services['provider'] = provider_service_info
            self._services['service_provider'] = provider_service_info
            self._services[ServiceProvider] = provider_service_info
            self._services[IServiceProvider] = provider_service_info

            # options
            self._services[Symbols.provider_options] = ValueServiceInfo(MappingProxyType(
                dict(
                    auto_enter=auto_enter
                )
            ))

        assert self._root is not None

    def add_init_hook(self, func: Callable):
        func = _wrap_signature(func)
        if self.__init_hooks is not None:
            with self._lock:
                if self.__init_hooks is not None:
                    self.__init_hooks.append(func)
                    return
        raise RuntimeError('Cannot add init hook after initialized.')

    def __ensure_init_hooks_called(self):
        if self.__init_hooks is not None or self.__init_exc is not None:
            with self._lock:
                if self.__init_exc is not None:
                    raise self.__init_exc
                if self.__init_hooks is not None:
                    _logger.debug('call init hooks')
                    hooks = self.__init_hooks
                    self.__init_hooks = None

                    disposable = self._services.add(Symbols.at_init, ValueServiceInfo(True))
                    try:
                        for func in hooks:
                            func(self)
                    except Exception as e:
                        self.__init_exc = e
                        raise
                    disposable()
                    self._services.add(Symbols.at_init, ValueServiceInfo(False))

    def _get_service_info(self, key) -> IServiceInfo:
        try:
            return self._services[key]
        except KeyError:
            pass
        # load missing resolver and resolve service info.
        resolver: IServiceInfoResolver = self._services[Symbols.missing_resolver].get(self)
        return resolver.get(self, key)

    def __getitem__(self, key):
        _logger.debug('get service by key: %r', key)
        self._root.__ensure_init_hooks_called()
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
        _logger.debug('get services by key: %r', key)
        self._root.__ensure_init_hooks_called()
        service_infos: Iterable[IServiceInfo] = self._services.get_many(key)
        try:
            return [si.get(self) for si in service_infos]
        except ServiceNotFoundError as err:
            raise ServiceNotFoundError(key, *err.resolve_chain)

    def enter(self, context: ContextManager[_T]):
        '''
        enter the context.

        returns the result of the `context.__enter__()` method.
        '''
        with self._lock:
            if self._exit_stack is None:
                self._exit_stack = ExitStack()
            return self._exit_stack.enter_context(context)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        with self._lock:
            if self._exit_stack is not None:
                self._exit_stack.__exit__(*args)
                self._exit_stack = None

    def register_service_info(self, key, service_info: IServiceInfo):
        '''
        register a `IServiceInfo` by key.
        '''
        if not isinstance(service_info, IServiceInfo):
            raise TypeError('service_info must be instance of IServiceInfo.')
        _logger.debug('register %r with key %r', service_info, key)
        return self._services.add(key, service_info)

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
        ssp = ServiceProvider(_services=self._services.scope(), _parent=self)
        return self.enter(ssp)

    @property
    def builder(self):
        '''
        get a new `ServiceProviderBuilder` wrapper for this `ServiceProvider`.
        '''
        from .builder import ServiceProviderBuilder
        return ServiceProviderBuilder(self)
