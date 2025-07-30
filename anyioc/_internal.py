# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from collections.abc import MutableMapping
from contextlib import AbstractContextManager, nullcontext
from threading import RLock
from typing import Any, Callable, Protocol, TypedDict, runtime_checkable

from typing_extensions import ReadOnly

_NULL_CONTEXT = nullcontext()

@runtime_checkable
class SupportsContext[T](Protocol):
    def __enter__(self) -> T: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> Any: ...

type AllSupportsContext[T] = SupportsContext[T] | AbstractContextManager[T]

class ProviderOptions(TypedDict):
    auto_enter: ReadOnly[bool]


class LockedMapping[TK, TV](MutableMapping[TK, TV]):
    def __init__(self, use_lock: bool) -> None:
        super().__init__()
        self._dict: dict[TK, TV] = dict()
        # The lock may be acquired multiple times,
        # as it is used to prevent repeated calls.
        self._lock = RLock() if use_lock else _NULL_CONTEXT

    @property
    def lock(self):
        return self._lock

    def __iter__(self):
        with self._lock:
            return iter(self._dict)

    def __len__(self) -> int:
        with self._lock:
            return len(self._dict)

    def __getitem__(self, key):
        with self._lock:
            return self._dict[key]

    def __setitem__(self, key, value) -> None:
        with self._lock:
            self._dict[key] = value

    def __delitem__(self, key) -> None:
        with self._lock:
            del self._dict[key]


class Disposable:
    __slots__ = ('dispose',)

    def __init__(self, dispose: Callable[[], None]) -> None:
        self.dispose = dispose

    def __call__(self):
        if dispose := self.dispose:
            self.dispose = None
            dispose()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if dispose := self.dispose:
            self.dispose = None
            dispose()
