# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import inspect
from pytest import raises

from anyioc import ServiceProvider
from anyioc.symbols import Symbols

def test_symbol_caller_frame():
    provider = ServiceProvider()
    fr = provider[Symbols.caller_frame]
    mo = inspect.getmodule(fr.frame)
    assert mo.__name__ == 'test_symbols'

def test_symbol_caller_frame_from_deep():
    provider = ServiceProvider()
    def get_name(ioc):
        fr = ioc[Symbols.caller_frame]
        mo = inspect.getmodule(fr.frame)
        return mo.__name__
    provider.register_transient('name', get_name)
    assert provider['name'] == 'test_symbols'
    