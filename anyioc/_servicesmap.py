# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from collections.abc import Generator, Hashable
from contextlib import nullcontext
from logging import getLogger
from threading import Lock
from typing import Any, overload

from ._internal import Disposable
from ._primitive_symbol import TypedSymbol, _Symbol
from ._service_info import IServiceInfo

_NULL_CONTEXT = nullcontext()
_logger = getLogger(__name__)

_MAP_TYPE = dict[Hashable, list[tuple[_Symbol, IServiceInfo]]]

class ServicesMap:
    def __init__(self, *maps: _MAP_TYPE, use_lock: bool=True) -> None:
        self._lock = Lock() if use_lock else _NULL_CONTEXT
        self._frozen_keys = set()
        self.maps: list[_MAP_TYPE] = list(maps) or [{}]

    def resolve(self, key: Hashable) -> Generator[IServiceInfo[Any], Any, None]:
        '''
        Resolve values with reversed order.
        '''
        with self._lock:
            for mapping in self.maps:
                yield from (v for _, v in reversed(mapping.get(key, ())))

    def add(self, key: Hashable, value: IServiceInfo) -> Disposable:

        with self._lock:
            if key in self._frozen_keys:
                raise RuntimeError(f'Key {key!r} is frozen.')

            internal_value = (_Symbol(), value) # ensure dispose the right value
            self.maps[0].setdefault(key, []).append(internal_value)

        def dispose() -> None:
            try:
                with self._lock:
                    self.maps[0][key].remove(internal_value)
            except ValueError:
                _logger.warning('dispose() is called after the key be removed.')
                pass

        return Disposable(dispose)

    def freeze_key(self, key: Hashable) -> None:
        with self._lock:
            self._frozen_keys.add(key)

    def __setitem__(self, key: Hashable, value: IServiceInfo) -> None:
        self.add(key, value)

    @overload
    def __getitem__[T](self, key: TypedSymbol[T]) -> IServiceInfo[T]: ...
    @overload
    def __getitem__(self, key: Hashable) -> IServiceInfo[Any]: ...
    def __getitem__(self, key: Hashable) -> IServiceInfo[Any]:
        'get item or raise `KeyError`` if not found'
        for value in self.resolve(key):
            return value
        raise KeyError(key)

    @overload
    def get[T, TD](self, key: TypedSymbol[T], default: TD=None) -> IServiceInfo[T] | TD: ...
    @overload
    def get[TD](self, key: Hashable, default: TD=None) -> IServiceInfo[Any] | TD: ...
    def get[TD](self, key: Hashable, default: TD=None) -> IServiceInfo[Any] | TD:
        'get item or `default` if not found'
        for value in self.resolve(key):
            return value
        return default

    def get_many(self, key: Hashable) -> list[IServiceInfo[Any]]:
        'get items as list'
        return list(self.resolve(key))

    def scope(self, use_lock: bool=False) -> 'ServicesMap':
        return self.__class__({}, *self.maps, use_lock=use_lock)
