# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from anyioc import (
    ServiceProvider
)

from assert_utils import (
    assert_singleton,
    assert_scoped,
    assert_transient
)

def test_singleton_cls():
    provider = ServiceProvider()
    decorator = provider.decorator()

    @decorator.singleton_cls
    class SomeClass:
        pass

    assert provider['SomeClass']
    assert isinstance(provider['SomeClass'], SomeClass)
    assert provider[SomeClass]
    assert isinstance(provider[SomeClass], SomeClass)
    assert assert_singleton(provider, 'SomeClass', SomeClass)

def test_ioc_scoped_cls():
    provider = ServiceProvider()
    decorator = provider.decorator()

    @decorator.scoped_cls
    class SomeClass:
        pass

    assert provider['SomeClass']
    assert isinstance(provider['SomeClass'], SomeClass)
    assert provider[SomeClass]
    assert isinstance(provider[SomeClass], SomeClass)
    assert assert_scoped(provider, 'SomeClass', SomeClass)

def test_ioc_transient_cls():
    provider = ServiceProvider()
    decorator = provider.decorator()

    @decorator.transient_cls
    class SomeClass:
        pass

    assert provider['SomeClass']
    assert isinstance(provider['SomeClass'], SomeClass)
    assert provider[SomeClass]
    assert isinstance(provider[SomeClass], SomeClass)
    assert assert_transient(provider, 'SomeClass', SomeClass)
