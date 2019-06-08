# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from anyioc.g import (
    ServiceProvider,
    ioc,
    ioc_singleton_cls, ioc_scoped_cls, ioc_transient_cls,
    get_module_provider, get_namespace_provider
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
    assert ioc[SomeClass_1]
    assert isinstance(ioc[SomeClass_1], SomeClass_1)
    assert assert_singleton(ioc, 'SomeClass_1', SomeClass_1)

def test_ioc_scoped_cls():
    @ioc_scoped_cls()
    class SomeClass_2:
        pass
    assert ioc['SomeClass_2']
    assert isinstance(ioc['SomeClass_2'], SomeClass_2)
    assert ioc[SomeClass_2]
    assert isinstance(ioc[SomeClass_2], SomeClass_2)
    assert assert_scoped(ioc, 'SomeClass_2', SomeClass_2)

def test_ioc_transient_cls():
    @ioc_transient_cls()
    class SomeClass_3:
        pass
    assert ioc['SomeClass_3']
    assert isinstance(ioc['SomeClass_3'], SomeClass_3)
    assert ioc[SomeClass_3]
    assert isinstance(ioc[SomeClass_3], SomeClass_3)
    assert assert_transient(ioc, 'SomeClass_3', SomeClass_3)

def test_get_module_provider():
    assert get_module_provider('A') is not get_module_provider('B')
    assert get_module_provider('A') is get_module_provider('A')
    assert get_module_provider() is get_module_provider(__name__)

    # diff for `get_module_provider` and `get_namespace_provider`
    assert get_module_provider('A.B') is not get_module_provider('A.C')

    assert isinstance(get_module_provider(), ServiceProvider)

def test_get_namespace_provider():
    assert get_namespace_provider('A') is not get_namespace_provider('B')
    assert get_namespace_provider('A') is get_namespace_provider('A')
    assert get_namespace_provider() is get_namespace_provider(__name__)

    # diff for `get_module_provider` and `get_namespace_provider`
    assert get_namespace_provider('A.B.C') is get_namespace_provider('A.C.E')

    assert get_namespace_provider('A.B.C') is get_module_provider('A')

    assert isinstance(get_namespace_provider(), ServiceProvider)
