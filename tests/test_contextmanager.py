# -*- coding: utf-8 -*-
#
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import contextlib
import types
from typing import Iterator, Self, assert_type, cast
from unittest.mock import MagicMock

from anyioc import ServiceProvider


class ContextManager:
    def __init__(self) -> None:
        self.value = 0

    def __enter__(self) -> Self:
        self.value = 1
        return self

    def __exit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None:
        self.value = 2


def test_enter() -> None:
    provider = ServiceProvider()
    callback = MagicMock()
    @contextlib.contextmanager
    def ctx() -> Iterator[None]:
        yield
        callback()
    with provider.scope() as scoped:
        scoped.enter(ctx())
        callback.assert_not_called()
    callback.assert_called_once()

def test_enter_return_type() -> None:
    provider = ServiceProvider()

    @contextlib.contextmanager
    def ctx() -> Iterator[int]:
        yield 42

    assert_type(provider.enter(ctx()), int)
    assert_type(provider.enter(ContextManager()), ContextManager)


def test_options_auto_enter_is_false() -> None:
    provider = ServiceProvider(auto_enter=False)
    provider.register_scoped('mgr', ContextManager)
    with provider.scope() as scoped_provider:
        mgr: ContextManager = cast(ContextManager, scoped_provider['mgr'])
        assert mgr.value == 0
    assert mgr.value == 0

def test_options_auto_enter_is_true() -> None:
    provider = ServiceProvider(auto_enter=True)
    provider.register_scoped('mgr', ContextManager)
    with provider.scope() as scoped_provider:
        mgr: ContextManager = cast(ContextManager, scoped_provider['mgr'])
        assert mgr.value == 1
    assert mgr.value == 2

