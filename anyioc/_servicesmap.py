# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import Any, Dict, List, Tuple

Wrapped = Tuple[object, Any]

def wrap(obj) -> Wrapped:
    return (object(), obj)

def unwrap(wrapped: Wrapped):
    return wrapped[1]


class ServicesMap:
    def __init__(self, *maps):
        self.maps: List[Dict[Any, List[Wrapped]]] = list(maps) or [{}]

    def _resolve_key(self, key):
        '''
        resolve values with reversed order.
        '''
        for mapping in self.maps:
            yield from (unwrap(x) for x in reversed(mapping.get(key, [])))

    def __setitem__(self, key, value):
        self.add(key, value)

    def __getitem__(self, key):
        'get item or raise `KeyError`` if not found'
        for value in self._resolve_key(key):
            return value
        raise KeyError(key)

    def get(self, key, default=None):
        'get item or `default` if not found'
        for value in self._resolve_key(key):
            return value
        return default

    def get_many(self, key):
        return self._resolve_key(key)

    def scope(self):
        return self.__class__({}, *self.maps)

    def add(self, key, value):
        wrapped_value = wrap(value) # ensure dispose the right value
        self.maps[0].setdefault(key, []).append(wrapped_value)

        def dispose():
            try:
                self.maps[0][key].remove(wrapped_value)
            except ValueError:
                raise RuntimeError('Cannot call dispose again')

        return Disposable(dispose)


class Disposable():
    __slots__ = ('dispose',)

    def __init__(self, dispose) -> None:
        self.dispose = dispose

    def __call__(self):
        return self.dispose()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.dispose()
