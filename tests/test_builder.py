# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from anyioc import ServiceProvider

from tests.assert_utils import assert_value_singleton, assert_value_scoped, assert_value_transient

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

def test_builder_transient_none_key():
    provider = ServiceProvider()
    @provider.builder.transient(None)
    def func():
        return ServiceProvider()
    assert_value_transient(provider, func)

def test_builder_value():
    provider = ServiceProvider()
    key = provider.builder.value(1, 2)
    assert provider[1] == 2

def test_builder_value_none_key():
    provider = ServiceProvider()
    key = provider.builder.value(None, 2)
    assert provider[key] == 2

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
