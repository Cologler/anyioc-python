# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import Dict, List, Any, Iterable

class ServicesMap:
    def __init__(self, *maps):
        self.maps: List[Dict[Any, list]] = list(maps) or [{}]

    def resolve(self, key):
        '''
        resolve items with reverse order.
        '''
        for mapping in self.maps:
            yield from reversed(mapping.get(key, []))

    def __setitem__(self, key, value):
        self.maps[0].setdefault(key, []).append(value)

    def __getitem__(self, key):
        'get item or raise `KeyError`` if not found'
        for value in self.resolve(key):
            return value
        raise KeyError(key)

    def get(self, key, default=None):
        'get item or `default` if not found'
        for value in self.resolve(key):
            return value
        return default

    def get_many(self, key):
        'get items as list'
        return list(self.resolve(key))

    def scope(self):
        return self.__class__({}, *self.maps)
