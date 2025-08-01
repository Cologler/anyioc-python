# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import AbstractContextManager
from enum import Enum
from typing import Any, Protocol, overload, runtime_checkable

from ._primitive_symbol import TypedSymbol


class LifeTime(Enum):
    '''
    Never cache.
    '''
    transient = 0

    '''
    Value is cached per IServiceProvider scope.
    '''
    scoped = 1

    '''
    Value is cached on the IServiceInfo,
    and constructed using the IServiceProvider that owns this IServiceInfo.
    '''
    singleton = 2


@runtime_checkable
class SupportsContext[T](Protocol):
    def __enter__(self) -> T: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> Any: ...

type AllSupportsContext[T] = SupportsContext[T] | AbstractContextManager[T]


class IServiceInfo[T](ABC):
    __slots__ = ()

    @abstractmethod
    def get_service(self, provider, /) -> T:
        raise NotImplementedError

    def get_services(self, provider, /) -> tuple[Any, ...]:
        return (self.get_service(provider),)


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

    @abstractmethod
    def enter[T](self, context: AllSupportsContext[T]) -> T:
        '''
        Enter the context, so that this context exits together when the current provider exits.

        Returns the result of the `context.__enter__()` method.
        '''
        raise NotImplementedError


class Factory[T](Protocol):
    def __call__(self, IServiceProvider, /) -> T: ...
