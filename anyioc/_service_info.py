# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import inspect
from contextlib import nullcontext
from enum import Enum
from threading import RLock
from typing import Any, Callable, override

from ._bases import IServiceInfo, IServiceProvider
from ._utils import create_service, get_frameinfos, wrap_signature
from .symbols import Symbols

_NULL_CONTEXT = nullcontext()


class LifeTime(Enum):
    transient = 0
    scoped = 1
    singleton = 2


class ServiceInfo[T](IServiceInfo[T]):
    '''generic `IServiceInfo`.'''

    __slots__ = (
        '_key', '_lifetime', '_factory', '_factory_origin',
        # for not transient
        '_lock',
        # for singleton
        '_cached_value', '_service_provider',
        # options
        '_options',
    )

    _NOT_ALLOWED_KEYS = frozenset([
        Symbols.provider_options,
        Symbols.cache,
    ])

    def __init__(self, service_provider: IServiceProvider, key, factory: Callable[..., T], lifetime):
        if key in self._NOT_ALLOWED_KEYS:
            raise ValueError(f'key {key!r} is not allowed')

        self._factory_origin = factory
        self._factory = wrap_signature(factory)

        self._key = key
        self._lifetime = lifetime
        self._options = service_provider[Symbols.provider_options]

        if self._lifetime != LifeTime.transient:
            self._lock = RLock()
        else:
            self._lock = _NULL_CONTEXT

        if self._lifetime == LifeTime.singleton:
            # service_provider is required when the lifetime is singleton
            self._service_provider: IServiceProvider | None = service_provider
            # the resolved value maybe a None, so we should cache it as a tuple.
            self._cached_value: tuple[T] | None = None

    def __repr__(self) -> str:
        return f'<{self._lifetime} service from {self._factory_origin!r}>'

    @override
    def get_service(self, provider: IServiceProvider) -> T:
        if self._lifetime is LifeTime.transient:
            return self._create(provider)

        if self._lifetime is LifeTime.scoped:
            return self._from_scoped(provider)

        if self._lifetime is LifeTime.singleton:
            return self._from_singleton()

        raise NotImplementedError(f'what is {self._lifetime}?')

    def _from_scoped(self, provider: IServiceProvider) -> T:
        cache = provider[Symbols.cache]
        try:
            return cache[self]
        except KeyError:
            pass
        with self._lock:
            try:
                return cache[self]
            except KeyError:
                pass
            service = self._create(provider)
            cache[self] = service
            return service

    def _from_singleton(self) -> T:
        if (cached_value := self._cached_value) is None:
            with self._lock:
                if (cached_value := self._cached_value) is None:
                    service_provider = self._service_provider
                    assert service_provider
                    self._cached_value = cached_value = (self._create(service_provider),)
        return cached_value[0]

    def _create(self, provider: IServiceProvider) -> T:
        '''
        return the finally service instance.
        '''
        return create_service(provider, self._factory, options=self._options)


class ProviderServiceInfo(IServiceInfo[IServiceProvider]):
    '''
    Get current `ServiceProvider`.
    '''

    __slots__ = ()

    def __repr__(self) -> str:
        return '<(ioc) => ioc>'

    @override
    def get_service(self, provider: IServiceProvider):
        return provider


class GetAttrServiceInfo(IServiceInfo[Any]):
    '''
    Call `getattr()` from current `ServiceProvider`.
    '''

    __slots__ = ('_getattr_args',)
    _UNSET = object()

    def __init__(self, attr_name: str, attr_default: Any=_UNSET):
        super().__init__()
        self._getattr_args = (attr_name,) if attr_default is self._UNSET else (attr_name, attr_default)

    def __repr__(self) -> str:
        getattr_args = ', '.join(repr(x) for x in self._getattr_args)
        return f'<(ioc) => getattr(ioc, {getattr_args})>'

    @override
    def get_service(self, provider: IServiceProvider):
        return getattr(provider, *self._getattr_args)


class ValueServiceInfo[T](IServiceInfo[T]):
    '''a `IServiceInfo` use for get fixed value.'''

    __slots__ = ('_value',)

    def __init__(self, value: T):
        self._value = value

    def __repr__(self) -> str:
        return f'<(_) => {self._value!r}>'

    @override
    def get_service(self, provider: IServiceProvider) -> T:
        return self._value


class BindedServiceInfo(IServiceInfo[Any]):
    '''a `IServiceInfo` use for get value from target key.'''

    __slots__ = ('_target_key',)

    def __init__(self, target_key: Any):
        self._target_key = target_key

    def __repr__(self) -> str:
        return f'<(ioc) => ioc[{self._target_key!r}]>'

    @override
    def get_service(self, provider: IServiceProvider):
        return provider[self._target_key]


class CallerFrameServiceInfo(IServiceInfo[inspect.FrameInfo | None]):
    'a `IServiceInfo` use for get caller frameinfo'

    __slots__ = ()

    @override
    def get_service(self, provider: IServiceProvider):
        for f in get_frameinfos(exclude_anyioc_frames=True):
            return f
