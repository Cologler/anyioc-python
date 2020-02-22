# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from pytest import raises

from anyioc.ioc import ServiceProvider, ServiceNotFoundError
from anyioc.utils import (
    inject_by_name, inject_by_anno, inject_by_keys,
    make_group
)

def test_inject_by_name():
    class SomeClass:
        def __init__(self, name_1, name_2):
            self.value = (name_1, name_2)

    provider = ServiceProvider()
    provider.register_transient('name_1', lambda _: 15)
    provider.register_transient('name_2', lambda _: 18)
    provider.register_transient('some_class', inject_by_name(SomeClass))
    instance = provider.get('some_class')
    assert instance.value == (15, 18)

def test_inject_by_name_with_error():
    class SomeClass:
        def __init__(self, name):
            pass

    provider = ServiceProvider()
    provider.register_transient('some_class', inject_by_name(SomeClass))
    with raises(ServiceNotFoundError):
        _ = provider['some_class']
    with raises(ServiceNotFoundError):
        _ = provider.get('some_class')

def test_inject_by_anno():
    class SomeClass:
        def __init__(self, name_1: str, name_2: int):
            self.value = (name_1, name_2)

    provider = ServiceProvider()
    provider.register_value(str, 'sd')
    provider.register_value(int, 18)
    provider.register_transient('some_class', inject_by_anno(SomeClass))
    instance = provider.get('some_class')
    assert instance.value == ('sd', 18)

def test_inject_by_anno_with_default():
    class SomeClass:
        def __init__(self, name: int = 3):
            self.value = name

    provider = ServiceProvider()
    provider.register_transient('some_class', inject_by_anno(SomeClass))
    instance = provider.get('some_class')
    assert instance.value == 3

def test_inject_by_anno_without_anno():
    class SomeClass:
        def __init__(self, name):
            self.value = name

    with raises(ValueError):
        inject_by_anno(SomeClass)

def test_inject_by_anno_with_default_without_anno():
    class SomeClass:
        def __init__(self, name=3):
            self.value = name

    provider = ServiceProvider()
    provider.register_transient('some_class', inject_by_anno(SomeClass))
    instance = provider.get('some_class')
    assert instance.value == 3

def test_inject_by_anno_without_anno_with_use_name_if_empty():
    @inject_by_anno(use_name_if_empty=True)
    class SomeClass:
        def __init__(self, name):
            self.value = name

    provider = ServiceProvider()
    provider.register_value('name', 'abc')
    provider.register_transient('some_class', SomeClass)
    instance = provider.get('some_class')
    assert instance.value == 'abc'

def test_inject_by_keys():
    class SomeClass:
        def __init__(self, first, second):
            self.value = (first, second)

    provider = ServiceProvider()
    provider.register_transient('val1', lambda : 100)
    provider.register_transient('val2', lambda : 200)
    provider.register_transient('some_class', inject_by_keys(first='val1', second='val2')(SomeClass))
    instance = provider.get('some_class')
    assert instance.value == (100, 200)

def test_make_group():
    provider = ServiceProvider()
    group = make_group(provider, 'gk')
    group('some_group_key')
    provider.register_value('some_group_key', 2)
    assert provider['gk'] == (2, )

def test_make_group_without_group_key():
    provider = ServiceProvider()
    group = make_group(provider)
    group('some_group_key')
    provider.register_value('some_group_key', 2)
    assert provider[group] == (2, )

def test_helper_get_logger():
    from anyioc.utils import get_logger

    provider = ServiceProvider()
    provider.register_transient('logger', get_logger)
    logger = provider['logger']
    assert logger.name == __name__
    assert logger.name == 'test_utils'
