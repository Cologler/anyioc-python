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
