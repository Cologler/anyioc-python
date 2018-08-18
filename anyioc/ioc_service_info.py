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
    @abstractmethod
    def get(self, provider) -> Any:
        raise NotImplementedError


class ServiceInfo(IServiceInfo):
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

    def get(self, provider):
        if self._lifetime == LifeTime.transient:
            return self._factory(provider)
        if self._lifetime == LifeTime.singleton:
            provider = provider[Symbols.provider_root]
        cache = provider[Symbols.cache]
        if self._key not in cache:
            cache[self._key] = self._factory(provider)
        return cache[self._key]


class ProviderServiceInfo(IServiceInfo):
    def get(self, provider):
        return provider


class ValueServiceInfo(IServiceInfo):
    def __init__(self, value):
        self._value = value

    def get(self, provider):
        return self._value


class CacheServiceInfo(IServiceInfo):
    def get(self, provider):
        # pylint: disable=W0212
        return provider._cache
