# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
# the internal utils.
# user should not import anything from this file.
# ----------

import atexit
import inspect
import sys
from collections.abc import Iterable, Mapping
from inspect import Parameter
from typing import Annotated, Any, Callable, cast, get_args, get_origin

from .annotations import InjectBy


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

def update_wrapper(wrapper, wrapped):
    '''
    update wrapper with internal attributes.
    '''
    wrapper.__anyioc_wrapped__ = getattr(wrapped, '__anyioc_wrapped__', wrapped)
    return wrapper

def wrap_signature[R](func: Callable[..., R]):
    '''
    wrap the function to single argument function.

    unlike the `inject*` series of utils, this is used for implicit convert.
    '''

    sign = inspect.signature(func)
    params = list(sign.parameters.values())
    if len(params) > 1:
        params = [p for p in params if p.kind != Parameter.VAR_KEYWORD]
    if len(params) > 1:
        params = [p for p in params if p.kind != Parameter.VAR_POSITIONAL]

    def get_injectby(param: Parameter):
        if param.kind in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL):
            return None
        if param.annotation is not Parameter.empty:
            if get_origin(param.annotation) is Annotated:
                metadatas = get_args(param.annotation)[1:]
                injectbys = [x for x in metadatas if isinstance(x, InjectBy)]
                if injectbys:
                    return injectbys[0]
            else:
                # create InjectBy for type annotation
                if param.default is Parameter.empty:
                    return InjectBy(param.annotation)
                else:
                    return InjectBy(param.annotation, param.default)

    params_with_injectby = [(p, get_injectby(p)) for p in params]

    if not params:
        return update_wrapper(lambda _: func(), func)

    elif all(p[1] for p in params_with_injectby):
        # all params are annotated with InjectBy(key=...)
        return create_adapter(
            func,
            p_params=[
                cast(InjectBy, p[1]) for p in params_with_injectby
                if p[0].kind == Parameter.POSITIONAL_ONLY],
            k_params={
                p[0].name: cast(InjectBy, p[1]) for p in params_with_injectby
                if p[0].kind != Parameter.POSITIONAL_ONLY}
        )

    elif len(params) == 1:
        arg_0, = params

        if arg_0.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            # does not need to wrap.
            return func

        elif arg_0.kind == inspect.Parameter.KEYWORD_ONLY:
            arg_0_name = arg_0.name
            return update_wrapper(lambda sp: func(**{arg_0_name: sp}), func)

        elif arg_0.kind == inspect.Parameter.VAR_POSITIONAL:
            return update_wrapper(lambda sp: func(sp), func)

        elif arg_0.kind == inspect.Parameter.VAR_KEYWORD:
            return update_wrapper(lambda sp: func(**{'provider': sp}), func)

        else:
            raise ValueError(f'unsupported factory signature: {sign}')

    else:
        raise TypeError('factory has too many parameters.')

def create_adapter(
        func: Callable,
        p_params: Iterable[tuple[Any] | tuple[Any, Any] | InjectBy],
        k_params: Mapping[str, tuple[Any] | tuple[Any, Any] | InjectBy]
    ):

    def to_injectby(arg: tuple[Any] | tuple[Any, Any] | InjectBy):
        if isinstance(arg, tuple):
            if len(arg) not in (1, 2):
                raise ValueError('tuple should contains 1 or 2 elements')
            return InjectBy(*arg)
        elif isinstance(arg, InjectBy):
            return arg
        raise TypeError(f'excepted tuple or InjectBy, got {type(arg)}')

    p_params_i = [to_injectby(v) for v in p_params]
    k_params_i = {k: to_injectby(v) for k, v in k_params.items()}

    def wrapper(ioc):
        return func(
            *(v.get_service(ioc) for v in p_params_i),
            **{k: v.get_service(ioc) for k, v in k_params_i.items()}
        )

    return update_wrapper(wrapper, func)
