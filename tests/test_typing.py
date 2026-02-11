# -*- coding: utf-8 -*-
# 
# Copyright (c) 2026~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------
from typing import assert_type

from anyioc import ServiceProvider


def test_get_typed_typing() -> None:
    sp = ServiceProvider()
    sp.register_value('', 123)
    sp.register_value(int, 456)

    assert_type(sp.get_typed(int, ''), int | None)
    assert_type(sp.get_typed(int, '', default={}), int | dict)
    assert_type(sp.get_typed(int), int | None)

def test_get_required_typed_typing() -> None:
    sp = ServiceProvider()
    sp.register_value('', 123)
    sp.register_value(int, 456)

    assert_type(sp.get_required_typed(int, ''), int)
    assert_type(sp.get_required_typed(int), int)
