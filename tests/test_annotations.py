# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from typing import Annotated

from anyioc import ServiceProvider
from anyioc.annotations import InjectBy


def test_inject_by_key():
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

def test_inject_by_key_with_default():
    key = 'the_int_key'

    class A:
        def __init__(self, x: Annotated[int, InjectBy(key, 555)]) -> None:
            self.val = x

    sp = ServiceProvider()
    sp.register_singleton(A, A)

    a: A = sp[A]
    assert a.val == 555
