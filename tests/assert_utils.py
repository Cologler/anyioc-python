# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from anyioc import ServiceProvider

def assert_singleton(ioc: ServiceProvider, key, *other_keys):
    root_value = ioc[key]
    assert ioc[key] is root_value
    for alias in other_keys:
        assert ioc[alias] is root_value
    with ioc.scope() as scoped:
        scoped_value = scoped[key]
        assert scoped_value is root_value
        for alias in other_keys:
            assert scoped[alias] is root_value
    return True

def assert_scoped(ioc: ServiceProvider, key, *other_keys):
    root_value = ioc[key]
    assert ioc[key] is root_value
    for alias in other_keys:
        assert ioc[alias] is root_value
    with ioc.scope() as scoped:
        scoped_value = scoped[key]
        assert scoped_value is not root_value
        for alias in other_keys:
            assert scoped[alias] is scoped_value
            assert scoped[alias] is not root_value
    return True

def assert_transient(ioc: ServiceProvider, key, *other_keys):
    assert ioc[key] is not ioc[key]
    with ioc.scope() as scoped:
        assert scoped[key] is not ioc[key]
    return True
