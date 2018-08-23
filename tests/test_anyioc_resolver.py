# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from pytest import raises

from anyioc import ServiceProvider, ServiceNotFoundError
from anyioc.symbols import Symbols
from anyioc.ioc_resolver import (
    ImportServiceInfoResolver,
    TypesServiceInfoResolver,
)

def test_import_resolver():
    provider = ServiceProvider()
    with raises(ServiceNotFoundError):
        _ = provider['anyioc']
    provider.register_value(Symbols.missing_resolver, ImportServiceInfoResolver())
    import anyioc
    assert provider['anyioc'] is anyioc
    import sys
    assert provider['sys'] is sys
    with raises(ServiceNotFoundError):
        _ = provider['unknown-some-wtf-module']

def test_import_resolver_with_cache():
    provider = ServiceProvider()
    with raises(ServiceNotFoundError):
        _ = provider['anyioc']
    provider.register_value(Symbols.missing_resolver, ImportServiceInfoResolver().cache())
    import anyioc
    assert provider['anyioc'] is anyioc
    import sys
    assert provider['sys'] is sys
    with raises(ServiceNotFoundError):
        _ = provider['unknown-some-wtf-module']

def test_type_resolver():
    class CLASS:
        def __init__(self, name):
            self.name = name

    provider = ServiceProvider()
    provider.register_value('name', 'some-name')
    with raises(ServiceNotFoundError):
        _ = provider[CLASS]
    provider.register_value(Symbols.missing_resolver, TypesServiceInfoResolver().cache())
    assert provider[CLASS].name == 'some-name'
    assert provider[CLASS] is not provider[CLASS]

def test_type_resolver_with_cache():
    class CLASS:
        def __init__(self, name):
            self.name = name

    provider = ServiceProvider()
    provider.register_value('name', 'some-name')
    with raises(ServiceNotFoundError):
        _ = provider[CLASS]
    provider.register_value(Symbols.missing_resolver, TypesServiceInfoResolver())
    assert provider[CLASS].name == 'some-name'
    assert provider[CLASS] is not provider[CLASS]

def test_chain_resolver():
    class CLASS:
        def __init__(self, name):
            self.name = name

    provider = ServiceProvider()
    provider.register_value('name', 'some-name')
    provider.register_value(Symbols.missing_resolver, ImportServiceInfoResolver() + TypesServiceInfoResolver())
    import sys
    assert provider['sys'] is sys
    assert provider[CLASS].name == 'some-name'
    with raises(ServiceNotFoundError):
        _ = provider['unknown-some-wtf-module']
