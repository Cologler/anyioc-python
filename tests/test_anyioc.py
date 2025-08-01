# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from pytest import raises

from anyioc import ServiceProvider
from anyioc.symbols import Symbols


def test_parameters_count():
    provider = ServiceProvider()
    # 0 args
    provider.register_singleton(1, lambda: 101)
    # 1 args
    provider.register_singleton(2, lambda x: 102)
    # 2 args
    with raises(TypeError):
        provider.register_singleton(3, lambda x, y: 103)

    assert provider[1] == 101
    assert provider[2] == 102

def test_symbols_types():
    from anyioc._internal import LockedMapping
    from anyioc.ioc import IServiceProvider
    from anyioc.ioc_resolver import IServiceInfoResolver
    from anyioc.symbols import Symbols

    provider = ServiceProvider()

    assert isinstance(provider[Symbols.provider], IServiceProvider)
    assert isinstance(provider[Symbols.provider_root], IServiceProvider)
    assert isinstance(provider[Symbols.cache], LockedMapping)
    assert isinstance(provider[Symbols.missing_resolver], IServiceInfoResolver)

    with provider.scope() as scoped_provider:
        assert isinstance(scoped_provider[Symbols.provider], IServiceProvider)
        assert isinstance(scoped_provider[Symbols.provider_root], IServiceProvider)
        assert isinstance(scoped_provider[Symbols.cache], LockedMapping)
        assert isinstance(scoped_provider[Symbols.missing_resolver], IServiceInfoResolver)

def test_symbols_values_is():
    root_provider = ServiceProvider()

    assert root_provider[Symbols.provider] is root_provider
    assert root_provider[Symbols.provider_root] is root_provider
    assert root_provider[Symbols.cache] is root_provider[Symbols.cache]

    with root_provider.scope() as scoped_provider:
        assert scoped_provider[Symbols.provider] is scoped_provider
        assert scoped_provider[Symbols.provider_root] is root_provider
        assert scoped_provider[Symbols.cache] is scoped_provider[Symbols.cache]
        assert scoped_provider[Symbols.cache] is not root_provider[Symbols.cache]

def test_options_auto_enter():
    provider = ServiceProvider(auto_enter=True)

    class ContextManager:
        value = 0

        def __enter__(self):
            self.value = 1
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.value = 2

    provider.register_scoped('mgr', ContextManager)
    with provider.scope() as scoped_provider:
        mgr = scoped_provider['mgr']
        assert mgr.value == 1
    assert mgr.value == 2

def test_add_init_hook_should_raises_error_after_initialized():
    provider = ServiceProvider()

    provider.register_value('a', 1)
    assert provider['a'] == 1

    with raises(RuntimeError):
        provider.add_init_hook(lambda _: None)

def test_call_init_hook_default():
    provider = ServiceProvider()

    @provider.add_init_hook
    def init_hook(sp):
        sp.register_value('a', 1)

    assert provider['a'] == 1

def test_call_init_hook_with_recursion():
    provider = ServiceProvider()

    provider.register_value('a', 1)

    @provider.add_init_hook
    def init_hook(sp):
        sp.register_value('b', sp['a'] + 10)

    assert provider['b'] == 11

def test_call_init_hook_only_once():
    provider = ServiceProvider()

    counter = 0
    def init_hook(_):
        nonlocal counter
        assert counter == 0
        counter += 1
    provider.add_init_hook(init_hook)

    def test_func():
        nonlocal counter
        assert counter == 1
        return counter + 2

    provider.register_transient('a', test_func)

    assert provider['a'] == 3
    assert provider['a'] == 3
    assert provider['a'] == 3
    assert provider['a'] == 3

def test_call_init_hook_when_raises_errors():
    provider = ServiceProvider()

    class Exc(Exception):
        pass

    counter = 0

    def init_hook(_):
        nonlocal counter
        assert counter == 0
        counter += 1
        raise Exc

    provider.add_init_hook(init_hook)

    provider.register_value('a', 0)

    with raises(Exc):
        provider['a']

    with raises(Exc):
        provider['a']

    with raises(Exc):
        provider['a']

    assert counter == 1

def test_resolve_from_naming_convention():
    root_provider = ServiceProvider()
    root_provider.register_value(str, 'dep_content')

    def func1(arg0, dep_str: str):
        return (arg0, dep_str)

    with raises(TypeError):
        root_provider.resolve(func1)

    def func2(ioc, dep_str: str): # convention for ioc
        return (ioc, dep_str)

    assert root_provider.resolve(func2) == (root_provider, 'dep_content')
