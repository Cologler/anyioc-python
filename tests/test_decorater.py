# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from anyioc import (
    ServiceProvider
)
from anyioc.utils import (
    inject_by_anno,
    inject_by_name
)

from assert_utils import (
    assert_singleton,
    assert_scoped,
    assert_transient
)

def test_singleton():
    provider = ServiceProvider()
    decorator = provider.decorator()

    @decorator.singleton
    class SomeClass:
        pass

    assert provider['SomeClass']
    assert isinstance(provider['SomeClass'], SomeClass)
    assert provider[SomeClass]
    assert isinstance(provider[SomeClass], SomeClass)
    assert assert_singleton(provider, 'SomeClass', SomeClass)

def test_ioc_scoped():
    provider = ServiceProvider()
    decorator = provider.decorator()

    @decorator.scoped
    class SomeClass:
        pass

    assert provider['SomeClass']
    assert isinstance(provider['SomeClass'], SomeClass)
    assert provider[SomeClass]
    assert isinstance(provider[SomeClass], SomeClass)
    assert assert_scoped(provider, 'SomeClass', SomeClass)

def test_ioc_transient():
    provider = ServiceProvider()
    decorator = provider.decorator()

    @decorator.transient
    class SomeClass:
        pass

    assert provider['SomeClass']
    assert isinstance(provider['SomeClass'], SomeClass)
    assert provider[SomeClass]
    assert isinstance(provider[SomeClass], SomeClass)
    assert assert_transient(provider, 'SomeClass', SomeClass)

def test_ioc_transient_with_inject_by_anno():
    provider = ServiceProvider()
    decorator = provider.decorator()

    @decorator.transient
    class Name:
        pass

    @decorator.transient(inject_by=inject_by_anno)
    class SomeClass:
        def __init__(self, name: Name):
            self.name = name

    assert isinstance(provider['SomeClass'].name, Name)
