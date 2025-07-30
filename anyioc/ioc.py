# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import inspect
from abc import abstractmethod
from contextlib import ExitStack, nullcontext
from logging import getLogger
from threading import RLock
from types import MappingProxyType
from typing import Any, Callable, Iterable, Optional, overload, override

from ._internal import AllSupportsContext, ScopedCache
from ._servicesmap import ServicesMap
from ._utils import wrap_signature as _wrap_signature
from .err import ServiceNotFoundError
from .ioc_resolver import ServiceInfoChainResolver
from .ioc_service_info import (
    BindedServiceInfo,
    CallerFrameServiceInfo,
    GetAttrServiceInfo,
    GroupedServiceInfo,
    IServiceInfo,
    LifeTime,
    ProviderServiceInfo,
    ServiceInfo,
    ValueServiceInfo,
)
from .symbols import Symbols, TypedSymbol

_NULL_CONTEXT = nullcontext()

_logger = getLogger(__name__)


class IServiceProvider:
    '''
    the base interface for `ServiceProvider`.
    '''

    @overload
    def __getitem__[T](self, key: TypedSymbol[T]) -> T: ...
    @overload
    def __getitem__(self, key) -> Any: ...
    @abstractmethod
    def __getitem__(self, key) -> Any:
        '''
        Get a service by key.
        '''
        raise NotImplementedError

    @overload
    def get[T, TD](self, key: TypedSymbol[T], d: TD=None) -> T | TD: ...
    @overload
    def get(self, key, d=None) -> Any: ...
    @abstractmethod
    def get(self, key, d=None) -> Any:
        '''
        Get a service by key with default value.
        '''
        raise NotImplementedError

    @overload
    def get_many[T](self, key: TypedSymbol[T]) -> list[T]: ...
    @overload
    def get_many(self, key) -> list[Any]: ...
    @abstractmethod
    def get_many(self, key) -> list[Any]:
        '''
        Get services by key.
        '''
        raise NotImplementedError

    @abstractmethod
    def resolve[R](self, factory: Callable[..., R]) -> R:
        '''
        Resolve the factory direct without register.
        '''
        raise NotImplementedError

    @abstractmethod
    def scope(self, *, use_lock: bool=False) -> 'IServiceProvider':
        '''
        Create a scoped service provider for get scoped services.

        By default, scoped IServiceProvider is not thread safely,
        set `use_lock` to `True` can change this.
        '''
        raise NotImplementedError


class ServiceProvider(IServiceProvider):
    def __init__(self, auto_enter=False, *,
                # internal uses:
                _services: Optional[ServicesMap]=None,
                _parent: Optional['ServiceProvider']=None,
                _use_lock: bool=True,
            ):

        self._exit_stack = None
        self._scoped_cache = ScopedCache(use_lock=_use_lock)
        self._lock = RLock() if _use_lock else _NULL_CONTEXT
        self._parent = _parent

        assert (_parent is None) is (_services is None)

        if _parent is not None:
            assert _services is not None
            # scope provider
            assert auto_enter is False, 'must be default value'
            self._services = _services
            self._root: ServiceProvider = _parent._root

        else:
            assert _use_lock, 'root provider must use lock'
            # root provider
            self._services = ServicesMap(use_lock=True)
            self._root: ServiceProvider = self

            # serviceinfos
            get_current_provicer = ProviderServiceInfo()
            get_frameinfo = CallerFrameServiceInfo()

            self._services[Symbols.provider] = get_current_provicer
            self._services[Symbols.provider_root] = ValueServiceInfo(self)
            self._services[Symbols.provider_parent] = GetAttrServiceInfo('_parent')
            self._services[Symbols.cache] = GetAttrServiceInfo('_scoped_cache')
            self._services[Symbols.missing_resolver] = ValueServiceInfo(ServiceInfoChainResolver())
            self._services[Symbols.caller_frame] = get_frameinfo

            self.__init_hooks = []
            self.__init_exc = None

            # service alias
            self._services['ioc'] = get_current_provicer
            self._services['provider'] = get_current_provicer
            self._services['service_provider'] = get_current_provicer
            self._services[ServiceProvider] = get_current_provicer
            self._services[IServiceProvider] = get_current_provicer
            self._services[inspect.FrameInfo] = get_frameinfo

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
        resolver = self._services[Symbols.missing_resolver].get(self)
        return resolver.get(self, key)

    @overload
    def __getitem__[T](self, key: TypedSymbol[T]) -> T: ...
    @overload
    def __getitem__(self, key) -> Any: ...
    @override
    def __getitem__(self, key) -> Any:
        _logger.debug('get service by key: %r', key)
        self._root.__ensure_init_hooks_called()
        service_info = self._get_service_info(key)
        try:
            return service_info.get(self)
        except ServiceNotFoundError as err:
            raise ServiceNotFoundError(key, *err.resolve_chain)

    @overload
    def get[T, TD](self, key: TypedSymbol[T], d: TD=None) -> T | TD: ...
    @overload
    def get(self, key, d=None) -> Any: ...
    @override
    def get(self, key, d=None) -> Any:
        '''
        Get a service by key with default value.
        '''
        try:
            return self[key]
        except ServiceNotFoundError as err:
            if len(err.resolve_chain) == 1:
                return d
            raise

    @overload
    def get_many[T](self, key: TypedSymbol[T]) -> list[T]: ...
    @overload
    def get_many(self, key) -> list[Any]: ...
    @override
    def get_many(self, key) -> list[Any]:
        '''
        Get services by key.

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

    def resolve[R](self, factory: Callable[..., R], *, follow: bool=False) -> R:
        '''
        Resolve the factory direct without register.
        '''
        return _wrap_signature(factory, follow=follow)(self)

    def enter[T](self, context: AllSupportsContext[T]):
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

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._lock:
            if self._exit_stack is not None:
                self._exit_stack.__exit__(exc_type, exc_val, exc_tb)
                self._exit_stack = None

    def freeze_key(self, key):
        '''

        Freeze key to avoid registering it later.

        Only effective for the current ServiceProvider.
        '''
        self._services.freeze_key(key)

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

    @override
    def scope(self, *, use_lock: bool=False) -> 'ServiceProvider':
        '''
        Create a scoped service provider for get scoped services.

        By default, scoped IServiceProvider is not thread safely,
        set `use_lock` to `True` can change this.
        '''
        ssp = ServiceProvider(
            _services=self._services.scope(use_lock=use_lock),
            _parent=self,
            _use_lock=use_lock,
        )
        return self.enter(ssp)

    @property
    def builder(self):
        '''
        get a new `ServiceProviderBuilder` wrapper for this `ServiceProvider`.
        '''
        from .builder import ServiceProviderBuilder
        return ServiceProviderBuilder(self)
