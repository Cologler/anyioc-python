# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from anyioc import ServiceProvider

from tests.assert_utils import assert_value_singleton, assert_value_scoped, assert_value_transient

def test_builder_register_key_canbe_none():
    provider = ServiceProvider()
    @provider.builder.singleton(None)
    def func():
        return 1
    assert provider[func] == 1

def test_builder_register_key_canbe_a_list():
    provider = ServiceProvider()
    @provider.builder.singleton(key=[1, 2])
    def func():
        return 3
    assert provider[1] == 3
    assert provider[2] == 3

def test_builder_register_return_none():
    provider = ServiceProvider()
    assert provider.builder.singleton(1, lambda: 0) is None

def test_builder_register_as_decorator_return_factory():
    provider = ServiceProvider()
    @provider.builder.singleton(1)
    def func():
        pass
    assert func is not None and func.__name__ == 'func'

def test_builder_singleton_as_decorator():
    provider = ServiceProvider()
    @provider.builder.singleton(1)
    def func():
        return ServiceProvider()
    assert_value_singleton(provider, 1)

def test_builder_scoped_as_decorator():
    provider = ServiceProvider()
    @provider.builder.scoped(1)
    def func():
        return ServiceProvider()
    assert_value_scoped(provider, 1)

def test_builder_transient_as_decorator():
    provider = ServiceProvider()
    @provider.builder.transient(1)
    def func():
        return ServiceProvider()
    assert_value_transient(provider, 1)

def test_builder_value():
    provider = ServiceProvider()
    key = provider.builder.value(1, 2)
    assert provider[1] == 2

def test_builder_value_none_key():
    # since none key cannot get, we need to use group
    provider = ServiceProvider()
    builder = provider.builder
    @builder.value(None)
    class A:
        pass
    key = builder.last_added_key
    assert isinstance(A, type)
    assert provider[key] is A

def test_builder_group():
    provider = ServiceProvider()
    group = provider.builder.group()
    group.value(None, 2)
    assert provider[group] == (2, )

def test_builder_group_with_group_key():
    provider = ServiceProvider()
    group = provider.builder.group('gk')
    group.value(None, 2)
    assert provider[group] == (2, )
    assert provider['gk'] == (2, )

def test_builder_group_as_decorator():
    provider = ServiceProvider()
    group = provider.builder.group()
    @group.singleton()
    class A:
        pass
    instance, = provider[group]
    assert isinstance(instance, A)

def test_builder_multi_level_group():
    provider = ServiceProvider()
    root_group = provider.builder.group()
    sub_group = root_group.group()
    sub_group.value(None, 2)
    assert provider[root_group] == ((2, ), )

def test_builder_group_with_group_key_then_from_group_src_symbol():
    from anyioc.symbols import Symbols
    provider = ServiceProvider()
    group = provider.builder.group('gk')
    assert group is provider[Symbols.get_symbol_for_group_src('gk')]
