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
from typing import Any

from ._internal import Disposable
from ._primitive_symbol import _Symbol

_NULL_CONTEXT = nullcontext()
_logger = getLogger(__name__)

class ServicesMap[TK: Hashable, TV]:
    def __init__(self, *maps: dict[TK, list[tuple[_Symbol, TV]]], use_lock: bool=True) -> None:
        self._lock = Lock() if use_lock else _NULL_CONTEXT
        self._frozen_keys = set()
        self.maps: list[dict[TK, list[tuple[_Symbol, TV]]]] = list(maps) or [{}]

    def resolve(self, key: TK) -> Generator[TV, Any, None]:
        '''
        Resolve values with reversed order.
        '''
        with self._lock:
            for mapping in self.maps:
                yield from (v for _, v in reversed(mapping.get(key, ())))

    def add(self, key: TK, value: TV) -> Disposable:

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

        return Disposable(dispose)

    def freeze_key(self, key: TK) -> None:
        with self._lock:
            self._frozen_keys.add(key)

    def __setitem__(self, key: TK, value: TV) -> None:
        self.add(key, value)

    def __getitem__(self, key: TK) -> TV:
        'get item or raise `KeyError`` if not found'
        for value in self.resolve(key):
            return value
        raise KeyError(key)

    def get[TD](self, key: TK, default: TD=None) -> TV | TD:
        'get item or `default` if not found'
        for value in self.resolve(key):
            return value
        return default

    def get_many(self, key: TK) -> list[TV]:
        'get items as list'
        return list(self.resolve(key))

    def scope(self, use_lock: bool=False) -> 'ServicesMap':
        return self.__class__({}, *self.maps, use_lock=use_lock)
