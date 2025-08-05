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
from types import MappingProxyType
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
from .annotations import InjectBy, InjectByGroup, InjectFrom, InjectWithValue
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

    if override_kwargs is None:
        override_kwargs = _EMPTY_STR_MAPPING

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
        if sis := [x for x in metadatas if isinstance(x, (InjectBy, InjectByGroup, InjectWithValue, InjectFrom))]:
            if len(sis) > 1:
                _logger.warning('Too many annotated InjectBy')
            return sis[0]

    def get_adapter(param: Parameter) -> ParameterAdapter | None:
        if param.kind == Parameter.VAR_KEYWORD:
            return

        if param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY):
            try:
                return ParameterAdapter(ValueServiceInfo(override_kwargs[param.name]))
            except KeyError:
                pass

        if param.annotation is not Parameter.empty:
            if param.kind == Parameter.VAR_POSITIONAL:
                tp, md = get_type_and_metadatas(param.annotation)
                match get_injectinfo_from_annotation(md):

                    case None:
                        # create ServiceInfo for type annotation
                        si = GetManyServiceInfo(tp)

                    case InjectBy(key, _, lifetime=lifetime) as jb:
                        if jb.has_default():
                            _logger.warning('default is invalid for VAR_POSITIONAL parameter.')
                        si = GetManyServiceInfo(key)
                        if lifetime != LifeTime.transient:
                            si = LifetimeServiceInfo(service_provider=None, key=None,
                                service_info=si,
                                lifetime=lifetime,
                                scoped_key=jb,
                            )

                    case InjectByGroup(keys):
                        si = GetGroupServiceInfo(keys)

                    case InjectWithValue() | InjectFrom() as rj:
                        raise TypeError(f'{type(rj)} is not allowed on VAR_POSITIONAL parameter')

                    case _:
                        raise NotImplementedError

                return ParameterAdapter(si, unpack=True)

            else:
                tp, md = get_type_and_metadatas(param.annotation)
                match get_injectinfo_from_annotation(md):
                    case None:
                        # create ServiceInfo for type annotation
                        ServiceInfoType = FollowedInjectBy if follow else GetOrDefaultServiceInfo
                        si = (
                            ServiceInfoType(tp) if param.default is Parameter.empty
                            else ServiceInfoType(tp, param.default)
                        )

                    case InjectBy(key, default, lifetime=lifetime) as jb:
                        si = GetOrDefaultServiceInfo(key, default)
                        if lifetime != LifeTime.transient:
                            si = LifetimeServiceInfo(service_provider=None, key=None,
                                service_info=si,
                                lifetime=lifetime,
                                scoped_key=jb,
                            )

                    case InjectWithValue(value):
                        si = ValueServiceInfo(value)

                    case InjectByGroup(keys):
                        si = GetGroupServiceInfo(keys)

                    case InjectFrom(func=func):
                        from ._service_info.extra import TransientServiceInfo
                        si = TransientServiceInfo(func, service_provider=None, key=None)

                    case _:
                        raise NotImplementedError

                return ParameterAdapter(si, unpack=False)

        elif param.name in SERVICEPROVIDER_NAMING_CONVENTION:
            return _GET_PROVIDER_PARAM_ADAPTER

    param_adapters = [get_adapter(p) for p in params]

    if not params:
        return FactoryAdapter(func)

    elif all(param_adapters):
        # all params are annotated with InjectBy(key=...)
        param_adapters = cast(list[ParameterAdapter], param_adapters)
        return FactoryAdapter(
            func,
            p_params=[
                pa for p, pa in zip(params, param_adapters, strict=True)
                if p.kind in (Parameter.POSITIONAL_ONLY, Parameter.VAR_POSITIONAL)
            ],
            k_params={
                p.name: pa for p, pa in zip(params, param_adapters, strict=True)
                if p.kind not in (Parameter.POSITIONAL_ONLY, Parameter.VAR_POSITIONAL)
            },
        )

    elif len(params) == 1:
        param_0, = params

        if param_0.kind in (Parameter.POSITIONAL_ONLY, Parameter.VAR_POSITIONAL):
            # does not need to wrap.
            return FactoryAdapter(func, p_params=(_GET_PROVIDER_PARAM_ADAPTER,))

        elif param_0.kind in (Parameter.KEYWORD_ONLY, Parameter.POSITIONAL_OR_KEYWORD, Parameter.VAR_KEYWORD):
            param_name = 'provider' if param_0.kind == Parameter.VAR_KEYWORD else param_0.name
            try:
                adapter = ParameterAdapter(ValueServiceInfo(override_kwargs[param_name]))
            except KeyError:
                adapter = _GET_PROVIDER_PARAM_ADAPTER
            return FactoryAdapter(func, k_params={param_name: adapter})

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

_GET_PROVIDER_PARAM_ADAPTER = ParameterAdapter(ProviderServiceInfo.get_singleton_instance())

_EMPTY_STR_MAPPING: Mapping[str, Any] = MappingProxyType({})

class FactoryAdapter[R](Factory[R]):
    __slots__ = (
        'func',
        'p_params',
        'k_params',
        'origin_func'
    )

    def __init__(self, func: Callable[..., R],
            p_params: Iterable[ParameterAdapter] = (),
            k_params: Mapping[str, ParameterAdapter] = _EMPTY_STR_MAPPING,
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
            kwargs = _EMPTY_STR_MAPPING

        return self.func(*args, **kwargs)

    def __repr__(self) -> str:
        return f'<Adapter of {self.origin_func!r} at {hex(id(self))}>'


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
