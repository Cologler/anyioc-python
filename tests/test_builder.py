# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import pytest

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
    @provider.builder.singleton([1, 2])
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

def test_builder_register_inject_by_can_be_str_name():
    provider = ServiceProvider()
    provider.register_value('f1', 1)
    provider.register_value('f2', 2)
    @provider.builder.transient('wtf', inject_by='name')
    def func(f1, f2):
        return f1 + f2
    assert 3 == provider['wtf']

def test_builder_register_inject_by_can_be_str_anno():
    provider = ServiceProvider()
    provider.register_value(int, 10)
    provider.register_value(str, '2')
    @provider.builder.transient('wtf', inject_by='anno')
    def func(f1: int, f2: str):
        return f'{f1}{f2}'
    assert '102' == provider['wtf']

def test_builder_register_inject_by_cannot_be_other_strs():
    provider = ServiceProvider()
    with pytest.raises(ValueError, match='dsds is not one of known `inject by` action.'):
        provider.builder.transient('wtf', inject_by='dsds')

def test_builder_value():
    provider = ServiceProvider()
    @provider.builder.value('type:A')
    class A:
        pass
    assert provider['type:A'] == A
    assert isinstance(A, type)

def test_builder_group_with_keys():
    provider = ServiceProvider()
    group = provider.builder.group('gk')
    group.value(object())(2)
    group.value(object())(4)
    group.value(object())(6)
    assert provider[group] == (2, 4, 6)
    assert provider['gk'] == (2, 4, 6)

def test_builder_group_with_no_keys():
    provider = ServiceProvider()
    group = provider.builder.group()
    group.value(object())(2)
    group.value(object())(4)
    group.value(object())(6)
    assert provider[group] == (2, 4, 6)

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
    sub_group.value(None)(2)
    assert provider[root_group] == ((2, ), )
