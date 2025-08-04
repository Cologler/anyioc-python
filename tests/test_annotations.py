# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

import inspect
from typing import Annotated, Any

from pytest import raises

from anyioc import LifeTime, ServiceProvider, ServiceNotFoundError
from anyioc.annotations import InjectBy, InjectByGroup, InjectFrom, InjectWithValue


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
    key = 'djiaoshfoia'

    def get_transient(x: Annotated[object, InjectBy(key, lifetime=LifeTime.transient)]):
        return x

    def get_scoped_1(x: Annotated[object, InjectBy(key, lifetime=LifeTime.scoped)]):
        return x

    def get_scoped_2(x: Annotated[object, InjectBy(key, lifetime=LifeTime.scoped)]):
        return x

    sp = ServiceProvider()
    sp.register_transient(key, lambda: object())

    assert sp.resolve(get_transient) is not sp.resolve(get_transient), 'transient should never cached'
    assert sp.resolve(get_scoped_1) is sp.resolve(get_scoped_1), 'scoped should cached'
    assert sp.resolve(get_scoped_2) is sp.resolve(get_scoped_2), 'scoped should cached'
    assert sp.resolve(get_scoped_1) is not sp.resolve(get_scoped_2), 'should not cache cross function'

def test_inject_func_by_annotated_injectby_with_default():
    key = 'the_int_key'
    val = 444

    def func(x: Annotated[int, InjectBy(key, val)]):
        return x

    sp = ServiceProvider()

    assert sp.resolve(func) == val

def test_inject_func_by_annotated_injectby_for_args():
    key = 'the_int_key'

    def func(*args: Annotated[int, InjectBy(key)]):
        return args

    sp = ServiceProvider()
    sp.register_value(key, 1)
    sp.register_value(key, 2)
    sp.register_value(key, 3)

    assert sp.resolve(func) == (3, 2, 1)

def test_inject_func_by_annotated_injectby_for_args_with_lifetime():
    key = 'jioerwjherhg'

    def get_transient(*args: Annotated[object, InjectBy(key, lifetime=LifeTime.transient)]):
        return args

    def get_scoped_1(*args: Annotated[object, InjectBy(key, lifetime=LifeTime.scoped)]):
        return args

    def get_scoped_2(*args: Annotated[object, InjectBy(key, lifetime=LifeTime.scoped)]):
        return args

    sp = ServiceProvider()
    sp.register_transient(key, lambda: object())
    sp.register_transient(key, lambda: object())

    assert all(len(sp.resolve(f)) == 2 for f in [get_transient, get_scoped_1, get_scoped_2]), \
        'all args are tuple[object, object]'

    assert len(set(x for f in [get_transient, get_transient] for x in sp.resolve(f))) == 4, \
        'objects are unique on all transient function'

    assert len(set(x for f in [get_scoped_1, get_scoped_2] for x in sp.resolve(f))) == 4, \
        'objects are unique on different scoped function'

    assert sp.resolve(get_scoped_1) == sp.resolve(get_scoped_1), \
        'objects are cached on different scoped function'


def test_inject_func_by_annotated_injectfrom():
    sp = ServiceProvider()

    def func_callee(val: int):
        return val

    def func_caller(val_from_callee: Annotated[Any, InjectFrom(func_callee)]):
        return val_from_callee

    with raises(ServiceNotFoundError) as se:
        sp.resolve(func_caller)
    assert se.value.resolve_chain == (int, )

    sp.register_value(int, 100)
    assert sp.resolve(func_caller) == 100

def test_inject_func_by_annotated_injectfrom_with_default():
    sp = ServiceProvider()

    def func_callee(val: int):
        return val

    def func_caller(val_from_callee: Annotated[Any, InjectFrom(func_callee)] = 200):
        return val_from_callee

    with raises(ServiceNotFoundError) as se:
        sp.resolve(func_caller)
    assert se.value.resolve_chain == (int, )

    sp.register_value(int, 100)
    assert sp.resolve(func_caller) == 100


def test_inject_func_by_annotated_injectbygroup():
    sv = 'ffw'
    iv = 46656

    def func(x: Annotated[tuple[str, int], InjectByGroup([str, int])]):
        return x

    sp = ServiceProvider()
    sp.register_value(str, sv)
    sp.register_value(int, iv)
    assert sp.resolve(func) == (sv, iv)

def test_inject_func_by_annotated_injectbygroup_for_args():
    sv = 'ffw'
    iv = 46656

    def func(*args: Annotated[str| int, InjectByGroup([str, int])]):
        return args

    sp = ServiceProvider()
    sp.register_value(str, sv)
    sp.register_value(int, iv)
    assert sp.resolve(func) == (sv, iv)


def test_inject_func_by_annotated_injectwithvalue():
    def func(inject_from_ioc: Annotated[int, InjectWithValue(1)] = 0):
        return inject_from_ioc

    assert func() == 0
    assert ServiceProvider().resolve(func) == 1

def test_inject_func_by_annotated_injectwithvalue_for_args():
    def func(*args: Annotated[int, InjectWithValue(1)]):
        return args

    assert func() == ()

    with raises(TypeError):
        ServiceProvider().resolve(func)


def test_inject_class_by_typed():
    val = 444

    class A:
        def __init__(self, x: int) -> None:
            self.val = x

    sp = ServiceProvider()
    sp.register_value(int, val)
    assert sp.resolve(A).val == val

def test_inject_class_by_typed_with_default():
    class A:
        def __init__(self, x: int = 200) -> None:
            self.val = x

    sp = ServiceProvider()
    assert sp.resolve(A).val == 200
    sp.register_value(int, 300)
    assert sp.resolve(A).val == 300

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
