# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from typing import Any, override

from ._bases import IServiceInfo, IServiceProvider
from ._service_info import ValueServiceInfo


class InjectBy(IServiceInfo[Any]):
    _UNSET = object()
    __slots__ = ('key', 'default')

    def __init__(self, key: Any, default: Any=_UNSET) -> None:
        self.key = key
        self.default = default

    @override
    def get_service(self, provider: IServiceProvider):
        if self.default is self._UNSET:
            return provider[self.key]
        else:
            return provider.get(self.key, self.default)


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
