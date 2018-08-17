# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from pytest import raises

from anyioc import ServiceProvider

def test_parameter():
    provider = ServiceProvider()
    # 0 args
    provider.register_singleton(1, lambda: 101)
    # 1 args
    provider.register_singleton(2, lambda x: 102)
    # 2 args
    with raises(TypeError):
        provider.register_singleton(3, lambda x, y: 103)

def test_singleton():
    provider = ServiceProvider()
    provider.register_singleton(1, lambda _: ServiceProvider())
    scoped_1 = provider.scope()
    scoped_2 = provider.scope()
    scoped_1_1 = scoped_1.scope()

    assert provider.get(1) is provider.get(1)
    assert provider.get(1) is scoped_1.get(1)
    assert provider.get(1) is scoped_2.get(1)
    assert provider.get(1) is scoped_1_1.get(1)

    assert scoped_1.get(1) is provider.get(1)
    assert scoped_1.get(1) is scoped_1.get(1)
    assert scoped_1.get(1) is scoped_2.get(1)
    assert scoped_1.get(1) is scoped_1_1.get(1)

    assert scoped_2.get(1) is provider.get(1)
    assert scoped_2.get(1) is scoped_1.get(1)
    assert scoped_2.get(1) is scoped_2.get(1)
    assert scoped_2.get(1) is scoped_1_1.get(1)

    assert scoped_1_1.get(1) is provider.get(1)
    assert scoped_1_1.get(1) is scoped_1.get(1)
    assert scoped_1_1.get(1) is scoped_2.get(1)
    assert scoped_1_1.get(1) is scoped_1_1.get(1)

def test_scoped():
    provider = ServiceProvider()
    provider.register_scoped(1, lambda _: ServiceProvider())
    scoped_1 = provider.scope()
    scoped_2 = provider.scope()
    scoped_1_1 = scoped_1.scope()

    assert provider.get(1) is provider.get(1)
    assert provider.get(1) is not scoped_1.get(1)
    assert provider.get(1) is not scoped_2.get(1)
    assert provider.get(1) is not scoped_1_1.get(1)

    assert scoped_1.get(1) is not provider.get(1)
    assert scoped_1.get(1) is scoped_1.get(1)
    assert scoped_1.get(1) is not scoped_2.get(1)
    assert scoped_1.get(1) is not scoped_1_1.get(1)

    assert scoped_2.get(1) is not provider.get(1)
    assert scoped_2.get(1) is not scoped_1.get(1)
    assert scoped_2.get(1) is scoped_2.get(1)
    assert scoped_2.get(1) is not scoped_1_1.get(1)

    assert scoped_1_1.get(1) is not provider.get(1)
    assert scoped_1_1.get(1) is not scoped_1.get(1)
    assert scoped_1_1.get(1) is not scoped_2.get(1)
    assert scoped_1_1.get(1) is scoped_1_1.get(1)

def test_transient():
    provider = ServiceProvider()
    provider.register_transient(1, lambda _: ServiceProvider())
    scoped_1 = provider.scope()
    scoped_2 = provider.scope()
    scoped_1_1 = scoped_1.scope()

    assert provider.get(1) is not provider.get(1)
    assert provider.get(1) is not scoped_1.get(1)
    assert provider.get(1) is not scoped_2.get(1)
    assert provider.get(1) is not scoped_1_1.get(1)

    assert scoped_1.get(1) is not provider.get(1)
    assert scoped_1.get(1) is not scoped_1.get(1)
    assert scoped_1.get(1) is not scoped_2.get(1)
    assert scoped_1.get(1) is not scoped_1_1.get(1)

    assert scoped_2.get(1) is not provider.get(1)
    assert scoped_2.get(1) is not scoped_1.get(1)
    assert scoped_2.get(1) is not scoped_2.get(1)
    assert scoped_2.get(1) is not scoped_1_1.get(1)

    assert scoped_1_1.get(1) is not provider.get(1)
    assert scoped_1_1.get(1) is not scoped_1.get(1)
    assert scoped_1_1.get(1) is not scoped_2.get(1)
    assert scoped_1_1.get(1) is not scoped_1_1.get(1)
