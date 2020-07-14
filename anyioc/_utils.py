# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
# the internal utils.
# user should not import anything from this file.
# ----------

import sys
import atexit
import inspect

def get_module_name(fr: inspect.FrameInfo):
    'get module name from frame info'
    mo = inspect.getmodule(fr.frame)
    name = '<stdin>' if mo is None else mo.__name__
    return name

def dispose_at_exit(provider):
    '''
    register `provider.__exit__()` into `atexit` module.

    return the `provider` itself.
    '''
    @atexit.register
    def provider_dispose_at_exit():
        provider.__exit__(*sys.exc_info())
    return provider
