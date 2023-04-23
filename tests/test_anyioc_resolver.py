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
from anyioc.utils import inject_by_name

def test_import_resolver():
    provider = ServiceProvider()
    with raises(ServiceNotFoundError):
        _ = provider['anyioc']
    provider[Symbols.missing_resolver].append(ImportServiceInfoResolver())
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
    provider[Symbols.missing_resolver].append(ImportServiceInfoResolver().cache())
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
    tsir = TypesServiceInfoResolver()
    tsir.inject_by = inject_by_name
    provider[Symbols.missing_resolver].append(tsir.cache())
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
    tsir = TypesServiceInfoResolver()
    tsir.inject_by = inject_by_name
    provider[Symbols.missing_resolver].append(tsir)
    assert provider[CLASS].name == 'some-name'
    assert provider[CLASS] is not provider[CLASS]

def test_chain_resolver():
    class CLASS:
        def __init__(self, name):
            self.name = name

    provider = ServiceProvider()
    provider.register_value('name', 'some-name')
    tsir = TypesServiceInfoResolver()
    tsir.inject_by = inject_by_name
    provider[Symbols.missing_resolver].append(ImportServiceInfoResolver() + tsir)
    import sys
    assert provider['sys'] is sys
    assert provider[CLASS].name == 'some-name'
    with raises(ServiceNotFoundError):
        _ = provider['unknown-some-wtf-module']

def test_():
    from anyioc.ioc_resolver import TypingServiceInfoResolver
    from typing import Tuple

    class TestClass:
        pass

    provider = ServiceProvider()
    provider.register_transient(TestClass, TestClass)
    provider.register_value(int, 15)
    provider[Symbols.missing_resolver].append(TypingServiceInfoResolver())

    ret = provider[Tuple[TestClass, int]]
    assert isinstance(ret, tuple)
    assert isinstance(ret[0], TestClass)
    assert ret[1] == 15
