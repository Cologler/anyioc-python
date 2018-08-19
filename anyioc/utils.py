# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import sys
from typing import List, Tuple
from inspect import signature, Parameter

def inject_by(func, required: List[Tuple[str, object]], optional: List[Tuple[str, object, object]]):
    '''
    `required`: `(name, key)`
    `optional`: `(name, key, default)`
    '''
    def new_func(ioc):
        kwargs = {}
        for name, key in required:
            kwargs[name] = ioc[key]
        for name, key, default in optional:
            kwargs[name] = ioc.get(key, default)
        return func(**kwargs)
    return new_func

def inject_by_name(func):
    '''
    wrap the func and auto inject by parameter name.

    var keyword parameter and var positional parameter will not be inject.

    return the new func with signature: `(ioc) => any`
    '''
    sign = signature(func)
    params = [p for p in sign.parameters.values() if p.kind in (
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.KEYWORD_ONLY
    )]
    required: List[Tuple[str, str]] = []
    optional: List[Tuple[str, str, object]] = []
    for param in params:
        if param.default is Parameter.empty:
            required.append((param.name, param.name))
        else:
            optional.append((param.name, param.name, param.default))
    return inject_by(func, required, optional)

def inject_by_anno(func):
    '''
    wrap the func and auto inject by parameter annotation.

    var keyword parameter and var positional parameter will not be inject.

    return the new func with signature: `(ioc) => any`
    '''
    sign = signature(func)
    params = [p for p in sign.parameters.values() if p.kind in (
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.KEYWORD_ONLY
    )]
    required: List[Tuple[str, object]] = []
    optional: List[Tuple[str, object, object]] = []
    for param in params:
        if param.annotation is Parameter.empty:
            if param.default is Parameter.empty:
                raise ValueError(f'annotation of args {param.name} is empty.')
            else:
                # use `object()` for ensure you never get the value.
                optional.append((param.name, object(), param.default))
        else:
            if param.default is Parameter.empty:
                required.append((param.name, param.annotation))
            else:
                optional.append((param.name, param.annotation, param.default))
    return inject_by(func, required, optional)

def auto_enter(func):
    '''
    auto enter the context manager when it created.

    the signature of func should be `(ioc) => any`.
    '''
    def new_func(ioc):
        item = func(ioc)
        ioc.enter(item)
        return item
    return new_func

def dispose_at_exit(provider):
    '''
    register `provider.__exit__()` into `atexit` module.

    return the `provider` itself.
    '''
    import atexit
    @atexit.register
    def provider_dispose_at_exit():
        provider.__exit__(*sys.exc_info())
    return provider

# keep old func names:

auto_inject = inject_by_name
