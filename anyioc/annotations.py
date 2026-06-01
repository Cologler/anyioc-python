# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from dataclasses import dataclass, field
from typing import Callable, Hashable, Iterable

from ._bases import LifeTime

_UNSET_KEY = object()
_UNSET_DEFAULT = object()


@dataclass(frozen=True, slots=True, eq=False)
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

    key: Hashable = field(default=_UNSET_KEY)
    default: object = field(default=_UNSET_DEFAULT)
    # kwonly:
    lifetime: LifeTime = field(default=LifeTime.transient, kw_only=True)
    name: str | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        if self.lifetime == LifeTime.singleton:
            # we don't known which IServiceProvider own this.
            raise ValueError('Singleton lifetime for InjectBy is not allowed.')

        if self.has_key() and self.has_name():
            raise ValueError('key and name cannot use togeter.')

        if not self.has_key() and not self.has_name():
            raise ValueError('Missing key or name.')

    def has_key(self) -> bool:
        return self.key is not _UNSET_KEY

    def has_name(self) -> bool:
        return self.name is not None

    def has_default(self) -> bool:
        return self.default is not _UNSET_DEFAULT


@dataclass(frozen=True, slots=True, eq=False)
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
    keys: Iterable[Hashable]


@dataclass(frozen=True, slots=True, eq=False)
class InjectWithValue:
    '''
    Inject with the fixed value.

    Equals:

    ```
    value
    ```

    For VAR_POSITIONAL parameter, this is not allowed.
    '''
    value: object


@dataclass(frozen=True, slots=True, eq=False)
class InjectFrom:
    '''
    Inject from a callable.

    The callable is resolved through the `IServiceProvider`,
    so its own parameters are injected by the container.
    If the callable cannot be resolved, the annotated parameter's
    default value is not used as a fallback.

    For example:

    ``` py
    def callee(value: int) -> int:
        return value

    def caller(value: Annotated[object, InjectFrom(callee)] = 200) -> object:
        return value

    provider.resolve(caller) # raises ServiceNotFoundError for int
    ```
    '''

    func: Callable[..., object]
    enter_context: bool | None = None


@dataclass(frozen=True, slots=True, eq=False)
class DontInject:
    pass


@dataclass(frozen=True, slots=True, eq=False)
class _InjectableInfo:
    lifetime: LifeTime
    key: Hashable

    def iter_keys(self) -> Iterable[Hashable]:
        yield self.key


def injectable[T: type](
        lifetime: LifeTime
    ) -> Callable[[T], T]:
    '''
    Indicate that the class is injectable.
    '''

    if lifetime == LifeTime.transient:
        raise ValueError('transient is the default lifetime, no need to use this decorator.')

    def decorator(cls: T) -> T:
        if not isinstance(cls, type):
            raise TypeError('injectable can only be used to decorate class.')

        info: _InjectableInfo = _InjectableInfo(
            lifetime=lifetime,
            key=cls,
        )
        setattr(cls, '__anyioc_injectable__', info)
        return cls

    return decorator

def _get_injectable_info(obj: object) -> _InjectableInfo | None:
    return getattr(obj, '__anyioc_injectable__', None)


__all__ = [
    'InjectBy',
    'InjectByGroup',
    'InjectFrom',
    'InjectWithValue',
    'DontInject',
    'injectable',
]
