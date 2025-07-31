# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
# the internal utils.
# user should not import anything from this file.
# ----------

import atexit
import inspect
import itertools
import sys
from collections.abc import Iterable, Mapping
from inspect import Parameter
from logging import getLogger
from typing import TYPE_CHECKING, Annotated, Any, Callable, cast, get_args, get_origin

from ._bases import IServiceInfo
from ._internal import Disposable
from .annotations import InjectBy
from .err import ServiceNotFoundError

if TYPE_CHECKING:
    from . import ioc


_logger = getLogger(__name__)

def get_module_name(fr: inspect.FrameInfo):
    '''
    Get module name from frame info
    '''
    mo = inspect.getmodule(fr.frame)
    name = '<stdin>' if mo is None else mo.__name__
    return name

def get_frameinfos(*,
        context: int=1, exclude_anyioc_frames: bool=True
    ):
    frs = inspect.stack(context=context)[1:] # exclude get_frameinfos
    if exclude_anyioc_frames:
        frs = list(itertools.dropwhile(lambda f: get_module_name(f).partition('.')[0] == 'anyioc', frs))
    return frs

def dispose_at_exit(provider):
    '''
    Register `provider.__exit__()` into `atexit` module.

    Returns a `Disposable` object to unregister and call `provider.__exit__()`.
    '''
    def callback():
        provider.__exit__(*sys.exc_info())
    def unregister():
        callback()
        atexit.unregister(callback)
    atexit.register(callback)
    return Disposable(unregister)

def update_wrapper(wrapper, wrapped):
    '''
    update wrapper with internal attributes.
    '''
    wrapper.__anyioc_wrapped__ = getattr(wrapped, '__anyioc_wrapped__', wrapped)
    return wrapper

class FollowedInjectBy(InjectBy):
    def get_service(self, provider: 'ioc.IServiceProvider'):
        try:
            return super().get_service(provider)
        except ServiceNotFoundError:
            if callable(self.key):
                return wrap_signature(self.key, follow=True)(provider)
            raise

def wrap_signature[R](func: Callable[..., R], *, follow: bool=False) -> Callable[['ioc.IServiceProvider'], R]:
    '''
    wrap the function to single argument function.

    unlike the `inject*` series of utils, this is used for implicit convert.
    '''
    from .ioc_service_info import ProviderServiceInfo

    sign = inspect.signature(func)
    params = list(sign.parameters.values())
    if len(params) > 1:
        params = [p for p in params if p.kind != Parameter.VAR_KEYWORD]
    if len(params) > 1:
        params = [p for p in params if p.kind != Parameter.VAR_POSITIONAL]

    def get_injectby(param: Parameter) -> IServiceInfo | None:
        if param.kind in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL):
            return None
        if param.annotation is not Parameter.empty:
            if get_origin(param.annotation) is Annotated:
                metadatas = get_args(param.annotation)[1:]
                if sis := [x for x in metadatas if isinstance(x, IServiceInfo)]:
                    if len(sis) > 1:
                        _logger.warning('Too many annotated InjectBy')
                    return sis[0]
            else:
                # create InjectBy for type annotation
                InjectByType = FollowedInjectBy if follow else InjectBy
                if param.default is Parameter.empty:
                    return InjectByType(param.annotation)
                else:
                    return InjectByType(param.annotation, param.default)

    params_with_injectby = [(p, get_injectby(p)) for p in params]

    if not params:
        return create_adapter(func)

    elif all(p[1] for p in params_with_injectby):
        # all params are annotated with InjectBy(key=...)
        return create_adapter(
            func,
            p_params=[
                cast(InjectBy, p[1]) for p in params_with_injectby
                if p[0].kind == Parameter.POSITIONAL_ONLY
            ],
            k_params={
                p[0].name: cast(InjectBy, p[1]) for p in params_with_injectby
                if p[0].kind != Parameter.POSITIONAL_ONLY
            }
        )

    elif len(params) == 1:
        arg_0, = params

        if arg_0.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD, Parameter.VAR_POSITIONAL):
            # does not need to wrap.
            return create_adapter(func, p_params=(ProviderServiceInfo(),))

        elif arg_0.kind == Parameter.KEYWORD_ONLY:
            return create_adapter(func, k_params={arg_0.name: ProviderServiceInfo()})

        elif arg_0.kind == Parameter.VAR_KEYWORD:
            return create_adapter(func, k_params={'provider': ProviderServiceInfo()})

        else:
            raise ValueError(f'unsupported factory signature: {sign}')

    else:
        raise TypeError('factory has too many parameters.')

_EMPTY_P_PARAMS: tuple[IServiceInfo, ...] = ()
_EMPTY_K_PARAMS: dict[str, IServiceInfo] = {}

def create_adapter[R](
        func: Callable[..., R],
        p_params: Iterable[tuple[Any] | tuple[Any, Any] | IServiceInfo] = _EMPTY_P_PARAMS,
        k_params: Mapping[str, tuple[Any] | tuple[Any, Any] | IServiceInfo] = _EMPTY_K_PARAMS,
    ) -> Callable[['ioc.IServiceProvider'], R]:

    def to_serviceinfo(arg: tuple[Any] | tuple[Any, Any] | IServiceInfo) -> IServiceInfo:
        if isinstance(arg, tuple):
            if len(arg) not in (1, 2):
                raise ValueError('tuple should contains 1 or 2 elements')
            return InjectBy(*arg)
        elif isinstance(arg, IServiceInfo):
            return arg
        raise TypeError(f'excepted tuple or IServiceInfo, got {type(arg)}')

    p_params_i = [to_serviceinfo(v) for v in p_params] if p_params else _EMPTY_P_PARAMS
    k_params_i = {k: to_serviceinfo(v) for k, v in k_params.items()} if k_params else _EMPTY_K_PARAMS

    def wrapper(ioc):
        return func(
            *(v.get_service(ioc) for v in p_params_i),
            **{k: v.get_service(ioc) for k, v in k_params_i.items()}
        )

    return update_wrapper(wrapper, func)
