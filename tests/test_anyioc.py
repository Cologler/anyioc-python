# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import itertools

from pytest import raises

from anyioc import ServiceProvider, ServiceNotFoundError

def test_no_value():
    provider = ServiceProvider()
    with raises(ServiceNotFoundError):
        provider['any']
    assert provider.get('any') is None

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

def test_argument_ioc_at_root():
    root_provider = ServiceProvider()
    with root_provider.scope() as scoped_provider:
        def singleton_func(ioc):
            assert ioc is root_provider
            return 'singleton'
        def scoped_func(ioc):
            assert ioc is scoped_provider
            return 'scoped'
        def transient_func(ioc):
            assert ioc is scoped_provider
            return 'transient'
        root_provider.register_singleton(1, singleton_func)
        root_provider.register_scoped(2, scoped_func)
        root_provider.register_transient(3, transient_func)

        assert scoped_provider[1] == 'singleton'
        assert scoped_provider[2] == 'scoped'
        assert scoped_provider[3] == 'transient'

def test_argument_ioc_at_scoped():
    root_provider = ServiceProvider()
    with root_provider.scope() as scoped_provider:
        def singleton_func(ioc):
            # when you register in scoped_provider,
            # value should singleton base on scoped_provider.
            assert ioc is scoped_provider
            return 'singleton'
        def scoped_func(ioc):
            assert ioc is scoped_provider
            return 'scoped'
        def transient_func(ioc):
            assert ioc is scoped_provider
            return 'transient'
        scoped_provider.register_singleton(1, singleton_func)
        scoped_provider.register_scoped(2, scoped_func)
        scoped_provider.register_transient(3, transient_func)

        assert scoped_provider[1] == 'singleton'
        assert scoped_provider[2] == 'scoped'
        assert scoped_provider[3] == 'transient'

def test_symbols_types():
    from anyioc.symbols import Symbols
    from anyioc.ioc import IServiceProvider
    from anyioc.ioc_resolver import IServiceInfoResolver

    provider = ServiceProvider()

    assert isinstance(provider[Symbols.provider], IServiceProvider)
    assert isinstance(provider[Symbols.provider_root], IServiceProvider)
    assert isinstance(provider[Symbols.cache], dict)
    assert isinstance(provider[Symbols.missing_resolver], IServiceInfoResolver)

    with provider.scope() as scoped_provider:
        assert isinstance(scoped_provider[Symbols.provider], IServiceProvider)
        assert isinstance(scoped_provider[Symbols.provider_root], IServiceProvider)
        assert isinstance(scoped_provider[Symbols.cache], dict)
        assert isinstance(scoped_provider[Symbols.missing_resolver], IServiceInfoResolver)

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

def test_error_message():
    provider = ServiceProvider()
    provider.register_transient('a', lambda ioc: ioc['b'])
    provider.register_transient('b', lambda ioc: ioc['c'])
    provider.register_transient('c', lambda ioc: ioc['d'])

    with raises(ServiceNotFoundError, match="unknown service: 'd'; resolve chain: 'a'->'b'->'c'->'d'"):
        provider['a']

def test_get_many():
    provider = ServiceProvider()
    provider.register_transient('a', lambda ioc: 1)
    provider.register_transient('a', lambda ioc: 2)
    provider.register_transient('a', lambda ioc: 3)

    assert [3, 2, 1] == provider.get_many('a')

def test_get_many_from_empty():
    provider = ServiceProvider()
    assert [] == provider.get_many('a') # wont raise error

def test_get_many_from_multilevel():
    provider = ServiceProvider()
    provider.register_transient('a', lambda ioc: 10)
    provider.register_transient('a', lambda ioc: 11)

    provider2 = provider.scope()
    provider2.register_transient('a', lambda ioc: 20)
    provider2.register_transient('a', lambda ioc: 21)

    provider3 = provider2.scope()
    provider3.register_transient('a', lambda ioc: 30)
    provider3.register_transient('a', lambda ioc: 31)

    provider4 = provider3.scope()
    provider4.register_transient('a', lambda ioc: 40)
    provider4.register_transient('a', lambda ioc: 41)

    assert [31, 30, 21, 20, 11, 10] == provider3.get_many('a')

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
