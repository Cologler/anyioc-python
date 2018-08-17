# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from inspect import signature, Parameter

def auto_inject(func):
    '''
    wrap the func and auto inject by parameter name.

    var keyword parameter and var positional parameter will not be inject.
    '''
    sign = signature(func)
    names = [p.name for p in sign.parameters.values() if p.kind in (
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.KEYWORD_ONLY
    )]
    def new_func(ioc):
        kwargs = {}
        for name in names:
            kwargs[name] = ioc.get(name)
        return func(**kwargs)
    return new_func
