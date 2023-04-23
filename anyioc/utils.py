# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import List, Tuple, Union, Any, Dict, Callable
from inspect import signature, Parameter

from ._utils import (
    get_module_name as _get_module_name,
    update_wrapper as _update_wrapper
)

def injectable(*pos_args: List[Union[Tuple[Any], Tuple[Any, Any]]],
               **kw_args: Dict[str, Union[Tuple[Any], Tuple[Any, Any]]]):
    '''
    return a decorator that use to wrap a callable with signature `(ioc) => any`.

    for each item in `pos_args` and each value in `kw_args`:

    - must be a tuple, with 1 or 2 elements;
    - element 1 is the key for get service from `ServiceProvider` container;
    - element 2 is the default value if provide,
      otherwise will use `ServiceProvider.__getitem__()` to get service;
    -

    ### Example:

    ``` py
    @injectable(a=('key1', 1), b=('key2'))
    def func(a, b):
        return a + b
    ```

    is equals:

    ``` py
    def func(ioc):
        def _func(a, b):
            return a + b
        return _func(a=ioc.get('key1', 1), b=ioc['key2'])
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
        return _update_wrapper(new_func, func)

    return decorator

def inject_by_key_selector(selector: Callable[[Parameter], Any]):
    '''
    inject arguments by `selector`.

    return a decorator that use to wrap a callable with signature `(ioc) => any`.

    `selector` should be a callable which accept a `inspect.Parameter` object as argument,
    return the key use for inject.

    Note: var keyword parameters and var positional parameters will be ignore.
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
            if param.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD):
                pos_args.append(val)
            elif param.kind == Parameter.KEYWORD_ONLY:
                kw_args[param.name] = val
        return injectable(*pos_args, **kw_args)(func)

    return decorator

def inject_by_name(func=None):
    '''
    wrap a callable with signature `(ioc) => any` for inject arguments by parameter name.

    return a decorator when `func` is `None`.

    ### Example:

    ``` py
    @inject_by_name
    def func(a, b='x'):
        return a + b
    ```

    is equals:

    ``` py
    def func(ioc):
        def _func(a, b):
            return a + b
        return _func(a=ioc['a'], b=ioc.get('b', 'x'))
    ```
    '''
    decorator = inject_by_key_selector(lambda x: x.name)

    return decorator if func is None else decorator(func)

def inject_by_anno(func=None, *, use_name_if_empty: bool = False):
    '''
    wrap a callable with signature `(ioc) => any` for inject arguments by parameter annotation.

    return a decorator when `func` is `None`.

    Options:

    - `use_name_if_empty`: whether use `Parameter.name` as key when the `Parameter.annotation` is empty.

    ### Example:

    ``` py
    @inject_by_anno
    def func(a: int, b: str='x'):
        return a + b
    ```

    is equals:

    ``` py
    def func(ioc):
        def _func(a, b):
            return a + b
        return _func(a=ioc[int], b=ioc.get(str, 'x'))
    ```
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
                    # use `object()` as key to ensure never get any value from container.
                    ioc_key = object()
            else:
                ioc_key = anno
            return ioc_key

        return inject_by_key_selector(selector)(func)

    return decorator if func is None else decorator(func)

def inject_by_keys(**keys):
    '''
    inject arguments by `keys`.

    return a decorator that use to wrap a callable with signature `(ioc) => any`.

    - keys should be parameter name of func.
    - values are the key that use to get service from service provider.

    ### Example:

    ``` py
    @inject_by_keys(a='key1', b='key2')
    def func(a, b):
        return a + b
    ```

    is equals:

    ``` py
    def func(ioc):
        def _func(a, b):
            return a + b
        return _func(a=ioc['key1'], b=ioc['key2'])
    ```
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
    from .symbols import Symbols

    fr = ioc[Symbols.caller_frame]
    name = _get_module_name(fr)
    return logging.getLogger(name)


class Releaser:
    '''
    A helper class to wrap a function as a exitable object.
    The `callback` will be call when the context manager exit.
    '''
    __slots__ = '_callback'

    def __init__(self, callback) -> None:
        self._callback = callback

    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._callback()

# keep old func names:

auto_inject = inject_by_name
