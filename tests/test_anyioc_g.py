# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from anyioc.g import (
    ServiceProvider,
    ioc,
    get_module_provider, get_namespace_provider
)
from anyioc.symbols import Symbols

from tests.assert_utils import (
    assert_value_singleton,
    assert_value_scoped,
    assert_value_transient
)

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

def test_scoped_provider_is_provider_root():
    provider = get_namespace_provider('a.b')
    assert provider[Symbols.provider_root] is provider
