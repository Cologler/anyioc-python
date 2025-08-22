# -*- coding: utf-8 -*-
#
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import contextlib
import types
from typing import Annotated, Iterator, Self, assert_type, cast
from unittest.mock import MagicMock

from anyioc import InjectFrom, ServiceProvider


class ContextManager:
    def __init__(self) -> None:
        self.value = 0

    def __enter__(self) -> Self:
        self.value = 1
        return self

    def __exit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None:
        self.value = 2


def test_enter() -> None:
    cleanup = MagicMock()
    @contextlib.contextmanager
    def ctx() -> Iterator[None]:
        yield
        cleanup()

    provider = ServiceProvider()
    with provider.scope() as scoped:
        scoped.enter(ctx())
        cleanup.assert_not_called()
    cleanup.assert_called_once()

def test_enter_return_type() -> None:
    @contextlib.contextmanager
    def ctx() -> Iterator[int]:
        yield 42

    provider = ServiceProvider()
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


def test_injectfrom_with_enter_context_is_true() -> None:
    cleanup = MagicMock()
    @contextlib.contextmanager
    def ctxmgr() -> Iterator[int]:
        yield 42
        cleanup()

    def func_with_inject_from_contextmanager(val: Annotated[int, InjectFrom(ctxmgr, enter_context=True)]) -> int:
        return val

    root_provider = ServiceProvider()
    with root_provider.scope() as provider:
        assert provider.resolve(func_with_inject_from_contextmanager) == 42
        cleanup.assert_not_called()
    cleanup.assert_called_once()


def test_injectfrom_with_enter_context_is_true_for_generator() -> None:
    cleanup = MagicMock()
    def gen() -> Iterator[int]:
        yield 42
        cleanup()

    def func_with_inject_from_contextmanager(val: Annotated[int, InjectFrom(gen, enter_context=True)]) -> int:
        return val

    root_provider = ServiceProvider()
    with root_provider.scope() as provider:
        assert provider.resolve(func_with_inject_from_contextmanager) == 42
        cleanup.assert_not_called()
    cleanup.assert_called_once()
