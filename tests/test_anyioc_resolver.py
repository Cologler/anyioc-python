# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import types
from typing import Annotated

from pytest import mark, raises

from anyioc import InjectBy, ServiceNotFoundError, ServiceProvider
from anyioc.ioc_resolver import (
    GenericListAsGetManyServiceInfoResolver,
    ImportServiceInfoResolver,
    TypesServiceInfoResolver,
)
from anyioc.symbols import Symbols


@mark.parametrize('use_cache', [False, True], ids=['without-cache', 'with-cache'])
def test_import_resolver(use_cache: bool) -> None:
    provider = ServiceProvider()
    with raises(ServiceNotFoundError):
        _ = provider['anyioc']

    resolver = ImportServiceInfoResolver()
    provider[Symbols.missing_resolver].append(resolver.cache() if use_cache else resolver)

    import anyioc
    assert provider['anyioc'] is anyioc
    assert provider['module::anyioc'] is anyioc

    import sys
    assert provider['sys'] is sys
    assert provider['module::sys'] is sys

    sys.modules.pop('module2', None)
    with raises(ServiceNotFoundError):
        provider['module2']
    assert provider['module::module2'] is not None
    assert provider['module2'] is not None
    module2 = provider['module2']
    assert isinstance(module2, types.ModuleType)

    with raises(ServiceNotFoundError):
        _ = provider['unknown-some-wtf-module']

@mark.parametrize('use_cache', [False, True], ids=['without-cache', 'with-cache'])
def test_type_resolver(use_cache: bool) -> None:
    class CLASS:
        def __init__(self, name: Annotated[str, InjectBy('name')]) -> None:
            self.name = name

    provider = ServiceProvider()
    provider.register_value('name', 'some-name')
    with raises(ServiceNotFoundError):
        _ = provider[CLASS]
    tsir = TypesServiceInfoResolver()
    provider[Symbols.missing_resolver].append(tsir.cache() if use_cache else tsir)

    obj = provider[CLASS]
    assert isinstance(obj, CLASS)
    assert obj.name == 'some-name'
    assert obj is not provider[CLASS]

def test_chain_resolver() -> None:
    class CLASS:
        def __init__(self, name: Annotated[str, InjectBy('name')]) -> None:
            self.name = name

    provider = ServiceProvider()
    provider.register_value('name', 'some-name')
    tsir = TypesServiceInfoResolver()
    provider[Symbols.missing_resolver].append(ImportServiceInfoResolver() + tsir)
    import sys
    assert provider['sys'] is sys

    obj = provider[CLASS]
    assert isinstance(obj, CLASS)
    assert obj.name == 'some-name'

    with raises(ServiceNotFoundError):
        _ = provider['unknown-some-wtf-module']

def test_list_as_getmany_resolver() -> None:
    provider = ServiceProvider()
    provider.register_value(int, 1)
    provider.register_value(int, 2)
    provider.register_value(int, 3)

    def get_ints_list(ints: list[int]) -> list[int]:
        return ints

    with raises(ServiceNotFoundError) as e:
        provider.resolve(get_ints_list)
    assert e.value.resolve_chain == (list[int], )

    provider[Symbols.missing_resolver].append(GenericListAsGetManyServiceInfoResolver(for_list=True, for_tuple=True))

    assert provider.resolve(get_ints_list) == [3, 2, 1]
