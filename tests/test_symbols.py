# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import inspect
from typing import Iterable

from pytest import raises

from anyioc import ServiceProvider
from anyioc._internal import LockedMapping
from anyioc._primitive_symbol import TypedSymbol, _Symbol
from anyioc.symbols import Symbols


def test_symbol_str() -> None:
    assert str(_Symbol('test')) == "Symbol(test)"
    assert repr(_Symbol('test')) == "Symbol('test')"

    assert str(TypedSymbol[int]('test')) == "TypedSymbol[int](test)"
    assert repr(TypedSymbol[int]('test')) == "TypedSymbol[int]('test')"

    assert str(TypedSymbol['int']('test')) == "TypedSymbol[int](test)"
    assert repr(TypedSymbol['int']('test')) == "TypedSymbol[int]('test')"

def test_symbols_has_no_vars() -> None:
    assert not hasattr(_Symbol(), '__dict__')
    assert not hasattr(TypedSymbol(), '__dict__')

def test_typed_symbol() -> None:
    assert TypedSymbol[int]('test').get_type() is int
    with raises(TypeError):
        assert TypedSymbol('test').get_type()

def test_symbol_caller_frame() -> None:
    provider = ServiceProvider()
    fr = provider[Symbols.caller_frame]
    assert isinstance(fr, inspect.FrameInfo)
    mo = inspect.getmodule(fr.frame)
    assert mo is not None
    assert mo.__name__ == 'test_symbols'

def test_symbol_caller_frame_from_deep() -> None:
    provider = ServiceProvider()
    def get_name(ioc: ServiceProvider) -> str:
        fr = ioc[Symbols.caller_frame]
        assert isinstance(fr, inspect.FrameInfo)
        mo = inspect.getmodule(fr.frame)
        assert mo is not None
        return mo.__name__
    provider.register_transient('name', get_name)
    assert provider['name'] == 'test_symbols'

def _create_scopes(provider: ServiceProvider, count: int=5) -> list[ServiceProvider]:
    providers = [provider]
    for i in range(0, count):
        providers.append(providers[-1].scope())
    return providers

def assert_get_many_returns_one_item(providers: Iterable[ServiceProvider], key: object) -> None:
    assert all(
        len(sp.get_many(Symbols.provider_root)) == 1 for sp in providers
    )

def test_symbol_provider_root() -> None:
    root_provider = ServiceProvider()
    providers = _create_scopes(root_provider)
    assert all(
        sp[Symbols.provider_root] is root_provider for sp in providers
    )
    assert_get_many_returns_one_item(providers, Symbols.provider_root)

def test_symbol_provider_parent() -> None:
    providers = _create_scopes(ServiceProvider())
    assert all(
        sp[Symbols.provider_parent] is (None if i == 0 else providers[i-1])
        for i, sp in enumerate(providers)
    )
    assert_get_many_returns_one_item(providers, Symbols.provider_parent)

def test_symbol_cache() -> None:
    providers = _create_scopes(ServiceProvider())
    assert all(
        isinstance(sp[Symbols.cache], LockedMapping) for sp in providers
    )
    assert_get_many_returns_one_item(providers, Symbols.cache)

def test_symbol_at_init() -> None:
    providers = _create_scopes(ServiceProvider())
    assert all(
        sp[Symbols.at_init] is False for sp in providers
    )
    assert_get_many_returns_one_item(providers, Symbols.at_init)

def test_symbol_at_init_in_init_hooks() -> None:
    provider = ServiceProvider()

    @provider.add_init_hook
    def init_hook() -> None:
        provider.register_value('a', 1)
        assert provider[Symbols.at_init] is True

    assert provider[Symbols.at_init] is False
    assert provider['a'] == 1
    assert provider[Symbols.at_init] is False
