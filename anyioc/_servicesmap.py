# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from collections.abc import Generator, Hashable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from logging import getLogger
from threading import Lock
from typing import Any

from ._internal import Disposable

_NULL_CONTEXT = nullcontext()
_logger = getLogger(__name__)


@dataclass(frozen=True, slots=True, eq=False)
class _Layer[TK: Hashable, TV]:
    registrations: dict[TK, list[tuple[TV]]]
    lock: AbstractContextManager[object]


class ServicesMap[TK: Hashable, TV]:
    def __init__(self, *maps: dict[TK, list[tuple[TV]]], use_lock: bool=True) -> None:
        lock = Lock() if use_lock else _NULL_CONTEXT
        self._layers = [_Layer(mapping, lock) for mapping in maps or ({},)]
        self._frozen_keys: set[TK] = set()

    def resolve(self, key: TK) -> Generator[TV, Any, None]:
        """Yield each layer's registrations in reverse order."""
        for layer in self._layers:
            with layer.lock:
                snapshot = tuple(layer.registrations.get(key, ()))
            # Iteration can suspend while the owner changes its registrations.
            for record in reversed(snapshot):
                yield record[0]

    def add(self, key: TK, value: TV) -> Disposable:
        layer = self._layers[0]
        with layer.lock:
            if key in self._frozen_keys:
                raise RuntimeError(f'Key {key!r} is frozen.')

            record = (value,) # ensure dispose the right value
            vec = layer.registrations.setdefault(key, [])
            inserted_index = len(vec) # no insert func, so we can cache this index
            vec.append(record)

        def dispose() -> None:
            try:
                with layer.lock:
                    # in most case, the del is del from end.
                    for i in range(min(inserted_index, len(vec) - 1), -1, -1):
                        if vec[i] is record:
                            del vec[i]
            except ValueError:
                _logger.warning('dispose() is called after the key be removed.')

        return Disposable(dispose)

    def freeze_key(self, key: TK) -> None:
        with self._layers[0].lock:
            self._frozen_keys.add(key)

    def __setitem__(self, key: TK, value: TV) -> None:
        self.add(key, value)

    def _latest_record(self, key: TK) -> tuple[TV] | None:
        for layer in self._layers:
            with layer.lock:
                if records := layer.registrations.get(key):
                    return records[-1]
        return None

    def __getitem__(self, key: TK) -> TV:
        record = self._latest_record(key)
        if record is None:
            raise KeyError(key)
        return record[0]

    def get[TD](self, key: TK, default: TD=None) -> TV | TD:
        record = self._latest_record(key)
        return record[0] if record is not None else default

    def get_many(self, key: TK) -> list[TV]:
        'get items as list'
        return list(self.resolve(key))

    def scope(self, use_lock: bool=False) -> 'ServicesMap[TK, TV]':
        scoped = self.__class__(use_lock=use_lock)
        # Reuse the locks that guard writes to the inherited registrations.
        scoped._layers.extend(self._layers)
        return scoped
