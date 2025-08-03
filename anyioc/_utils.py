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

from ._bases import Factory, IServiceInfo, IServiceProvider, LifeTime, SupportsContext
from ._consts import SERVICEPROVIDER_NAMING_CONVENTION
from ._internal import Disposable, ProviderOptions
from ._service_info import (
    GetGroupServiceInfo,
    GetManyServiceInfo,
    GetOrDefaultServiceInfo,
    LifetimeServiceInfo,
    ProviderServiceInfo,
    ValueServiceInfo,
)
from .annotations import InjectBy, InjectByGroup, InjectWithValue
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
            if callable(self._key):
                return wrap_signature(self._key, follow=True)(provider)
            raise


def get_type_and_metadatas(annotation: Any) -> tuple[Any, tuple[Any, ...]]:
    assert annotation is not Parameter.empty
    if get_origin(annotation) is Annotated:
        args = get_args(annotation)
        return args[0], args[1:]
    else:
        return annotation, ()

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

    def get_injectinfo_from_annotation(metadatas: Iterable[Any]):
        '''
        Get Inject annotation from parameter annotation.
        '''
        if sis := [x for x in metadatas if isinstance(x, (InjectBy, InjectByGroup, InjectWithValue))]:
            if len(sis) > 1:
                _logger.warning('Too many annotated InjectBy')
            return sis[0]

    def get_adapter(param: Parameter) -> IServiceInfo | ParameterAdapter | None:
        if param.kind == Parameter.VAR_KEYWORD:
            return

        elif param.kind == Parameter.VAR_POSITIONAL:
            if param.annotation is not Parameter.empty:
                tp, md = get_type_and_metadatas(param.annotation)
                if ji := get_injectinfo_from_annotation(md):
                    if isinstance(ji, InjectBy):
                        if ji.lifetime != LifeTime.transient:
                            raise RuntimeError('lifetime is invalid for VAR_POSITIONAL parameter.')
                        if ji.has_default():
                            _logger.warning('default is invalid for VAR_POSITIONAL parameter.')
                        return ParameterAdapter(GetManyServiceInfo(ji.key), unpack=True)
                    elif isinstance(ji, InjectByGroup):
                        return ParameterAdapter(GetGroupServiceInfo(ji.keys), unpack=True)
                    elif isinstance(ji, InjectWithValue):
                        return ValueServiceInfo(ji.value)
                    else:
                        raise NotImplementedError

                # create ServiceInfo for type annotation
                return ParameterAdapter(GetManyServiceInfo(tp), unpack=True)

        elif param.annotation is not Parameter.empty:
            tp, md = get_type_and_metadatas(param.annotation)
            if ji := get_injectinfo_from_annotation(md):
                if isinstance(ji, InjectBy):
                    si = GetOrDefaultServiceInfo(ji.key, ji.default)
                    if ji.lifetime != LifeTime.transient:
                        si = LifetimeServiceInfo(service_provider=None, key=None,
                            service_info=si,
                            lifetime=ji.lifetime,
                            scoped_key=ji,
                        )
                    return si
                elif isinstance(ji, InjectWithValue):
                    return ValueServiceInfo(ji.value)
                elif isinstance(ji, InjectByGroup):
                    return GetGroupServiceInfo(ji.keys)
                else:
                    raise NotImplementedError

            # create ServiceInfo for type annotation
            ServiceInfoType = FollowedInjectBy if follow else GetOrDefaultServiceInfo
            if param.default is Parameter.empty:
                return ServiceInfoType(tp)
            else:
                return ServiceInfoType(tp, param.default)

        elif param.name in SERVICEPROVIDER_NAMING_CONVENTION:
            return GetOrDefaultServiceInfo(Symbols.provider)

    param_adapters = [get_adapter(p) for p in params]

    if not params:
        return create_adapter(func)

    elif all(param_adapters):
        # all params are annotated with InjectBy(key=...)
        param_adapters = cast(list[IServiceInfo | ParameterAdapter], param_adapters)
        return create_adapter(
            func,
            p_params=[
                pa for p, pa in zip(params, param_adapters, strict=True)
                if p.kind in (Parameter.POSITIONAL_ONLY, Parameter.VAR_POSITIONAL)
            ],
            k_params={
                p.name: pa for p, pa in zip(params, param_adapters, strict=True)
                if p.kind not in (Parameter.POSITIONAL_ONLY, Parameter.VAR_POSITIONAL)
            },
            override_kwargs=override_kwargs,
        )

    elif len(params) == 1:
        param_0, = params

        if param_0.kind in (Parameter.POSITIONAL_ONLY, Parameter.VAR_POSITIONAL):
            # does not need to wrap.
            return create_adapter(func, p_params=(ProviderServiceInfo.get_singleton_instance(),),
                override_kwargs=override_kwargs)

        elif param_0.kind in (Parameter.KEYWORD_ONLY, Parameter.POSITIONAL_OR_KEYWORD):
            return create_adapter(func, k_params={param_0.name: ProviderServiceInfo.get_singleton_instance()},
                override_kwargs=override_kwargs)

        elif param_0.kind == Parameter.VAR_KEYWORD:
            return create_adapter(func, k_params={'provider': ProviderServiceInfo.get_singleton_instance()},
                override_kwargs=override_kwargs)

        else:
            raise ValueError(f'unsupported factory signature: {sign}')

    else:
        raise TypeError('factory has too many parameters.')


class ParameterAdapter:
    __slots__ = (
        '_service_info',
        '_unpack',
    )

    def __init__(self, service_info: IServiceInfo, *, unpack: bool = False) -> None:
        self._service_info = service_info
        self._unpack = unpack

    def append_args(self, ioc, args: list[Any], /):
        val = self._service_info.get_service(ioc)
        if self._unpack:
            args.extend(val)
        else:
            args.append(val)

    def append_kwargs(self, ioc, name: str, kwargs: dict[str, Any], /):
        kwargs[name] = self._service_info.get_service(ioc)


_EMPTY_P_PARAMS: tuple[ParameterAdapter, ...] = ()
_EMPTY_K_PARAMS: Mapping[str, ParameterAdapter] = {}
_EMPTY_K_ARGS: Mapping[str, Any] = {}

class FactoryAdapter[R](Factory[R]):
    __slots__ = (
        'func',
        'p_params',
        'k_params',
        'origin_func'
    )

    def __init__(self, func: Callable[..., R],
            p_params: Iterable[ParameterAdapter],
            k_params: Mapping[str, ParameterAdapter]
        ) -> None:
        self.func = func
        self.p_params = p_params
        self.k_params = k_params
        self.origin_func = func.func if isinstance(func, FactoryAdapter) else func

    def __call__(self, ioc, /) -> Any:
        if self.p_params:
            args = []
            for param in self.p_params:
                param.append_args(ioc, args)
        else:
            args = ()

        if self.k_params:
            kwargs = {}
            for name, param in self.k_params.items():
                param.append_kwargs(ioc, name, kwargs)
        else:
            kwargs = _EMPTY_K_ARGS

        return self.func(*args, **kwargs)

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
        p_params: Iterable[IServiceInfo | ParameterAdapter] = _EMPTY_P_PARAMS,
        k_params: Mapping[str, IServiceInfo | ParameterAdapter] = _EMPTY_K_PARAMS,
        override_kwargs: Mapping[str, Any] | None = None,
    ) -> Factory[R]:

    def to_parameter_adapter(arg: tuple[Any] | tuple[Any, Any] | IServiceInfo | ParameterAdapter) -> ParameterAdapter:
        if isinstance(arg, ParameterAdapter):
            return arg
        elif isinstance(arg, IServiceInfo):
            return ParameterAdapter(arg)
        elif isinstance(arg, tuple):
            if len(arg) not in (1, 2):
                raise ValueError('tuple should contains 1 or 2 elements')
            return ParameterAdapter(GetOrDefaultServiceInfo(*arg))
        raise TypeError(f'excepted tuple or IServiceInfo, got {type(arg)}')

    if override_kwargs is None:
        override_kwargs = _EMPTY_K_ARGS

    p_params_si = [to_parameter_adapter(v) for v in p_params] if p_params else _EMPTY_P_PARAMS
    k_params_si = {
        k: ParameterAdapter(ValueServiceInfo(override_kwargs[k])) if k in override_kwargs else to_parameter_adapter(v)
        for k, v in k_params.items()
    } if k_params else _EMPTY_K_PARAMS

    return FactoryAdapter(func, p_params_si, k_params_si)


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
