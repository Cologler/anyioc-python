# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import sys
from typing import List, Tuple, Union, Any, Dict, Callable
import inspect
from inspect import signature, Parameter


def injectable(*pos_args: List[Union[Tuple[Any], Tuple[Any, Any]]],
               **kw_args: Dict[str, Union[Tuple[Any], Tuple[Any, Any]]]):
    '''
    return a decorator that use to convert a callable to `(ioc) => any` signature.

    each arguments must be a tuple, each tuple can contains 1 or 2 elements.
    the 1st element is the key for get service from ioc container;
    the 2rd element will be the default value if provide.

    Example:

    ``` py
    @injectable(a=('key1', 1), b=('key2'))
    def func(a, b):
        return a + b
    ```

    equals:

    ``` py
    def wrapper(ioc):
        return func(a=ioc.get('key1', 1), b=ioc['key2'])
    ```
    '''
    for tup in list(pos_args) + list(kw_args.values()):
        if not isinstance(tup, tuple):
            raise TypeError(f'excepted tuple, got {type(tup)}')
        if len(tup) not in (1, 2):
            raise ValueError('tuple should contains 1 or 2 elements')

    def decorator(func):
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

    return decorator

def inject_by_key_selector(selector: Callable[[Parameter], Any]):
    '''
    return a decorator that use to convert a callable to `(ioc) => any` signature
    with auto inject arguments by selector.

    `selector` should be a callcable which accept a `inspect.Parameter` object as argument,
    return the key use for inject.

    Note: *var keyword parameter and var positional parameter will be ignore.*
    '''

    if not callable(selector):
        raise TypeError

    def decorator(func):
        sign = signature(func)
        params = [p for p in sign.parameters.values()]
        pos_args = []
        kw_args = {}
        for param in params:
            ioc_key = selector(param)
            val = (ioc_key, ) if param.default is Parameter.empty else (ioc_key, param.default)
            if param.kind == Parameter.POSITIONAL_OR_KEYWORD:
                pos_args.append(val)
            elif param.kind == Parameter.KEYWORD_ONLY:
                kw_args[param.name] = val
        return injectable(*pos_args, **kw_args)(func)

    return decorator

def inject_by_name(func=None):
    '''
    convert a callable to `(ioc) => any` signature with auto inject arguments by parameter name.

    return a decorator if func is `None`.

    Note: *var keyword parameter and var positional parameter will be ignore.*
    '''
    decorator = inject_by_key_selector(lambda x: x.name)

    return decorator if func is None else decorator(func)

def inject_by_anno(func=None, *, use_name_if_empty: bool = False):
    '''
    convert a callable to `(ioc) => any` signature with auto inject arguments by parameter annotation.

    return a decorator if func is `None`.

    Options:

    - `use_name_if_empty`: whether use `Parameter.name` as key when `Parameter.annotation` is empty.

    Note: *var keyword parameter and var positional parameter will be ignore.*
    '''
    def decorator(func):
        def selector(param: Parameter):
            anno = param.annotation
            if anno is Parameter.empty:
                if use_name_if_empty:
                    ioc_key = param.name
                elif param.default is Parameter.empty:
                    raise ValueError(f'annotation of args {param.name} is empty.')
                else:
                    # use `object()` for ensure you never get any value.
                    ioc_key = object()
            else:
                ioc_key = anno
            return ioc_key

        return inject_by_key_selector(selector)(func)

    return decorator if func is None else decorator(func)

def inject_by_keys(**keys):
    '''
    return a decorator that use to convert a callable to `(ioc) => any` signature
    with auto inject arguments by keys.

    - keys should be parameter name of func.
    - values are the key that use to get service from service provider.
    '''

    kw_args = dict((k, (v, )) for k, v in keys.items())
    return injectable(**kw_args)

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

def make_group(container, group_key=None):
    '''
    add a new group into `container` by key `group_key`.
    if `group_key` is `None`, use return function as key.

    return a function accept single argument for add next group item key.
    '''
    group_keys = []

    def add_next_key(next_group_key):
        '''
        add next key into this group.
        '''
        group_keys.append(next_group_key)
        return next_group_key

    if group_key is None:
        group_key = add_next_key

    container.register_group(group_key, group_keys)

    return add_next_key

def find_keys(obj):
    keys = []

    if isinstance(obj, type):
        try:
            # only hashable() canbe key
            hash(obj)
            keys.append(obj)
        except TypeError:
            pass

    try:
        name = getattr(obj, '__name__')
        keys.append(name)
    except AttributeError:
        pass

    return keys

def get_module_name(fr: inspect.FrameInfo):
    'get module name from frame info'
    mo = inspect.getmodule(fr.frame)
    name = '<stdin>' if mo is None else mo.__name__
    return name

def get_logger(ioc):
    '''
    a helper that use to get logger from ioc.

    Usage:

    ``` py
    ioc.register_transient('logger', get_logger) # use transient to ensure no cache
    logger = ioc['logger']
    assert logger.name == __name__ # the logger should have module name
    ```
    '''
    import logging
    import inspect
    from .symbols import Symbols

    fr = ioc[Symbols.caller_frame]
    name = get_module_name(fr)
    return logging.getLogger(name)

# keep old func names:

auto_inject = inject_by_name
