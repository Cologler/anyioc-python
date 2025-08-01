# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
# the internal utils.
# user should not import anything from this file.
# ----------

import atexit
import inspect
import io
import itertools
import sys
from collections.abc import Iterable, Mapping
from inspect import Parameter
from logging import getLogger
from typing import Annotated, Any, Callable, cast, get_args, get_origin

from ._bases import Factory, IServiceInfo, IServiceProvider, SupportsContext
from ._consts import SERVICEPROVIDER_NAMING_CONVENTION
from ._internal import Disposable, ProviderOptions
from ._service_info import (
    GetManyServiceInfo,
    GetOrDefaultServiceInfo,
    LifetimeServiceInfo,
    ProviderServiceInfo,
    ValueServiceInfo,
)
from .annotations import InjectBy
from .err import ServiceNotFoundError
from .symbols import Symbols

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


class FollowedInjectBy(GetOrDefaultServiceInfo):
    def get_service(self, provider: IServiceProvider):
        try:
            return super().get_service(provider)
        except ServiceNotFoundError:
            if callable(self.key):
                return wrap_signature(self.key, follow=True)(provider)
            raise

class UnpackingServiceInfo[T](IServiceInfo[T]):
    __slots__ = (
        'service_info',
    )

    def __init__(self, service_info: IServiceInfo[Iterable[T]]):
        self.service_info = service_info

    def get_service(self, provider):
        raise NotImplementedError

    def get_packed_services(self, provider):
        return tuple(self.service_info.get_service(provider))

def wrap_signature[R](func: Callable[..., R], *,
        follow: bool = False,
        override_kwargs: Mapping[str, Any] | None = None,
    ) -> Factory[R]:
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

    def get_serviceinfo_from_annotation(annotation: Any, default: Any) -> IServiceInfo | None:
        if get_origin(annotation) is Annotated:
            metadatas = get_args(annotation)[1:]
            if sis := [x for x in metadatas if isinstance(x, IServiceInfo)]:
                if len(sis) > 1:
                    _logger.warning('Too many annotated InjectBy')
                return sis[0]

    def get_serviceinfo(param: Parameter) -> IServiceInfo | None:
        if param.kind == Parameter.VAR_KEYWORD:
            return

        elif param.kind == Parameter.VAR_POSITIONAL:
            if param.annotation is not Parameter.empty:
                if si := get_serviceinfo_from_annotation(param.annotation, param.default):
                    if isinstance(si, InjectBy):
                        if isinstance(si._service_info, LifetimeServiceInfo):
                            raise RuntimeError('lifetime is invalid for VAR_POSITIONAL parameter.')
                        else:
                            god = si._service_info
                        assert isinstance(god, GetOrDefaultServiceInfo)
                        if god.has_default():
                            _logger.warning('default is invalid for VAR_POSITIONAL parameter.')
                        return UnpackingServiceInfo(GetManyServiceInfo(god.key))
                    return si

                # create ServiceInfo for type annotation
                return UnpackingServiceInfo(GetManyServiceInfo(param.annotation))

        elif param.annotation is not Parameter.empty:
            if si := get_serviceinfo_from_annotation(param.annotation, param.default):
                return si

            # create ServiceInfo for type annotation
            ServiceInfoType = FollowedInjectBy if follow else GetOrDefaultServiceInfo
            if param.default is Parameter.empty:
                return ServiceInfoType(param.annotation)
            else:
                return ServiceInfoType(param.annotation, param.default)

        elif param.name in SERVICEPROVIDER_NAMING_CONVENTION:
            return GetOrDefaultServiceInfo(Symbols.provider)

    params_with_serviceinfo = [(p, get_serviceinfo(p)) for p in params]

    if not params:
        return create_adapter(func)

    elif all(p[1] for p in params_with_serviceinfo):
        # all params are annotated with InjectBy(key=...)
        return create_adapter(
            func,
            p_params=[
                cast(IServiceInfo, p[1]) for p in params_with_serviceinfo
                if p[0].kind in (Parameter.POSITIONAL_ONLY, Parameter.VAR_POSITIONAL)
            ],
            k_params={
                p[0].name: cast(IServiceInfo, p[1]) for p in params_with_serviceinfo
                if p[0].kind not in (Parameter.POSITIONAL_ONLY, Parameter.VAR_POSITIONAL)
            },
            override_kwargs=override_kwargs,
        )

    elif len(params) == 1:
        arg_0, = params

        if arg_0.kind in (Parameter.POSITIONAL_ONLY, Parameter.VAR_POSITIONAL):
            # does not need to wrap.
            return create_adapter(func, p_params=(ProviderServiceInfo.get_singleton_instance(),),
                override_kwargs=override_kwargs)

        elif arg_0.kind in (Parameter.KEYWORD_ONLY, Parameter.POSITIONAL_OR_KEYWORD):
            return create_adapter(func, k_params={arg_0.name: ProviderServiceInfo.get_singleton_instance()},
                override_kwargs=override_kwargs)

        elif arg_0.kind == Parameter.VAR_KEYWORD:
            return create_adapter(func, k_params={'provider': ProviderServiceInfo.get_singleton_instance()},
                override_kwargs=override_kwargs)

        else:
            raise ValueError(f'unsupported factory signature: {sign}')

    else:
        raise TypeError('factory has too many parameters.')


_EMPTY_P_PARAMS: tuple[IServiceInfo, ...] = ()
_EMPTY_K_PARAMS: Mapping[str, IServiceInfo] = {}
_EMPTY_K_ARGS: Mapping[str, Any] = {}

class Adapter[R](Factory[R]):
    __slots__ = (
        'func',
        'p_params',
        'k_params',
        'origin_func'
    )

    def __init__(self, func: Callable[..., R],
            p_params: Iterable[IServiceInfo],
            k_params: Mapping[str, IServiceInfo]
        ) -> None:
        self.func = func
        self.p_params = p_params
        self.k_params = k_params
        self.origin_func = func.func if isinstance(func, Adapter) else func

    def __call__(self, ioc, /) -> Any:
        return self.func(
            *(v for si in self.p_params for v in si.get_packed_services(ioc)),
            **{k: v.get_service(ioc) for k, v in self.k_params.items()}
        )

    def __str__(self) -> str:
        out = io.StringIO()
        self.write_str(out)
        return out.getvalue()

    def write_str(self, out: io.StringIO,
            *, init_indent: str = '',
            level_indent: str = '  '):

        level = 0
        def write(s: str):
            out.write(init_indent)
            out.write(level_indent * level + s)

        write(f'{self.func}(\n')
        level += 1

        for i, s in enumerate(self.p_params):
            write(f'args.{i} = {s},\n')

        for k, s in self.k_params.items():
            write(f'{k} = {s},\n')

        level -= 1
        write(')')


def create_adapter[R](
        func: Callable[..., R],
        p_params: Iterable[tuple[Any] | tuple[Any, Any] | IServiceInfo] = _EMPTY_P_PARAMS,
        k_params: Mapping[str, tuple[Any] | tuple[Any, Any] | IServiceInfo] = _EMPTY_K_PARAMS,
        override_kwargs: Mapping[str, Any] | None = None,
    ) -> Factory[R]:

    def to_serviceinfo(arg: tuple[Any] | tuple[Any, Any] | IServiceInfo) -> IServiceInfo:
        if isinstance(arg, tuple):
            if len(arg) not in (1, 2):
                raise ValueError('tuple should contains 1 or 2 elements')
            return GetOrDefaultServiceInfo(*arg)
        elif isinstance(arg, IServiceInfo):
            return arg
        raise TypeError(f'excepted tuple or IServiceInfo, got {type(arg)}')

    if override_kwargs is None:
        override_kwargs = _EMPTY_K_ARGS

    p_params_si = [to_serviceinfo(v) for v in p_params] if p_params else _EMPTY_P_PARAMS
    k_params_si = {
        k: ValueServiceInfo(override_kwargs[k]) if k in override_kwargs else to_serviceinfo(v)
        for k, v in k_params.items()
    } if k_params else _EMPTY_K_PARAMS

    return Adapter(func, p_params_si, k_params_si)


def create_service[T](
        provider: IServiceProvider,
        factory: Factory[T],
        options: ProviderOptions | None = None,
    ) -> T:

    options = provider[Symbols.provider_options] if options is None else options

    service = factory(provider)
    if options['auto_enter']:
        wrapped = getattr(factory, 'origin_func', factory)
        # We must ensure that the original object is a ContextManager.
        # If the original object is a factory function and
        # the ContextManager service is merely the return value of that function,
        # then __enter__ should not be called automatically.
        if isinstance(wrapped, SupportsContext) and isinstance(service, SupportsContext):
            service = provider.enter(service)
    return service # type: ignore
