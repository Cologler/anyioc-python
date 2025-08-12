# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

import inspect
from typing import Annotated

from pytest import raises

from anyioc import LifeTime, ServiceNotFoundError, ServiceProvider
from anyioc.annotations import DontInject, InjectBy, InjectByGroup, InjectFrom, InjectWithValue
from anyioc.keys import NamedType


def test_inject_func_by_annotated_dontinject() -> None:
    def param_without_default_func(x: Annotated[int, DontInject()]) -> None:
        pass

    def param_with_default_func(x: Annotated[int, DontInject()] = 2) -> int:
        return x

    sp = ServiceProvider()
    sp.register_value(int, 1)

    with raises(TypeError):
        assert sp.resolve(param_without_default_func)

    assert 2 == sp.resolve(param_with_default_func)

def test_inject_func_by_annotated_dontinject_for_args() -> None:
    def param_without_default_func(*args: Annotated[int, DontInject()]) -> tuple:
        return args

    sp = ServiceProvider()
    sp.register_value(int, 1)

    assert () == sp.resolve(param_without_default_func)

def test_inject_func_by_annotated_dontinject_for_kwargs() -> None:
    def default_kwargs_func(**kwargs) -> dict[str, object]:  # noqa: ANN003
        return kwargs

    def default_typed_kwargs_func(**kwargs: int) -> dict[str, int]:
        return kwargs

    def kwargs_annotated_dontinject_func(**kwargs: Annotated[int, DontInject()]) -> dict[str, int]:
        return kwargs

    sp = ServiceProvider()
    sp.register_value(NamedType('val', int), 1)

    assert sp.resolve(default_kwargs_func) == {'provider': sp}
    assert sp.resolve(default_typed_kwargs_func) == {'val': 1}
    assert sp.resolve(kwargs_annotated_dontinject_func) == {}


def test_inject_class_by_annotated_injectby() -> None:
    key = 'the_int_key'
    val = 444

    class A:
        def __init__(self, x: Annotated[int, InjectBy(key)]) -> None:
            self.val = x

    sp = ServiceProvider()
    sp.register_value(key, val)

    assert sp.resolve(A).val == val

def test_inject_class_by_annotated_injectby_with_default() -> None:
    key = 'the_int_key'
    val = 444

    class A:
        def __init__(self, x: Annotated[int, InjectBy(key, val)]) -> None:
            self.val = x

    sp = ServiceProvider()
    assert sp.resolve(A).val == val

def test_inject_func_by_annotated_injectby() -> None:
    key = 'the_int_key'
    val = 444

    def func(x: Annotated[int, InjectBy(key)]) -> int:
        return x

    sp = ServiceProvider()
    sp.register_value(key, val)

    assert sp.resolve(func) == val

def test_inject_func_by_annotated_injectby_with_name() -> None:
    def func(x: Annotated[int, InjectBy(name='name2')]) -> int:
        return x

    sp = ServiceProvider()
    sp.register_transient(NamedType('name1', int), lambda: 1)
    sp.register_transient(NamedType('name2', int), lambda: 2)
    sp.register_transient(NamedType('name3', int), lambda: 3)
    sp.register_transient(NamedType('name4', int), lambda: 4)

    assert sp.resolve(func) == 2

def test_inject_func_by_annotated_injectby_with_lifetime() -> None:
    key = 'djiaoshfoia'

    def get_transient(x: Annotated[object, InjectBy(key, lifetime=LifeTime.transient)]) -> object:
        return x

    def get_scoped_1(x: Annotated[object, InjectBy(key, lifetime=LifeTime.scoped)]) -> object:
        return x

    def get_scoped_2(x: Annotated[object, InjectBy(key, lifetime=LifeTime.scoped)]) -> object:
        return x

    sp = ServiceProvider()
    sp.register_transient(key, lambda: object())

    assert sp.resolve(get_transient) is not sp.resolve(get_transient), 'transient should never cached'
    assert sp.resolve(get_scoped_1) is sp.resolve(get_scoped_1), 'scoped should cached'
    assert sp.resolve(get_scoped_2) is sp.resolve(get_scoped_2), 'scoped should cached'
    assert sp.resolve(get_scoped_1) is not sp.resolve(get_scoped_2), 'should not cache cross function'

def test_inject_func_by_annotated_injectby_with_default() -> None:
    key = 'the_int_key'
    val = 444

    def func(x: Annotated[int, InjectBy(key, val)]) -> int:
        return x

    sp = ServiceProvider()

    assert sp.resolve(func) == val

def test_inject_func_by_annotated_injectby_for_args() -> None:
    key = 'the_int_key'

    def func(*args: Annotated[int, InjectBy(key)]) -> tuple[int, ...]:
        return args

    sp = ServiceProvider()
    sp.register_value(key, 1)
    sp.register_value(key, 2)
    sp.register_value(key, 3)

    assert sp.resolve(func) == (3, 2, 1)

def test_inject_func_by_annotated_injectby_for_args_with_lifetime() -> None:
    key = 'jioerwjherhg'

    def get_transient(*args: Annotated[object, InjectBy(key, lifetime=LifeTime.transient)]) -> tuple[object, ...]:
        return args

    def get_scoped_1(*args: Annotated[object, InjectBy(key, lifetime=LifeTime.scoped)]) -> tuple[object, ...]:
        return args

    def get_scoped_2(*args: Annotated[object, InjectBy(key, lifetime=LifeTime.scoped)]) -> tuple[object, ...]:
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


def test_inject_func_by_annotated_injectfrom() -> None:
    sp = ServiceProvider()

    def func_callee(val: int) -> int:
        return val

    def func_caller(val_from_callee: Annotated[object, InjectFrom(func_callee)]) -> object:
        return val_from_callee

    with raises(ServiceNotFoundError) as se:
        sp.resolve(func_caller)
    assert se.value.resolve_chain == (int, )

    sp.register_value(int, 100)
    assert sp.resolve(func_caller) == 100

def test_inject_func_by_annotated_injectfrom_with_default() -> None:
    sp = ServiceProvider()

    def func_callee(val: int) -> int:
        return val

    def func_caller(val_from_callee: Annotated[object, InjectFrom(func_callee)] = 200) -> object:
        return val_from_callee

    with raises(ServiceNotFoundError) as se:
        sp.resolve(func_caller)
    assert se.value.resolve_chain == (int, )

    sp.register_value(int, 100)
    assert sp.resolve(func_caller) == 100


def test_inject_func_by_annotated_injectbygroup() -> None:
    sv = 'ffw'
    iv = 46656

    def func(x: Annotated[tuple[str, int], InjectByGroup([str, int])]) -> tuple[str, int]:
        return x

    sp = ServiceProvider()
    sp.register_value(str, sv)
    sp.register_value(int, iv)
    assert sp.resolve(func) == (sv, iv)

def test_inject_func_by_annotated_injectbygroup_for_args() -> None:
    sv = 'ffw'
    iv = 46656

    def func(*args: Annotated[str | int, InjectByGroup([str, int])]) -> tuple[str | int, ...]:
        return args

    sp = ServiceProvider()
    sp.register_value(str, sv)
    sp.register_value(int, iv)
    assert sp.resolve(func) == (sv, iv)


def test_inject_func_by_annotated_injectwithvalue() -> None:
    def func(inject_from_ioc: Annotated[int, InjectWithValue(1)] = 0) -> int:
        return inject_from_ioc

    assert func() == 0
    assert ServiceProvider().resolve(func) == 1

def test_inject_func_by_annotated_injectwithvalue_for_args() -> None:
    def func(*args: Annotated[int, InjectWithValue(1)]) -> tuple[int, ...]:
        return args

    assert func() == ()

    with raises(TypeError):
        ServiceProvider().resolve(func)


def test_inject_class_by_typed() -> None:
    val = 444

    class A:
        def __init__(self, x: int) -> None:
            self.val = x

    sp = ServiceProvider()
    sp.register_value(int, val)
    assert sp.resolve(A).val == val

def test_inject_class_by_typed_with_default() -> None:
    class A:
        def __init__(self, x: int = 200) -> None:
            self.val = x

    sp = ServiceProvider()
    assert sp.resolve(A).val == 200
    sp.register_value(int, 300)
    assert sp.resolve(A).val == 300

def test_inject_types_for_service_provider() -> None:
    def get_value(val: ServiceProvider) -> ServiceProvider:
        return val

    sp = ServiceProvider()
    assert sp.resolve(get_value) is sp

def test_inject_types_for_frameinfo() -> None:
    def get_value(val: inspect.FrameInfo) -> inspect.FrameInfo:
        return val

    sp = ServiceProvider()

    fr = sp.resolve(get_value)
    assert isinstance(fr, inspect.FrameInfo)
    mo = inspect.getmodule(fr.frame)
    assert mo is not None
    assert mo.__name__ == 'test_annotations'
