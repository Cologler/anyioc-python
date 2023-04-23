# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import itertools

from anyioc import ServiceProvider

def assert_value_singleton(provider: ServiceProvider, key):
    scoped_1 = provider.scope()
    scoped_2 = provider.scope()
    scoped_1_1 = scoped_1.scope()

    for left, right in itertools.combinations_with_replacement([provider, scoped_1, scoped_2, scoped_1_1], 2):
        assert left.get(key) is right.get(key)

def assert_value_scoped(provider: ServiceProvider, key):
    scoped_1 = provider.scope()
    scoped_2 = provider.scope()
    scoped_1_1 = scoped_1.scope()

    for left, right in itertools.combinations_with_replacement([provider, scoped_1, scoped_2, scoped_1_1], 2):
        if left is right:
            assert left.get(key) is right.get(key)
        else:
            assert left.get(key) is not right.get(key)

def assert_value_transient(provider: ServiceProvider, key):
    scoped_1 = provider.scope()
    scoped_2 = provider.scope()
    scoped_1_1 = scoped_1.scope()

    for left, right in itertools.combinations_with_replacement([provider, scoped_1, scoped_2, scoped_1_1], 2):
        assert left.get(key) is not right.get(key)
