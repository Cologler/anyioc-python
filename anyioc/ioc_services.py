# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from collections.abc import MutableMapping
from collections import ChainMap

class ServicesMap(ChainMap):
    def __init__(self, *maps):
        self.maps = list(maps) or [{}]

    def __missing__(self, key):
        raise KeyError(key)

    def __getitem__(self, key):
        for mapping in self.maps:
            try:
                services: list = mapping[key]
                return services[-1]
            except KeyError:
                pass
        return self.__missing__(key)

    def __setitem__(self, key, value):
        mapping0: dict = self.maps[0]
        services = mapping0.setdefault(key, [])
        services.append(value)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def get_many(self, key):
        services = []
        for mapping in self.maps:
            try:
                services.extend(reversed(mapping[key]))
            except KeyError:
                pass
        return services

    def scope(self):
        return self.__class__({}, *self.maps)
