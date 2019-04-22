# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod
from enum import Enum
from inspect import signature, Parameter
from typing import Any

from .symbols import Symbols


class LifeTime(Enum):
    transient = 0
    scoped = 1
    singleton = 2


class IServiceInfo:
    __slots__ = ()

    @abstractmethod
    def get(self, provider) -> Any:
        raise NotImplementedError


class ServiceInfo(IServiceInfo):
    __slots__ = ('_key', '_lifetime', '_cache_value', '_factory')

    def __init__(self, key, factory, lifetime):

        sign = signature(factory)
        if not sign.parameters:
            self._factory = lambda _: factory()
        elif len(sign.parameters) == 1:
            arg_0 = list(sign.parameters.values())[0]
            if arg_0.kind != Parameter.POSITIONAL_OR_KEYWORD:
                raise TypeError('1st parameter of factory must be a positional parameter.')
            self._factory = factory
        else:
            raise TypeError('factory has too many parameters.')

        self._key = key
        self._lifetime = lifetime
        self._cache_value = None

    def get(self, provider):
        if self._lifetime is LifeTime.transient:
            return self._factory(provider)

        if self._lifetime is LifeTime.scoped:
            cache = provider[Symbols.cache]
            if self not in cache:
                cache[self] = self._factory(provider)
            return cache[self]

        if self._lifetime is LifeTime.singleton:
            if self._cache_value is None:
                provider = provider[Symbols.provider_root]
                self._cache_value = (self._factory(provider), )
            return self._cache_value[0]

        raise NotImplementedError(f'what is {self._lifetime}?')


class ProviderServiceInfo(IServiceInfo):
    __slots__ = ()

    def get(self, provider):
        return provider


class ValueServiceInfo(IServiceInfo):
    __slots__ = ('_value')

    def __init__(self, value):
        self._value = value

    def get(self, provider):
        return self._value


class GroupedServiceInfo(IServiceInfo):
    __slots__ = ('_keys')

    def __init__(self, keys: list):
        self._keys = keys

    def get(self, provider):
        return tuple(provider[k] for k in self._keys)
