# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

import inspect
from typing import Annotated

from anyioc import LifeTime, ServiceProvider
from anyioc.annotations import InjectBy, InjectByGroup, InjectWithValue


def test_inject_class_by_annotated_injectby():
    key = 'the_int_key'
    val = 444

    class A:
        def __init__(self, x: Annotated[int, InjectBy(key)]) -> None:
            self.val = x

    sp = ServiceProvider()
    sp.register_value(key, val)

    assert sp.resolve(A).val == val

def test_inject_class_by_annotated_injectby_with_default():
    key = 'the_int_key'
    val = 444

    class A:
        def __init__(self, x: Annotated[int, InjectBy(key, val)]) -> None:
            self.val = x

    sp = ServiceProvider()
    assert sp.resolve(A).val == val

def test_inject_func_by_annotated_injectby():
    key = 'the_int_key'
    val = 444

    def func(x: Annotated[int, InjectBy(key)]):
        return x

    sp = ServiceProvider()
    sp.register_value(key, val)

    assert sp.resolve(func) == val

def test_inject_func_by_annotated_injectby_with_lifetime():
    key = 'the_key'

    def get_transient(x: Annotated[object, InjectBy(key, lifetime=LifeTime.transient)]):
        return x

    def get_scoped(x: Annotated[object, InjectBy(key, lifetime=LifeTime.scoped)]):
        return x

    sp = ServiceProvider()
    sp.register_transient(key, lambda: object())

    assert sp.resolve(get_transient) is not sp.resolve(get_transient)
    assert sp.resolve(get_scoped) is sp.resolve(get_scoped)

def test_inject_func_by_annotated_injectby_with_default():
    key = 'the_int_key'
    val = 444

    def func(x: Annotated[int, InjectBy(key, val)]):
        return x

    sp = ServiceProvider()
    sp.register_singleton(func, func)

    assert sp.resolve(func) == val

def test_inject_func_by_annotated_injectbygroup():
    sv = 'ffw'
    iv = 46656

    def func(x: Annotated[tuple[str, int], InjectByGroup(str, int)]):
        return x

    sp = ServiceProvider()
    sp.register_value(str, sv)
    sp.register_value(int, iv)
    assert sp.resolve(func) == (sv, iv)

def test_inject_func_by_annotated_injectwithvalue():
    def func(inject_from_ioc: Annotated[int, InjectWithValue(1)] = 0):
        return inject_from_ioc

    sp = ServiceProvider()
    sp.register_value(int, 2)
    assert func() == 0
    assert sp.resolve(func) == 1

def test_inject_class_by_typed():
    val = 444

    class A:
        def __init__(self, x: int) -> None:
            self.val = x

    sp = ServiceProvider()
    sp.register_value(int, val)
    assert sp.resolve(A).val == val

def test_inject_class_by_typed_with_default():
    val = 444

    class A:
        def __init__(self, x: int = val) -> None:
            self.val = x

    sp = ServiceProvider()
    assert sp.resolve(A).val == val

def test_inject_types_for_service_provider():
    def get_value(val: ServiceProvider):
        return val

    sp = ServiceProvider()
    assert sp.resolve(get_value) is sp

def test_inject_types_for_frameinfo():
    def get_value(val: inspect.FrameInfo):
        return val

    sp = ServiceProvider()

    fr = sp.resolve(get_value)
    assert isinstance(fr, inspect.FrameInfo)
    mo = inspect.getmodule(fr.frame)
    assert mo is not None
    assert mo.__name__ == 'test_annotations'
