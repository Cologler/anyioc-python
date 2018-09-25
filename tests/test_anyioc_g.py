# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from anyioc.g import (
    ioc,
    ioc_singleton, ioc_scoped, ioc_transient,
    ioc_singleton_cls, ioc_scoped_cls, ioc_transient_cls,
    ioc_bind
)

from assert_utils import (
    assert_singleton,
    assert_scoped,
    assert_transient
)

def test_ioc_singleton_cls():
    @ioc_singleton_cls()
    class SomeClass_1:
        pass
    assert ioc['SomeClass_1']
    assert isinstance(ioc['SomeClass_1'], SomeClass_1)
    assert_singleton(ioc, 'SomeClass_1')

def test_ioc_scoped_cls():
    @ioc_scoped_cls()
    class SomeClass_2:
        pass
    assert ioc['SomeClass_2']
    assert isinstance(ioc['SomeClass_2'], SomeClass_2)
    assert_scoped(ioc, 'SomeClass_2')

def test_ioc_transient_cls():
    @ioc_transient_cls()
    class SomeClass_3:
        pass
    assert ioc['SomeClass_3']
    assert isinstance(ioc['SomeClass_3'], SomeClass_3)
    assert assert_transient(ioc, 'SomeClass_3')
