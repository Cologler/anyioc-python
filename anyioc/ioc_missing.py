# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod

from .err import ServiceNotFoundError

class IMissingResolver:
    @abstractmethod
    def get(self, provider, key):
        '''
        get the `IServiceInfo` from resolver.
        '''
        raise NotImplementedError


class MissingResolver(IMissingResolver):
    '''
    the default missing resolver
    '''

    def get(self, provider, key):
        raise ServiceNotFoundError(key)
