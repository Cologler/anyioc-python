# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from typing import Annotated
import inspect

from anyioc import ServiceProvider
from anyioc.annotations import InjectBy


def test_inject_class_by_annotated_injectby():
    key = 'the_int_key'
    val = 444

    class A:
        def __init__(self, x: Annotated[int, InjectBy(key)]) -> None:
            self.val = x

    sp = ServiceProvider()
    sp.register_value(key, val)
    sp.register_singleton(A, A)

    a: A = sp[A]
    assert a.val == val

def test_inject_class_by_annotated_injectby_with_default():
    key = 'the_int_key'
    val = 444

    class A:
        def __init__(self, x: Annotated[int, InjectBy(key, val)]) -> None:
            self.val = x

    sp = ServiceProvider()
    sp.register_singleton(A, A)

    a: A = sp[A]
    assert a.val == val

def test_inject_func_by_annotated_injectby():
    key = 'the_int_key'
    val = 444

    def func(x: Annotated[int, InjectBy(key)]):
        return x

    sp = ServiceProvider()
    sp.register_value(key, val)
    sp.register_singleton(func, func)

    assert sp[func] == val

def test_inject_func_by_annotated_injectby_with_default():
    key = 'the_int_key'
    val = 444

    def func(x: Annotated[int, InjectBy(key, val)]):
        return x

    sp = ServiceProvider()
    sp.register_singleton(func, func)

    assert sp[func] == val

def test_inject_class_by_typed():
    val = 444

    class A:
        def __init__(self, x: int) -> None:
            self.val = x

    sp = ServiceProvider()
    sp.register_value(int, val)
    sp.register_singleton(A, A)

    a: A = sp[A]
    assert a.val == val

def test_inject_class_by_typed_with_default():
    val = 444

    class A:
        def __init__(self, x: int = val) -> None:
            self.val = x

    sp = ServiceProvider()
    sp.register_singleton(A, A)

    a: A = sp[A]
    assert a.val == val

def test_inject_types_for_service_provider():
    def get_value(val: ServiceProvider):
        return val

    sp = ServiceProvider()
    sp.register_singleton(get_value, get_value)

    val = sp.get(get_value)
    assert isinstance(val, ServiceProvider)

def test_inject_types_for_frameinfo():
    def get_value(val: inspect.FrameInfo):
        return val

    sp = ServiceProvider()
    sp.register_singleton(get_value, get_value)

    fr = sp.get(get_value)
    assert isinstance(fr, inspect.FrameInfo)
    mo = inspect.getmodule(fr.frame)
    assert mo is not None
    assert mo.__name__ == 'test_annotations'
