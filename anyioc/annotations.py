# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

'''Configure dependency injection for classes and parameters.

Use the `@injectable(LifeTime.singleton)` or `@injectable(LifeTime.scoped)`
class decorator to declare a service lifetime.

Use instances of `InjectBy`, `InjectByGroup`, `InjectFrom`, `InjectWithValue`,
and `DontInject` as metadata in `typing.Annotated` on function or constructor
parameters. When the provider resolves the callable with `provider.resolve(...)`,
an annotation such as `port: Annotated[int, InjectBy('port')]` tells it to
look up the parameter by the key `'port'`.
'''

from dataclasses import dataclass, field
from typing import Callable, Hashable, Iterable

from ._bases import LifeTime

_UNSET_KEY = object()
_UNSET_DEFAULT = object()


@dataclass(frozen=True, slots=True, eq=False)
class InjectBy:
    '''Select a service key using `typing.Annotated` metadata.

    Supply either `key` or `name`. With `name`, the provider first looks up
    the `NamedType` formed from that name and the annotated type, then falls
    back to the type alone if the named lookup fails.

    ``` py
    from typing import Annotated

    from anyioc import InjectBy

    def get_port(port: Annotated[int, InjectBy('http_port', default=8080)]) -> int:
        return port
    ```

    Pass `default` to `InjectBy` to supply a fallback for a missing service.
    On `*args`, supply a key to inject all values from `provider.get_many(key)`.
    For `*args`, `name` is invalid and `default` is ignored. `**kwargs` is
    unsupported.

    The default `lifetime` is `LifeTime.transient`. Use `LifeTime.scoped`
    to cache the injected result per scope. `LifeTime.singleton` is invalid
    because the annotation has no owning provider for a singleton cache.
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
    '''Inject a tuple of services using `typing.Annotated` metadata.

    Resolve one service per key in the order given by `keys`.

    ``` py
    from typing import Annotated

    from anyioc import InjectByGroup

    def get_address(address: Annotated[tuple[str, int], InjectByGroup(['host', 'port'])]) -> tuple[str, int]:
        return address
    ```

    On `*args`, the provider unpacks the tuple into positional arguments.
    `**kwargs` is unsupported.
    '''
    keys: Iterable[Hashable]


@dataclass(frozen=True, slots=True, eq=False)
class InjectWithValue:
    '''Supply a fixed value using `typing.Annotated` metadata.

    The provider injects `value` directly, without a service lookup.

    ``` py
    from typing import Annotated

    from anyioc import InjectWithValue

    def get_port(port: Annotated[int, InjectWithValue(8080)]) -> int:
        return port
    ```

    `*args` and `**kwargs` are unsupported.
    '''
    value: object


@dataclass(frozen=True, slots=True, eq=False)
class InjectFrom:
    '''Inject the result of a callable using `typing.Annotated` metadata.

    The service provider injects the callable's own parameters. A missing
    dependency raises `ServiceNotFoundError` even if the annotated parameter
    has a default. `*args` and `**kwargs` are unsupported.

    ``` py
    from typing import Annotated

    from anyioc import InjectFrom

    def make_url(host: str) -> str:
        return f'https://{host}'

    def get_url(url: Annotated[str, InjectFrom(make_url)]) -> str:
        return url
    ```

    Set `enter_context=True` to inject the value obtained by entering the
    returned context manager or the value yielded by a single-yield generator.
    `False` injects the returned object directly, and `None` (the default)
    follows the provider's automatic context-entry rules.
    '''

    func: Callable[..., object]
    enter_context: bool | None = None


@dataclass(frozen=True, slots=True, eq=False)
class DontInject:
    '''Skip service injection for a parameter using `typing.Annotated` metadata.

    Give the parameter a default or supply it through `resolve(..., kwargs=...)`
    if it accepts a keyword argument. On `*args` and `**kwargs`, the provider
    skips automatic injection of items.

    ``` py
    from typing import Annotated

    from anyioc import DontInject

    def get_retries(retries: Annotated[int, DontInject()] = 3) -> int:
        return retries
    ```
    '''


@dataclass(frozen=True, slots=True, eq=False)
class _InjectableInfo:
    lifetime: LifeTime
    key: Hashable

    def iter_keys(self) -> Iterable[Hashable]:
        yield self.key


def injectable[T: type](
        lifetime: LifeTime
    ) -> Callable[[T], T]:
    '''Return a class decorator that declares an injectable service lifetime.

    The provider registers the class under its own type on first lookup if
    the class has no existing registration. Use `LifeTime.singleton` or
    `LifeTime.scoped`. `LifeTime.transient` is rejected because it is the
    default lifetime.

    ``` py
    from anyioc import LifeTime, ServiceProvider, injectable

    @injectable(LifeTime.singleton)
    class Client:
        pass

    provider = ServiceProvider()
    assert provider[Client] is provider[Client]
    ```
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
