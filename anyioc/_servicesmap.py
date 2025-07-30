# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import Any, overload

from .ioc_service_info import IServiceInfo
from .symbols import TypedSymbol, _Symbol


class ServicesMap:
    def __init__(self, *maps):
        self.maps: list[dict[Any, list[tuple[_Symbol, IServiceInfo]]]] = list(maps) or [{}]

    def resolve(self, key: Any):
        '''
        Resolve values with reversed order.
        '''
        for mapping in self.maps:
            yield from (v for _s, v in reversed(mapping.get(key, [])))

    def __setitem__(self, key, value):
        self.add(key, value)

    @overload
    def __getitem__[T](self, key: TypedSymbol[T]) -> IServiceInfo[T]: ...
    @overload
    def __getitem__(self, key): ...
    def __getitem__(self, key):
        'get item or raise `KeyError`` if not found'
        for value in self.resolve(key):
            return value
        raise KeyError(key)

    @overload
    def get[T, TD](self, key: TypedSymbol[T], default: TD=None) -> IServiceInfo[T] | TD: ...
    @overload
    def get(self, key, default=None): ...
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

    def add(self, key, value):
        internal_value = (_Symbol(), value) # ensure dispose the right value
        self.maps[0].setdefault(key, []).append(internal_value)

        def dispose():
            try:
                self.maps[0][key].remove(internal_value)
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
