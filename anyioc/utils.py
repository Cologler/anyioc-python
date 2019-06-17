# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import sys
from typing import List, Tuple, Union, Any, Dict, Callable
from inspect import signature, Parameter

def injectable(*pos_args: List[Union[Tuple[Any], Tuple[Any, Any]]],
               **kw_args: Dict[str, Union[Tuple[Any], Tuple[Any, Any]]]):
    '''
    each **value** in `pos_args` and `kw_args` should be a tuple,
    the 1st item in tuple is the key for get service from ioc container;

    if len of tuple is 2,
    the 2rd item is the default value.

    example:

    ``` py
    @injectable(a=('ioc-key', 'default-value-for-param'))
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

def inject_by_key_selector(selector: Callable[[Parameter], Any]):
    '''
    wrap the func and auto inject by key selector.

    `selector` should be a callcable which accept a `Parameter` object as argument,
    return the key use for inject.

    var keyword parameter and var positional parameter will be ignore.

    `inject_by_key_selector` return a function decorator,
    and the decorator return the new func with signature: `(ioc) => any`
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

def inject_by_name(func):
    '''
    wrap the func and auto inject by parameter name.

    var keyword parameter and var positional parameter will be ignore.

    return the new func with signature: `(ioc) => any`
    '''
    return inject_by_key_selector(lambda x: x.name)(func)

def inject_by_anno(func=None, *, use_name_if_empty: bool = False):
    '''
    wrap the func and auto inject by parameter annotation.

    var keyword parameter and var positional parameter will be ignore.

    `use_name_if_empty`: whether use `Parameter.name` as key when `Parameter.annotation` is empty.

    return the new func with signature: `(ioc) => any`
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
    wrap the func and auto inject by keys.

    each key in keys should be parameter name of func.

    each value in keys should use for get value from service provider.

    return a decorator for wrap your func to new func with signature: `(ioc) => any`.
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

# keep old func names:

auto_inject = inject_by_name
