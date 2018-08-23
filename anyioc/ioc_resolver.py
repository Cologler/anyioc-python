# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod
from typing import List

from .err import ServiceNotFoundError
from .ioc_service_info import ValueServiceInfo

class IServiceInfoResolver:
    @abstractmethod
    def get(self, provider, key):
        '''
        get the `IServiceInfo` from resolver.
        '''
        raise NotImplementedError

    def __add__(self, other):
        new_resolver = ServiceInfoChainResolver()
        new_resolver.chain.append(self)
        new_resolver.append(other)
        return new_resolver


class EmptyResolver(IServiceInfoResolver):
    '''
    the default missing resolver
    '''

    def get(self, provider, key):
        raise ServiceNotFoundError(key)


class ServiceInfoChainResolver(IServiceInfoResolver):
    '''
    the chain resolver
    '''
    def __init__(self, *resolvers):
        self.chain: List[IServiceInfoResolver] = list(resolvers)

    def get(self, provider, key):
        for resolver in self.chain:
            try:
                return resolver.get(provider, key)
            except ServiceNotFoundError:
                pass
        raise ServiceNotFoundError(key)

    def append(self, other):
        if isinstance(other, ServiceInfoChainResolver):
            self.chain.extend(other.chain)
        else:
            self.chain.append(other)

    def __add__(self, other):
        new_resolver = ServiceInfoChainResolver()
        new_resolver.chain.extend(self.chain)
        new_resolver.append(other)
        return new_resolver


class ImportServiceInfoResolver(IServiceInfoResolver):
    def get(self, provider, key):
        import importlib
        if isinstance(key, str):
            try:
                module = importlib.import_module(key)
            except TypeError:
                raise ServiceNotFoundError(key)
            except ModuleNotFoundError:
                raise ServiceNotFoundError(key)
            return ValueServiceInfo(module)
        raise ServiceNotFoundError(key)
