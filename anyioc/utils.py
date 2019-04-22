# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import sys
from typing import List, Tuple, Union, Any, Dict
from inspect import signature, Parameter

def injectable(*pos_args: List[Union[Tuple[Any], Tuple[Any, Any]]],
               **kw_args: Dict[str, Union[Tuple[Any], Tuple[Any, Any]]]):
    '''
    for each tuple in `pos_args`, the 1st item is the key, the 2rd item is the default value if provide.

    for each value tuple in `kw_args`, the 1st item is the key, the 2rd item is the default value if provide.

    example:

    ``` py
    @injectable(a=('key', 'def-val'))
    def func(a):
        pass
    ```
    '''
    def wrapper(func):
        def new_func(ioc):
            args = []
            for item in pos_args:
                if len(item) == 1:
                    args.append(ioc[item[0]])
                else:
                    key, default = item
                    args.append(ioc.get(key, default))
            kwargs = {}
            for name, item in kw_args.items():
                if len(item) == 1:
                    kwargs[name] = ioc[item[0]]
                else:
                    key, default = item
                    kwargs[name] = ioc.get(key, default)
            return func(*args, **kwargs)
        return new_func
    return wrapper

def inject_by_name(func):
    '''
    wrap the func and auto inject by parameter name.

    var keyword parameter and var positional parameter will not be inject.

    return the new func with signature: `(ioc) => any`
    '''
    sign = signature(func)
    params = [p for p in sign.parameters.values()]
    pos_args = []
    kw_args = {}
    for param in params:
        val = (param.name, ) if param.default is Parameter.empty else (param.name, param.default)
        if param.kind == Parameter.POSITIONAL_OR_KEYWORD:
            pos_args.append(val)
        elif param.kind == Parameter.KEYWORD_ONLY:
            kw_args[param.name] = val
    return injectable(*pos_args, **kw_args)(func)

def inject_by_anno(func):
    '''
    wrap the func and auto inject by parameter annotation.

    var keyword parameter and var positional parameter will not be inject.

    return the new func with signature: `(ioc) => any`
    '''
    sign = signature(func)
    params = [p for p in sign.parameters.values()]
    pos_args = []
    kw_args = {}
    for param in params:
        anno = param.annotation
        if anno is Parameter.empty:
            if param.default is Parameter.empty:
                raise ValueError(f'annotation of args {param.name} is empty.')
            # use `object()` for ensure you never get the value.
            ioc_key = object()
        else:
            ioc_key = anno
        val = (ioc_key, ) if param.default is Parameter.empty else (ioc_key, param.default)

        if param.kind == Parameter.POSITIONAL_OR_KEYWORD:
            pos_args.append(val)
        elif param.kind == Parameter.KEYWORD_ONLY:
            kw_args[param.name] = val

    return injectable(*pos_args, **kw_args)(func)

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

def make_group(container, group_key):
    '''
    add a new group into `container` by `group_key`,
    return a decorator function for add next group item key.

    '''
    group_keys = []
    container.register_group(group_key, group_keys)
    def decorator(next_group_key):
        group_keys.append(next_group_key)
        return next_group_key
    return decorator

# keep old func names:

auto_inject = inject_by_name
