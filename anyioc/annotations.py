# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from typing import Any, override

from ._bases import IServiceInfo, IServiceProvider, LifeTime
from ._service_info import GetOrDefaultServiceInfo, LifetimeServiceInfo, ValueServiceInfo


class InjectBy(IServiceInfo[Any]):
    _UNSET = object()
    __slots__ = ('key', 'default', '_service_info')

    def __init__(self, key: Any, default: Any=_UNSET, *,
            lifetime: LifeTime = LifeTime.transient,
        ) -> None:

        if lifetime == LifeTime.singleton:
            # we don't known which IServiceProvider own this.
            raise RuntimeError(
                'Singleton lifetime for InjectBy is not allowed.'
            )

        if default is self._UNSET:
            service_info = GetOrDefaultServiceInfo(key)
        else:
            service_info = GetOrDefaultServiceInfo(key, default)

        if lifetime != LifeTime.transient:
            service_info = LifetimeServiceInfo(
                service_provider=None,
                key=None,
                service_info=service_info,
                lifetime=lifetime,
            )

        self._service_info = service_info

    @override
    def get_service(self, provider: IServiceProvider):
        return self._service_info.get_service(provider)


class InjectByGroup(IServiceInfo[tuple[Any, ...]]):
    '''
    Inject args as tuple group.

    Equals:

    ```
    tuple(provider[k] for k in keys)
    ```
    '''
    __slots__ = ('_keys',)

    def __init__(self, *keys: Any):
        self._keys = keys

    @override
    def get_service(self, provider: IServiceProvider):
        return tuple(provider[k] for k in self._keys)


class InjectWithValue[T](ValueServiceInfo[T]):
    '''
    Inject with the fixed value.
    '''
    __slots__ = ()


__all__ = [
    'InjectBy',
    'InjectByGroup',
    'InjectWithValue'
]
