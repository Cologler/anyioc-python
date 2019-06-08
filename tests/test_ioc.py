# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from anyioc import ServiceProvider

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
