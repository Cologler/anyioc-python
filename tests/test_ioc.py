# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from anyioc import ServiceProvider
from anyioc.symbols import Symbols

from tests.assert_utils import assert_value_singleton, assert_value_scoped, assert_value_transient

def test_singleton():
    provider = ServiceProvider()
    provider.register_singleton(1, lambda: ServiceProvider())
    assert_value_singleton(provider, 1)

def test_scoped():
    provider = ServiceProvider()
    provider.register_scoped(1, lambda: ServiceProvider())
    assert_value_scoped(provider, 1)

def test_transient():
    provider = ServiceProvider()
    provider.register_transient(1, lambda: ServiceProvider())
    assert_value_transient(provider, 1)

def test_resolve_group():
    provider = ServiceProvider()
    provider.register_transient('str', lambda: 'name')
    provider.register_transient('int', lambda: 1)
    provider.register_value('float', 1.1)
    group_keys = ['str', 'int']
    provider.register_group('any', group_keys)
    assert provider['any'] == ('name', 1)
    # always transient:
    assert provider['any'] is not provider['any']
    # allow to add later
    group_keys.append('float')
    assert provider['any'] == ('name', 1, 1.1)

def test_resolve_group_then_from_group_src_symbol():
    provider = ServiceProvider()
    src = []
    provider.register_group('group', src)
    assert src is provider[Symbols.get_symbol_for_group_src('group')]

def test_resolve_value():
    provider = ServiceProvider()
    provider.register_value('k', 'value')
    assert provider['k'] == 'value'

def test_register_bind():
    provider = ServiceProvider()
    provider.register_value('k', 'value')
    provider.register_bind('b', 'k')
    assert provider['b'] == 'value'
