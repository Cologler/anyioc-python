# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from collections.abc import Callable, Generator, Hashable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from threading import RLock
from typing import Any

from ._internal import Disposable

_NULL_CONTEXT = nullcontext()


@dataclass(frozen=True, slots=True, eq=False)
class _Layer[TK: Hashable, TV]:
    snapshots: dict[TK, tuple[tuple[TV], ...]]
    lock: AbstractContextManager[object]


class ServicesMap[TK: Hashable, TV]:
    def __init__(self, *maps: dict[TK, list[tuple[TV]]], use_lock: bool=True) -> None:
        # A caller can hold the layer lock while registering an entry through add().
        lock = RLock() if use_lock else _NULL_CONTEXT
        self._layers: list[_Layer[TK, TV]] = [
            _Layer({key: tuple(records) for key, records in mapping.items()}, lock)
            for mapping in maps
        ] or [_Layer({}, lock)]
        self._frozen_keys: set[TK] = set()

    def read_lock(self) -> AbstractContextManager[object]:
        """Read the published snapshots without acquiring a layer lock."""
        return _NULL_CONTEXT

    def write_lock(self) -> AbstractContextManager[object]:
        """Serialize writers to the current layer."""
        return self._layers[0].lock

    def resolve(self, key: TK) -> Generator[TV, Any, None]:
        """Yield each layer's registrations in reverse order."""
        for layer in self._layers:
            # Writers replace the tuple so a suspended iterator keeps its snapshot.
            for record in reversed(layer.snapshots.get(key, ())):
                yield record[0]

    def add(self, key: TK, value: TV) -> Disposable:
        layer = self._layers[0]
        with layer.lock:
            if key in self._frozen_keys:
                raise RuntimeError(f'Key {key!r} is frozen.')

            # Each registration needs its own identity even when values are equal.
            record = (value,)
            snapshot = layer.snapshots.get(key, ())
            layer.snapshots[key] = (*snapshot, record)

        def dispose() -> None:
            with layer.lock:
                snapshot = layer.snapshots[key]
                layer.snapshots[key] = tuple(item for item in snapshot if item is not record)

        return Disposable(dispose)

    def freeze_key(self, key: TK) -> None:
        with self._layers[0].lock:
            self._frozen_keys.add(key)

    def __setitem__(self, key: TK, value: TV) -> None:
        self.add(key, value)

    def _latest_record(self, key: TK) -> tuple[TV] | None:
        for layer in self._layers:
            if snapshot := layer.snapshots.get(key):
                return snapshot[-1]
        return None

    def __getitem__(self, key: TK) -> TV:
        record = self._latest_record(key)
        if record is None:
            raise KeyError(key)
        return record[0]

    def get[TD](self, key: TK, default: TD=None) -> TV | TD:
        record = self._latest_record(key)
        return record[0] if record is not None else default

    def add_if_new(self, key: TK, factory: Callable[[], TV]) -> Disposable | None:
        """Register a value only if no visible entry exists for the key."""
        with self.write_lock():
            if self._latest_record(key) is not None:
                return None

            return self.add(key, factory())

    def get_many(self, key: TK) -> list[TV]:
        'get items as list'
        return list(self.resolve(key))

    def snapshot_registrations(self) -> list[list[tuple[TK, TV]]]:
        """Copy registrations by layer, from the current scope to the root."""
        layers: list[list[tuple[TK, TV]]] = []
        for layer in self._layers:
            with layer.lock:
                registrations = [
                    (key, record[0])
                    for key, records in layer.snapshots.items()
                    for record in reversed(records)
                ]
            layers.append(registrations)
        return layers

    def scope(self, use_lock: bool=False) -> 'ServicesMap[TK, TV]':
        scoped = self.__class__(use_lock=use_lock)
        # Share the owners' published snapshots and writer locks.
        scoped._layers.extend(self._layers)
        return scoped
