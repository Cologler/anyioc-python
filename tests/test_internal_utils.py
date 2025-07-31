# -*- coding: utf-8 -*-
# 
# Copyright (c) 2023~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

import pytest

from anyioc import ServiceProvider
from anyioc._utils import wrap_signature


def test_wrap_signature_with_no_params():
    sp = ServiceProvider()

    def func():
        return 1
    assert wrap_signature(func)(sp) == 1

def test_wrap_signature_with_single_positional_params():
    sp = ServiceProvider()

    def func(arg_0):
        return arg_0
    assert wrap_signature(func)(sp) is sp

def test_wrap_signature_with_single_keyword_params():
    sp = ServiceProvider()

    def func(*, arg_0):
        return arg_0
    assert wrap_signature(func)(sp) is sp

def test_wrap_signature_with_multi_params():
    def func(arg_0, arg_1):
        return arg_0 + arg_1
    with pytest.raises(TypeError):
        wrap_signature(func)

def test_wrap_signature_with_var_positional_params():
    sp = ServiceProvider()

    def func(*args):
        assert len(args) == 1
        return args
    assert wrap_signature(func)(sp) == (sp, )

def test_wrap_signature_with_var_keyword_params():
    sp = ServiceProvider()

    def func(**kwargs):
        return kwargs
    assert wrap_signature(func)(sp) == {
        'provider': sp
    }

def test_wrap_signature_with_both_var_params():
    sp = ServiceProvider()

    def func(*args, **kwargs):
        assert len(args) == 1
        assert len(kwargs) == 0
        return args
    assert wrap_signature(func)(sp) == (sp,)

def test_wrap_signature_with_both_var_params_with_args():
    sp = ServiceProvider()

    def func(sp, *args, **kwargs):
        assert len(args) == 0
        assert len(kwargs) == 0
        return sp
    assert wrap_signature(func)(sp) is sp
