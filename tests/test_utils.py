# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from anyioc.ioc import ServiceProvider
from anyioc.utils import auto_inject

def test_auto_inject():
    class SomeClass:
        def __init__(self, name_1, name_2):
            self.value = (name_1, name_2)

    provider = ServiceProvider()
    provider.register_transient('name_1', lambda _: 15)
    provider.register_transient('name_2', lambda _: 18)
    provider.register_transient('some_class', auto_inject(SomeClass))
    instance = provider.get('some_class')
    assert instance.value == (15, 18)
