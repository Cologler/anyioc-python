# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

import inspect
import itertools
from typing import Annotated, Callable, Iterable

from pytest import mark, raises

from anyioc import LifeTime, ServiceNotFoundError, ServiceProvider
from anyioc.annotations import DontInject, InjectBy, InjectByGroup, InjectFrom, InjectWithValue, injectable
from anyioc.keys import NamedType


def assert_resolve_lifetime(sps: Iterable[ServiceProvider], key: Callable, lifetime: LifeTime) -> None:
    for left, right in itertools.combinations_with_replacement(sps, 2):
        left_val = left.resolve(key)
        right_val = right.resolve(key)
        if lifetime == LifeTime.singleton:
            assert left_val is right_val
        elif lifetime == LifeTime.scoped:
            assert (left is right) == (left_val is right_val)
        elif lifetime == LifeTime.transient:
            assert left_val is not right_val
        else:
            raise ValueError(f'unsupported lifetime: {lifetime}')

def assert_resolve_lifetime_from_root(sp: ServiceProvider, key: Callable, lifetime: LifeTime) -> None:
    with sp.scope() as sp1:
        with sp.scope() as sp2:
            assert_resolve_lifetime([sp, sp1, sp2], key, lifetime)


def test_dontinject_resolves_required_parameter_error() -> None:
    def param_without_default_func(x: Annotated[int, DontInject()]) -> None:
        pass

    def param_with_default_func(x: Annotated[int, DontInject()] = 2) -> int:
        return x

    sp = ServiceProvider()
    sp.register_value(int, 1)

    with raises(TypeError):
        assert sp.resolve(param_without_default_func)

    assert 2 == sp.resolve(param_with_default_func)

def test_dontinject_ignores_varargs() -> None:
    def param_without_default_func(*args: Annotated[int, DontInject()]) -> tuple:
        return args

    sp = ServiceProvider()
    sp.register_value(int, 1)

    assert () == sp.resolve(param_without_default_func)

def test_dontinject_ignores_varkwargs() -> None:
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


def test_injectby_resolves_class_constructor_parameter() -> None:
    key = 'the_int_key'
    val = 444

    class A:
        def __init__(self, x: Annotated[int, InjectBy(key)]) -> None:
            self.val = x

    sp = ServiceProvider()
    sp.register_value(key, val)

    assert sp.resolve(A).val == val

def test_injectby_uses_default_for_class_constructor_parameter() -> None:
    key = 'the_int_key'
    val = 444

    class A:
        def __init__(self, x: Annotated[int, InjectBy(key, val)]) -> None:
            self.val = x

    sp = ServiceProvider()
    assert sp.resolve(A).val == val

def test_injectby_resolves_callable_parameter() -> None:
    key = 'the_int_key'
    val = 444

    def func(x: Annotated[int, InjectBy(key)]) -> int:
        return x

    sp = ServiceProvider()
    sp.register_value(key, val)

    assert sp.resolve(func) == val

def test_injectby_resolves_named_parameter() -> None:
    def func(x: Annotated[int, InjectBy(name='name2')]) -> int:
        return x

    sp = ServiceProvider()
    sp.register_transient(NamedType('name1', int), lambda: 1)
    sp.register_transient(NamedType('name2', int), lambda: 2)
    sp.register_transient(NamedType('name3', int), lambda: 3)
    sp.register_transient(NamedType('name4', int), lambda: 4)

    assert sp.resolve(func) == 2

@mark.parametrize(
    'lifetime',
    [LifeTime.transient, LifeTime.scoped],
    ids=['transient', 'scoped'],
)
def test_injectby_lifetime_caches_parameter(lifetime: LifeTime) -> None:
    key = 'djiaoshfoia'

    def get_value_1(x: Annotated[object, InjectBy(key, lifetime=lifetime)]) -> object:
        return x

    sp = ServiceProvider()
    sp.register_transient(key, lambda: object())

    assert_resolve_lifetime_from_root(sp, get_value_1, lifetime)

def test_injectby_lifetime_rejects_singleton() -> None:
    with raises(ValueError, match='Singleton lifetime for InjectBy is not allowed\\.'):
        InjectBy('key', lifetime=LifeTime.singleton)

def test_injectby_uses_default_for_callable_parameter() -> None:
    key = 'the_int_key'
    val = 444

    def func(x: Annotated[int, InjectBy(key, val)]) -> int:
        return x

    sp = ServiceProvider()

    assert sp.resolve(func) == val

def test_injectby_resolves_varargs() -> None:
    key = 'the_int_key'

    def func(*args: Annotated[int, InjectBy(key)]) -> tuple[int, ...]:
        return args

    sp = ServiceProvider()
    sp.register_value(key, 1)
    sp.register_value(key, 2)
    sp.register_value(key, 3)

    assert sp.resolve(func) == (3, 2, 1)

@mark.parametrize(
    'lifetime',
    [LifeTime.transient, LifeTime.scoped],
    ids=['transient', 'scoped'],
)
def test_injectby_lifetime_caches_varargs(lifetime: LifeTime) -> None:
    key = 'jioerwjherhg'

    def get_args_1(*args: Annotated[object, InjectBy(key, lifetime=lifetime)]) -> tuple[object, ...]:
        return args

    def get_args_2(*args: Annotated[object, InjectBy(key, lifetime=lifetime)]) -> tuple[object, ...]:
        return args

    sp = ServiceProvider()
    sp.register_transient(key, lambda: object())
    sp.register_transient(key, lambda: object())

    first = sp.resolve(get_args_1)
    second = sp.resolve(get_args_1)

    assert len(first) == len(second) == 2

    if lifetime == LifeTime.scoped:
        assert first == second, 'objects are cached on the same scoped function'
        assert len(set(first + sp.resolve(get_args_2))) == 4, \
            'objects are unique on different scoped function'

    else:
        assert len(set(first + second)) == 4, 'objects are unique on transient function'


def test_injectfrom_resolves_callable_dependency() -> None:
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

def test_injectfrom_does_not_use_parameter_default_for_unresolved_dependency() -> None:
    sp = ServiceProvider()

    def func_callee(val: int) -> int:
        return val

    def func_caller(val_from_callee: Annotated[object, InjectFrom(func_callee)] = 200) -> object:
        return val_from_callee

    # The caller parameter default is not a fallback for unresolved InjectFrom dependencies.
    with raises(ServiceNotFoundError) as se:
        sp.resolve(func_caller)
    assert se.value.resolve_chain == (int, )

    sp.register_value(int, 100)
    assert sp.resolve(func_caller) == 100


def test_injectbygroup_resolves_tuple_parameter() -> None:
    sv = 'ffw'
    iv = 46656

    def func(x: Annotated[tuple[str, int], InjectByGroup([str, int])]) -> tuple[str, int]:
        return x

    sp = ServiceProvider()
    sp.register_value(str, sv)
    sp.register_value(int, iv)
    assert sp.resolve(func) == (sv, iv)

def test_injectbygroup_resolves_varargs() -> None:
    sv = 'ffw'
    iv = 46656

    def func(*args: Annotated[str | int, InjectByGroup([str, int])]) -> tuple[str | int, ...]:
        return args

    sp = ServiceProvider()
    sp.register_value(str, sv)
    sp.register_value(int, iv)
    assert sp.resolve(func) == (sv, iv)


def test_injectwithvalue_resolves_parameter() -> None:
    def func(inject_from_ioc: Annotated[int, InjectWithValue(1)] = 0) -> int:
        return inject_from_ioc

    assert func() == 0
    assert ServiceProvider().resolve(func) == 1

def test_injectwithvalue_rejects_varargs() -> None:
    def func(*args: Annotated[int, InjectWithValue(1)]) -> tuple[int, ...]:
        return args

    assert func() == ()

    with raises(TypeError):
        ServiceProvider().resolve(func)

def test_injectable_registers_type_with_lifetime() -> None:
    @injectable(LifeTime.singleton)
    class S:
        def __init__(self) -> None:
            pass

    class T:
        def __init__(self) -> None:
            pass

    class A:
        def __init__(self, s: S, t: T) -> None:
            self.s = s
            self.t = t

    class B:
        def __init__(self, s: S) -> None:
            self.s = s

    sp = ServiceProvider()

    s = sp[S]

    a1 = sp.resolve(A, follow=True)
    a2 = sp.resolve(A, follow=True)
    assert a1.s is a2.s is s
    assert a1.t is not a2.t

    b1 = sp.resolve(B, follow=False)
    b2 = sp.resolve(B, follow=False)
    assert a1.s is b1.s is b2.s is s

def test_type_annotation_resolves_class_constructor_parameter() -> None:
    val = 444

    class A:
        def __init__(self, x: int) -> None:
            self.val = x

    sp = ServiceProvider()
    sp.register_value(int, val)
    assert sp.resolve(A).val == val

def test_type_annotation_uses_class_constructor_parameter_default() -> None:
    class A:
        def __init__(self, x: int = 200) -> None:
            self.val = x

    sp = ServiceProvider()
    assert sp.resolve(A).val == 200
    sp.register_value(int, 300)
    assert sp.resolve(A).val == 300

def test_type_annotation_resolves_service_provider() -> None:
    def get_value(val: ServiceProvider) -> ServiceProvider:
        return val

    sp = ServiceProvider()
    assert sp.resolve(get_value) is sp

def test_type_annotation_resolves_caller_frameinfo() -> None:
    def get_value(val: inspect.FrameInfo) -> inspect.FrameInfo:
        return val

    sp = ServiceProvider()

    fr = sp.resolve(get_value)
    assert isinstance(fr, inspect.FrameInfo)
    mo = inspect.getmodule(fr.frame)
    assert mo is not None
    assert mo.__name__ == 'test_annotations'
