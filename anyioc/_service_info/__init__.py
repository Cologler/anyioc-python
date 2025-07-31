# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from typing import Any, override

from .._bases import Factory, IServiceInfo, IServiceProvider


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


class FactoryServiceInfo[T](IServiceInfo[T]):
    __slots__ = ('_factory')

    def __init__(self, factory: Factory[T]):
        self._factory = factory

    @override
    def get_service(self, provider: IServiceProvider) -> T:
        return self._factory(provider)
