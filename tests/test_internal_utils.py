# -*- coding: utf-8 -*-
# 
# Copyright (c) 2023~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

import pytest

from anyioc._utils import wrap_signature

def test_wrap_signature_with_no_params():
    def func():
        return 1
    assert wrap_signature(func)(None) == 1

def test_wrap_signature_with_single_positional_params():
    def func(arg_0):
        return arg_0
    assert wrap_signature(func)(2) == 2

def test_wrap_signature_with_single_keyword_params():
    def func(*, arg_0):
        return arg_0
    assert wrap_signature(func)(3) == 3

def test_wrap_signature_with_multi_params():
    def func(arg_0, arg_1):
        return arg_0 + arg_1
    with pytest.raises(TypeError):
        wrap_signature(func)

def test_wrap_signature_with_var_positional_params():
    def func(*args):
        assert len(args) == 1
        return args
    assert wrap_signature(func)(5) == (5, )

def test_wrap_signature_with_var_keyword_params():
    def func(**kwargs):
        return kwargs
    assert wrap_signature(func)(6) == {
        'provider': 6
    }

def test_wrap_signature_with_both_var_params():
    def func(*args, **kwargs):
        assert len(args) == 1
        assert len(kwargs) == 0
        return args
    assert wrap_signature(func)(7) == (7,)

def test_wrap_signature_with_both_var_params_with_args():
    def func(sp, *args, **kwargs):
        assert len(args) == 0
        assert len(kwargs) == 0
        return sp
    assert wrap_signature(func)(8) == 8
