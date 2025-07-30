# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import logging
from inspect import Parameter, signature
from typing import Any, Callable, Literal, overload

from ._utils import create_adapter as _create_adapter
from ._utils import get_module_name as _get_module_name
from .annotations import InjectBy
from .ioc import IServiceProvider
from .symbols import Symbols


def injectable(
        *p_params: tuple[Any] | tuple[Any, Any],
        **k_params: tuple[Any] | tuple[Any, Any]
    ):
    '''
    return a decorator that use to wrap a callable with signature `(ioc) => any`.

    for each item in `pos_args` and each value in `kw_args`:

    - must be a tuple, with 1 or 2 elements;
    - element 1 is the key for get service from `ServiceProvider` container;
    - element 2 is the default value if provide,
      otherwise will use `ServiceProvider.__getitem__()` to get service;

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
    for tup in list(p_params) + list(k_params.values()):
        if not isinstance(tup, tuple):
            raise TypeError(f'excepted tuple, got {type(tup)}')
        if len(tup) not in (1, 2):
            raise ValueError('tuple should contains 1 or 2 elements')

    def decorator[R](func: Callable[..., R]):
        return _create_adapter(func, p_params, k_params)

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

    def decorator[**P, R](func: Callable[P, R], /):
        sign = signature(func)
        params = [p for p in sign.parameters.values()]
        p_params: list[InjectBy] = []
        k_params: dict[str, InjectBy] = {}
        for param in params:
            ioc_key = selector(param)
            val = (ioc_key, ) if param.default is Parameter.empty else (ioc_key, param.default)
            if param.kind is Parameter.POSITIONAL_ONLY:
                p_params.append(InjectBy(*val))
            elif param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY):
                k_params[param.name] = InjectBy(*val)
        return _create_adapter(func, p_params, k_params)

    return decorator

@overload
def inject_by_name[**P, R](func: Literal[None] = None) -> Callable[[Callable[P, R]], Callable[[IServiceProvider], R]]: ...
@overload
def inject_by_name[**P, R](func: Callable[P, R] | None) -> Callable[[IServiceProvider], R]: ...
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

@overload
def inject_by_anno[**P, R](func: Literal[None] = None, *, use_name_if_empty: bool = False) \
    -> Callable[[Callable[P, R]], Callable[[IServiceProvider], R]]: ...
@overload
def inject_by_anno[**P, R](func: Callable[P, R] | None, *, use_name_if_empty: bool = False) \
    -> Callable[[IServiceProvider], R]: ...
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
    def decorator(func, /):
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
    fr = ioc[Symbols.caller_frame]
    name = _get_module_name(fr)
    return logging.getLogger(name)

def is_root(provider: IServiceProvider):
    '''
    Test is the IServiceProvider is the root provider or not.
    '''
    return provider[Symbols.provider_root] is provider

def get_scope_depth(provider: IServiceProvider):
    '''
    Get the depth of scopes.

    The root provider is 0.
    '''
    depth = 0
    root = provider[Symbols.provider_root]
    while provider is not root:
        provider = provider[Symbols.provider_parent]
        depth += 1
    return depth

# keep old func names:

auto_inject = inject_by_name
