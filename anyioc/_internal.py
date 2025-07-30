# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from collections.abc import MutableMapping
from contextlib import nullcontext
from threading import RLock
from typing import Any, ReadOnly, TypedDict

_NULL_CONTEXT = nullcontext()


class ProviderOptions(TypedDict):
    auto_enter: ReadOnly[bool]


class ScopedCache(MutableMapping):
    def __init__(self, use_lock: bool) -> None:
        super().__init__()
        self._dict: dict[Any, Any] = dict()
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
