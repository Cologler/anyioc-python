# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from contextlib import nullcontext
from threading import RLock
from typing import Any, final, override

from .._bases import Factory, IServiceInfo, IServiceProvider, LifeTime
from ..symbols import Symbols

_NULL_CONTEXT = nullcontext()


@final
class ProviderServiceInfo(IServiceInfo[IServiceProvider]):
    '''
    Get current `ServiceProvider`.
    '''
    _INSTANCE: 'ProviderServiceInfo'
    __slots__ = ()

    def __repr__(self) -> str:
        return '<(ioc) => ioc>'

    @override
    def get_service(self, provider: IServiceProvider):
        return provider

    @classmethod
    def get_singleton_instance(cls):
        return cls._INSTANCE

ProviderServiceInfo._INSTANCE = ProviderServiceInfo()


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


class FactoryServiceInfo[T](IServiceInfo[T]):
    __slots__ = ('_factory')

    def __init__(self, factory: Factory[T]):
        self._factory = factory

    @override
    def get_service(self, provider: IServiceProvider) -> T:
        return self._factory(provider)


class BoundServiceInfo[T](IServiceInfo[T]):
    __slots__ = (
        '_service_info',
        '_service_provider'
    )

    def __init__(self, service_provider: IServiceProvider, service_info: IServiceInfo[T]):
        self._service_info = service_info
        self._service_provider = service_provider

    def __repr__(self) -> str:
        return f'<Bound {self._service_info!r}>'

    @override
    def get_service(self, provider: IServiceProvider) -> T:
        return self._service_info.get_service(self._service_provider)

    @staticmethod
    def wrap(service_provider: IServiceProvider, service_info: IServiceInfo[T]):
        if type(service_info) is BoundServiceInfo:
            service_info = service_info._service_info
        return BoundServiceInfo(service_provider, service_info)


class LifetimeServiceInfo[T](IServiceInfo[T]):
    __slots__ = (
        '_service_info', '_lifetime',
        # for not transient
        '_lock',
        # for singleton
        '_cached_value',
    )

    _NOT_ALLOWED_KEYS = frozenset([
        Symbols.cache,
    ])

    def __init__(self, *,
            service_provider: IServiceProvider | None,
            key: Any,
            service_info: IServiceInfo[T],
            lifetime: LifeTime,
        ):

        if key in self._NOT_ALLOWED_KEYS:
            raise ValueError(f'Key {key!r} is not allowed')

        if lifetime == LifeTime.singleton:
            assert service_provider is not None
            # service_provider is required when the lifetime is singleton
            service_info = BoundServiceInfo.wrap(service_provider, service_info)
            # the resolved value maybe a None, so we should cache it as a tuple.
            self._cached_value: tuple[T] | None = None

        self._service_info = service_info
        self._lifetime = lifetime

        if self._lifetime != LifeTime.transient:
            self._lock = RLock()
        else:
            self._lock = _NULL_CONTEXT

    def __repr__(self) -> str:
        return f'<{self._lifetime} service from {self._service_info!r}>'

    @override
    def get_service(self, provider: IServiceProvider) -> T:
        if self._lifetime is LifeTime.transient:
            return self._create(provider)

        if self._lifetime is LifeTime.scoped:
            return self._from_scoped(provider)

        if self._lifetime is LifeTime.singleton:
            return self._from_singleton(provider)

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

    def _from_singleton(self, provider: IServiceProvider) -> T:
        if (cached_value := self._cached_value) is None:
            with self._lock:
                if (cached_value := self._cached_value) is None:
                    self._cached_value = cached_value = (self._create(provider),)
        return cached_value[0]

    def _create(self, provider: IServiceProvider) -> T:
        '''
        return the finally service instance.
        '''
        return self._service_info.get_service(provider)


class GetOrDefaultServiceInfo(IServiceInfo[Any]):
    _UNSET = object()
    __slots__ = ('key', 'default')

    def __init__(self, key: Any, default: Any=_UNSET) -> None:
        self.key = key
        self.default = default

    def __repr__(self) -> str:
        if self.default is self._UNSET:
            return f'<(ioc) => ioc[{self.key!r}]>'
        else:
            return f'<(ioc) => ioct.({self.key!r}, {self.default!r})>'

    @override
    def get_service(self, provider: IServiceProvider):
        if self.default is self._UNSET:
            return provider[self.key]
        else:
            return provider.get(self.key, self.default)
