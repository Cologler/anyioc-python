# -*- coding: utf-8 -*-
# 
# Copyright (c) 2023~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

import pytest
from pytest import raises

from anyioc import ServiceNotFoundError, ServiceProvider
from anyioc._utils import wrap_signature


def test_wrap_signature_with_no_params() -> None:
    sp = ServiceProvider()

    def func() -> int:
        return 1

    assert wrap_signature(func)(sp) == 1

def test_wrap_signature_with_single_positional_params() -> None:
    sp = ServiceProvider()

    def func(arg_0) -> object:  # noqa: ANN001
        return arg_0

    assert wrap_signature(func)(sp) is sp

def test_wrap_signature_with_annotated_single_positional_params() -> None:
    sp = ServiceProvider()

    def func(arg_0: int) -> object:
        return arg_0

    with raises(ServiceNotFoundError) as e:
        assert wrap_signature(func)(sp)

    assert e.value.resolve_chain == (int, )

def test_wrap_signature_with_single_keyword_params() -> None:
    sp = ServiceProvider()

    def func(*, arg_0) -> object:  # noqa: ANN001
        return arg_0

    assert wrap_signature(func)(sp) is sp

def test_wrap_signature_with_annotated_single_keyword_params() -> None:
    sp = ServiceProvider()

    def func(*, arg_0: object) -> object:
        return arg_0

    with raises(ServiceNotFoundError) as e:
        assert wrap_signature(func)(sp)

    assert e.value.resolve_chain == (object, )

def test_wrap_signature_with_multi_params() -> None:
    sp = ServiceProvider()
    sp.register_value(str, '100')

    def func_with_1_args(arg_0) -> tuple[object]:  # noqa: ANN001
        return (arg_0, )
    assert wrap_signature(func_with_1_args)(sp) == (sp, )

    def func_with_2_args(arg_0, arg_1) -> tuple[object, object]:  # noqa: ANN001
        return (arg_0, arg_1)
    with raises(TypeError):
        wrap_signature(func_with_2_args)

    def func_1_unknown_args(arg_0, arg_1: str) -> tuple[object, str]:  # noqa: ANN001
        return (arg_0, arg_1)
    assert wrap_signature(func_1_unknown_args)(sp) == (sp, '100')

    def func_2_unknown_args(arg_0, arg_1, arg_2: str) -> tuple[object, object, str]:  # noqa: ANN001
        return (arg_0, arg_1, arg_2)
    with pytest.raises(TypeError):
        wrap_signature(func_2_unknown_args)

def test_wrap_signature_with_multi_params_and_naming_convention() -> None:
    sp = ServiceProvider()
    sp.register_value(str, 'arg_1_val')

    # convention for ioc
    def func(ioc, arg_1: str) -> tuple[object, str]:  # noqa: ANN001
        return (ioc, arg_1)

    assert wrap_signature(func)(sp) == (sp, 'arg_1_val')

def test_wrap_signature_with_var_positional_params() -> None:
    sp = ServiceProvider()

    def func(*args) -> tuple[object, ...]:  # noqa: ANN002
        assert len(args) == 1
        return args

    assert wrap_signature(func)(sp) == (sp, )

def test_wrap_signature_with_var_positional_params_with_typing() -> None:
    sp = ServiceProvider()
    sp.register_value(int, 1)
    sp.register_value(int, 2)
    sp.register_value(int, 3)

    def func(*args: int) -> tuple[int, ...]:
        return args

    assert wrap_signature(func)(sp) == (3, 2, 1)

def test_wrap_signature_with_var_keyword_params() -> None:
    sp = ServiceProvider()

    def func(**kwargs) -> dict[str, object]:  # noqa: ANN003
        return kwargs

    assert wrap_signature(func)(sp) == {
        'provider': sp
    }

def test_wrap_signature_with_both_var_params() -> None:
    sp = ServiceProvider()

    def func(*args, **kwargs) -> tuple[tuple, dict]:  # noqa: ANN002, ANN003
        assert len(args) == 1
        assert len(kwargs) == 0
        return args, kwargs

    assert wrap_signature(func)(sp) == ((sp, ), {})

def test_wrap_signature_with_both_var_params_with_args() -> None:
    sp = ServiceProvider()

    def func(sp, *args, **kwargs) -> object:  # noqa: ANN001, ANN002, ANN003
        assert len(args) == 0
        assert len(kwargs) == 0
        return sp

    assert wrap_signature(func)(sp) is sp
