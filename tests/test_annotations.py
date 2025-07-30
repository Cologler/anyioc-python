# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from typing import Annotated

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
