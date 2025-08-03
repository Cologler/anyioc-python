# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from dataclasses import dataclass, field
from typing import Any, Iterable

from ._bases import LifeTime
from ._service_info import GetOrDefaultServiceInfo


@dataclass(frozen=True, slots=True)
class InjectBy:
    '''
    Inject args by key.

    Equals:

    ```
    provider.get(key, default) if has_default() else provider[key]
    ```

    For VAR_POSITIONAL parameter, this equals:

    ```
    * provider.get_many(key)
    ```
    '''

    key: Any
    default: Any = field(default=GetOrDefaultServiceInfo._UNSET)
    lifetime: LifeTime = field(default=LifeTime.transient, kw_only=True)

    def __post_init__(self):
        if self.lifetime == LifeTime.singleton:
            # we don't known which IServiceProvider own this.
            raise RuntimeError(
                'Singleton lifetime for InjectBy is not allowed.'
            )

    def has_default(self):
        return self.default is not GetOrDefaultServiceInfo._UNSET


@dataclass(frozen=True, slots=True)
class InjectByGroup:
    '''
    Inject args as tuple group.

    Equals:

    ```
    tuple(provider[k] for k in keys)
    ```

    For VAR_POSITIONAL parameter, this equals:

    ```
    * tuple(provider[k] for k in keys)
    ```
    '''
    keys: Iterable[Any]


@dataclass(frozen=True, slots=True)
class InjectWithValue:
    '''
    Inject with the fixed value.

    Equals:

    ```
    value
    ```

    For VAR_POSITIONAL parameter, this equals:

    ```
    * (value, )
    ```
    '''
    value: Any


__all__ = [
    'InjectBy',
    'InjectByGroup',
    'InjectWithValue'
]
