# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from pytest import raises

from anyioc import ServiceProvider, ServiceNotFoundError

def test_no_value():
    provider = ServiceProvider()
    with raises(ServiceNotFoundError):
        provider['any']
    assert provider.get('any') is None

def test_parameter():
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

def test_singleton():
    provider = ServiceProvider()
    provider.register_singleton(1, lambda _: ServiceProvider())
    scoped_1 = provider.scope()
    scoped_2 = provider.scope()
    scoped_1_1 = scoped_1.scope()

    assert provider.get(1) is provider.get(1)
    assert provider.get(1) is scoped_1.get(1)
    assert provider.get(1) is scoped_2.get(1)
    assert provider.get(1) is scoped_1_1.get(1)

    assert scoped_1.get(1) is provider.get(1)
    assert scoped_1.get(1) is scoped_1.get(1)
    assert scoped_1.get(1) is scoped_2.get(1)
    assert scoped_1.get(1) is scoped_1_1.get(1)

    assert scoped_2.get(1) is provider.get(1)
    assert scoped_2.get(1) is scoped_1.get(1)
    assert scoped_2.get(1) is scoped_2.get(1)
    assert scoped_2.get(1) is scoped_1_1.get(1)

    assert scoped_1_1.get(1) is provider.get(1)
    assert scoped_1_1.get(1) is scoped_1.get(1)
    assert scoped_1_1.get(1) is scoped_2.get(1)
    assert scoped_1_1.get(1) is scoped_1_1.get(1)

def test_scoped():
    provider = ServiceProvider()
    provider.register_scoped(1, lambda _: ServiceProvider())
    scoped_1 = provider.scope()
    scoped_2 = provider.scope()
    scoped_1_1 = scoped_1.scope()

    assert provider.get(1) is provider.get(1)
    assert provider.get(1) is not scoped_1.get(1)
    assert provider.get(1) is not scoped_2.get(1)
    assert provider.get(1) is not scoped_1_1.get(1)

    assert scoped_1.get(1) is not provider.get(1)
    assert scoped_1.get(1) is scoped_1.get(1)
    assert scoped_1.get(1) is not scoped_2.get(1)
    assert scoped_1.get(1) is not scoped_1_1.get(1)

    assert scoped_2.get(1) is not provider.get(1)
    assert scoped_2.get(1) is not scoped_1.get(1)
    assert scoped_2.get(1) is scoped_2.get(1)
    assert scoped_2.get(1) is not scoped_1_1.get(1)

    assert scoped_1_1.get(1) is not provider.get(1)
    assert scoped_1_1.get(1) is not scoped_1.get(1)
    assert scoped_1_1.get(1) is not scoped_2.get(1)
    assert scoped_1_1.get(1) is scoped_1_1.get(1)

def test_transient():
    provider = ServiceProvider()
    provider.register_transient(1, lambda _: ServiceProvider())
    scoped_1 = provider.scope()
    scoped_2 = provider.scope()
    scoped_1_1 = scoped_1.scope()

    assert provider.get(1) is not provider.get(1)
    assert provider.get(1) is not scoped_1.get(1)
    assert provider.get(1) is not scoped_2.get(1)
    assert provider.get(1) is not scoped_1_1.get(1)

    assert scoped_1.get(1) is not provider.get(1)
    assert scoped_1.get(1) is not scoped_1.get(1)
    assert scoped_1.get(1) is not scoped_2.get(1)
    assert scoped_1.get(1) is not scoped_1_1.get(1)

    assert scoped_2.get(1) is not provider.get(1)
    assert scoped_2.get(1) is not scoped_1.get(1)
    assert scoped_2.get(1) is not scoped_2.get(1)
    assert scoped_2.get(1) is not scoped_1_1.get(1)

    assert scoped_1_1.get(1) is not provider.get(1)
    assert scoped_1_1.get(1) is not scoped_1.get(1)
    assert scoped_1_1.get(1) is not scoped_2.get(1)
    assert scoped_1_1.get(1) is not scoped_1_1.get(1)

def test_symbols_types():
    from anyioc.symbols import Symbols
    from anyioc.ioc import IServiceProvider
    from anyioc.ioc_missing import IMissingResolver

    provider = ServiceProvider()

    assert isinstance(provider[Symbols.provider], IServiceProvider)
    assert isinstance(provider[Symbols.provider_root], IServiceProvider)
    assert isinstance(provider[Symbols.cache], dict)
    assert isinstance(provider[Symbols.missing_resolver], IMissingResolver)

    with provider.scope() as scoped_provider:
        assert isinstance(scoped_provider[Symbols.provider], IServiceProvider)
        assert isinstance(scoped_provider[Symbols.provider_root], IServiceProvider)
        assert isinstance(scoped_provider[Symbols.cache], dict)
        assert isinstance(scoped_provider[Symbols.missing_resolver], IMissingResolver)

def test_symbols_values_ref():
    from anyioc.symbols import Symbols

    provider = ServiceProvider()

    assert provider[Symbols.provider] is provider
    assert provider[Symbols.provider_root] is provider
    assert provider[Symbols.cache] is provider[Symbols.cache]

    with provider.scope() as scoped_provider:
        assert scoped_provider[Symbols.provider] is scoped_provider
        assert scoped_provider[Symbols.provider_root] is provider
        assert scoped_provider[Symbols.cache] is scoped_provider[Symbols.cache]
        assert scoped_provider[Symbols.cache] is not provider[Symbols.cache]
