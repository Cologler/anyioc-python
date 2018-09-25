# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from anyioc import ServiceProvider

def assert_singleton(ioc: ServiceProvider, key):
    assert ioc[key] is ioc[key]
    with ioc.scope() as scoped:
        assert scoped[key] is ioc[key]
    return True

def assert_scoped(ioc: ServiceProvider, key):
    assert ioc[key] is ioc[key]
    with ioc.scope() as scoped:
        assert scoped[key] is not ioc[key]
    return True

def assert_transient(ioc: ServiceProvider, key):
    assert ioc[key] is not ioc[key]
    with ioc.scope() as scoped:
        assert scoped[key] is not ioc[key]
    return True
