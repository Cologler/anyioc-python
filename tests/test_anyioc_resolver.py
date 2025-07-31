# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import types
from typing import Annotated

from pytest import raises

from anyioc import InjectBy, ServiceNotFoundError, ServiceProvider
from anyioc.ioc_resolver import (
    ImportServiceInfoResolver,
    TypesServiceInfoResolver,
)
from anyioc.symbols import Symbols


def test_import_resolver():
    provider = ServiceProvider()
    with raises(ServiceNotFoundError):
        _ = provider['anyioc']

    provider[Symbols.missing_resolver].append(ImportServiceInfoResolver())

    import anyioc
    assert provider['anyioc'] is anyioc
    assert provider['module::anyioc'] is anyioc

    import sys
    assert provider['sys'] is sys
    assert provider['module::sys'] is sys

    with raises(ServiceNotFoundError):
        provider['module2']
    assert provider['module::module2'] is not None
    assert provider['module2'] is not None
    module2 = provider['module2']
    assert isinstance(module2, types.ModuleType)

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
        def __init__(self, name: Annotated[str, InjectBy('name')]):
            self.name = name

    provider = ServiceProvider()
    provider.register_value('name', 'some-name')
    with raises(ServiceNotFoundError):
        _ = provider[CLASS]
    tsir = TypesServiceInfoResolver()
    provider[Symbols.missing_resolver].append(tsir.cache())
    assert provider[CLASS].name == 'some-name'
    assert provider[CLASS] is not provider[CLASS]

def test_type_resolver_with_cache():
    class CLASS:
        def __init__(self, name: Annotated[str, InjectBy('name')]):
            self.name = name

    provider = ServiceProvider()
    provider.register_value('name', 'some-name')
    with raises(ServiceNotFoundError):
        _ = provider[CLASS]
    tsir = TypesServiceInfoResolver()
    provider[Symbols.missing_resolver].append(tsir)
    assert provider[CLASS].name == 'some-name'
    assert provider[CLASS] is not provider[CLASS]

def test_chain_resolver():
    class CLASS:
        def __init__(self, name: Annotated[str, InjectBy('name')]):
            self.name = name

    provider = ServiceProvider()
    provider.register_value('name', 'some-name')
    tsir = TypesServiceInfoResolver()
    provider[Symbols.missing_resolver].append(ImportServiceInfoResolver() + tsir)
    import sys
    assert provider['sys'] is sys
    assert provider[CLASS].name == 'some-name'
    with raises(ServiceNotFoundError):
        _ = provider['unknown-some-wtf-module']
