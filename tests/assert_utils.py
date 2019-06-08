# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import itertools

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

def assert_value_singleton(provider: ServiceProvider, key):
    scoped_1 = provider.scope()
    scoped_2 = provider.scope()
    scoped_1_1 = scoped_1.scope()

    for l, r in itertools.combinations_with_replacement([provider, scoped_1, scoped_2, scoped_1_1], 2):
        assert l.get(key) is r.get(key)

def assert_value_scoped(provider: ServiceProvider, key):
    scoped_1 = provider.scope()
    scoped_2 = provider.scope()
    scoped_1_1 = scoped_1.scope()

    for l, r in itertools.combinations_with_replacement([provider, scoped_1, scoped_2, scoped_1_1], 2):
        if l is r:
            assert l.get(key) is r.get(key)
        else:
            assert l.get(key) is not r.get(key)

def assert_value_transient(provider: ServiceProvider, key):
    scoped_1 = provider.scope()
    scoped_2 = provider.scope()
    scoped_1_1 = scoped_1.scope()

    for l, r in itertools.combinations_with_replacement([provider, scoped_1, scoped_2, scoped_1_1], 2):
        assert l.get(key) is not r.get(key)
