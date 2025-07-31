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
from typing import TYPE_CHECKING, Any, Callable, override

from ._bases import IServiceInfo
from ._internal import SupportsContext
from ._utils import get_frameinfos as _get_frameinfos
from ._utils import wrap_signature as _wrap_signature
from .symbols import Symbols

if TYPE_CHECKING:
    from . import ioc

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
        '_cache_value', '_service_provider',
        # options
        '_options',
    )

    _not_allowed_keys = frozenset([
        Symbols.provider_options,
        Symbols.cache,
    ])

    def __init__(self, service_provider: 'ioc.ServiceProvider', key, factory: Callable[..., T], lifetime):
        if key in self._not_allowed_keys:
            raise ValueError(f'key {key!r} is not allowed')

        self._factory_origin = factory
        self._factory = _wrap_signature(factory)

        self._key = key
        self._lifetime = lifetime
        self._cache_value = None
        self._service_provider = service_provider
        self._options = service_provider[Symbols.provider_options]

        if self._lifetime != LifeTime.transient:
            self._lock = RLock()
        else:
            self._lock = _NULL_CONTEXT

        if self._lifetime == LifeTime.singleton:
            # service_provider is required when lifetime == singleton
            assert self._service_provider is not None

    def __repr__(self) -> str:
        return f'<Service: {self._lifetime}, {self._factory_origin!r}>'

    @override
    def get_service(self, provider: 'ioc.ServiceProvider') -> T:
        if self._lifetime is LifeTime.transient:
            return self._create(provider)

        if self._lifetime is LifeTime.scoped:
            return self._from_scoped(provider)

        if self._lifetime is LifeTime.singleton:
            return self._from_singleton()

        raise NotImplementedError(f'what is {self._lifetime}?')

    def _from_scoped(self, provider: 'ioc.ServiceProvider') -> T:
        cache = provider[Symbols.cache]
        try:
            return cache[self] # type: ignore
        except KeyError:
            pass
        with cache.lock:
            try:
                return cache[self] # type: ignore
            except KeyError:
                service = self._create(provider) # must create with lock
                cache[self] = service
                return service

    def _from_singleton(self) -> T:
        if self._cache_value is None:
            with self._lock:
                if self._cache_value is None:
                    self._cache_value = (
                        self._create(self._service_provider), )
        return self._cache_value[0]

    def _create(self, provider: 'ioc.ServiceProvider') -> T:
        '''
        return the finally service instance.
        '''

        service = self._factory(provider)
        if self._options['auto_enter']:
            wrapped = getattr(self._factory, '__anyioc_wrapped__', self._factory)
            # We must ensure that the original object is a ContextManager.
            # If the original object is a factory function and
            # the ContextManager service is merely the return value of that function,
            # then __enter__ should not be called automatically.
            if isinstance(wrapped, SupportsContext) and isinstance(service, SupportsContext):
                service = provider.enter(service)
        return service # type: ignore


class ProviderServiceInfo(IServiceInfo['ioc.ServiceProvider']):
    '''
    Get current `ServiceProvider`.
    '''

    __slots__ = ()

    def __repr__(self) -> str:
        return '<(ioc) => ioc>'

    @override
    def get_service(self, provider: 'ioc.ServiceProvider'):
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
    def get_service(self, provider: 'ioc.ServiceProvider'):
        return getattr(provider, *self._getattr_args)


class ValueServiceInfo[T](IServiceInfo[T]):
    '''a `IServiceInfo` use for get fixed value.'''

    __slots__ = ('_value',)

    def __init__(self, value: T):
        self._value = value

    def __repr__(self) -> str:
        return f'<(_) => {self._value!r}>'

    @override
    def get_service(self, provider: 'ioc.ServiceProvider') -> T:
        return self._value


class BindedServiceInfo(IServiceInfo[Any]):
    '''a `IServiceInfo` use for get value from target key.'''

    __slots__ = ('_target_key',)

    def __init__(self, target_key: Any):
        self._target_key = target_key

    def __repr__(self) -> str:
        return f'<(ioc) => ioc[{self._target_key!r}]>'

    @override
    def get_service(self, provider: 'ioc.ServiceProvider'):
        return provider[self._target_key]


class CallerFrameServiceInfo(IServiceInfo[inspect.FrameInfo | None]):
    'a `IServiceInfo` use for get caller frameinfo'

    __slots__ = ()

    @override
    def get_service(self, provider: 'ioc.ServiceProvider'):
        for f in _get_frameinfos(exclude_anyioc_frames=True):
            return f
