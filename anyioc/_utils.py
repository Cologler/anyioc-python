# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
# the internal utils.
# user should not import anything from this file.
# ----------

import atexit
import contextlib
import inspect
import itertools
import sys
from collections.abc import Iterable, Mapping
from contextlib import suppress
from inspect import Parameter
from logging import getLogger
from types import GeneratorType, MappingProxyType
from typing import Annotated, Any, Callable, NoReturn, cast, get_args, get_origin, override

from ._bases import Factory, IServiceInfo, IServiceProvider, LifeTime, SupportsContext
from ._consts import SERVICEPROVIDER_NAMING_CONVENTION
from ._internal import Disposable, ProviderOptions
from ._service_info import (
    GetGroupServiceInfo,
    GetManyServiceInfo,
    GetOrDefaultServiceInfo,
    GetOrRaisesServiceInfo,
    LifetimeServiceInfo,
    ProviderServiceInfo,
    ServiceInfoProxy,
    ValueServiceInfo,
)
from .annotations import DontInject, InjectBy, InjectByGroup, InjectFrom, InjectWithValue
from .err import ServiceNotFoundError
from .keys import NamedType, _NamedTypeListKey
from .symbols import Symbols

_logger = getLogger(__name__)

def get_module_name(fr: inspect.FrameInfo) -> str:
    '''
    Get module name from frame info
    '''
    mo = inspect.getmodule(fr.frame)
    name = '<stdin>' if mo is None else mo.__name__
    return name

def get_frameinfos(*,
        context: int=1, exclude_anyioc_frames: bool=True
    ) -> list[inspect.FrameInfo]:
    frs = inspect.stack(context=context)[1:] # exclude get_frameinfos
    if exclude_anyioc_frames:
        frs = list(itertools.dropwhile(lambda f: get_module_name(f).partition('.')[0] == 'anyioc', frs))
    return frs

def dispose_at_exit(provider: IServiceProvider) -> Disposable:
    '''
    Register `provider.__exit__()` into `atexit` module.

    Returns a `Disposable` object to unregister and call `provider.__exit__()`.
    '''
    def callback() -> None:
        provider.__exit__(*sys.exc_info())
    def unregister() -> None:
        callback()
        atexit.unregister(callback)
    atexit.register(callback)
    return Disposable(unregister)


class NamedTypeServiceInfoProxy(ServiceInfoProxy[GetOrDefaultServiceInfo | GetOrRaisesServiceInfo]):
    __slots__ = ('_key', '_follow')

    def __init__(self, key: NamedType, service_info: GetOrDefaultServiceInfo | GetOrRaisesServiceInfo, *,
            follow: bool) -> None:
        self._key = key
        super().__init__(service_info)
        self._follow = follow

    @override
    def get_service(self, provider: IServiceProvider) -> object:
        key = self._key
        service_info = self._service_info

        with suppress(ServiceNotFoundError):
            return provider[key] # ignore default

        # fallback to type only.
        try:
            return service_info.get_service_by_key(provider, key.type)
        except ServiceNotFoundError:
            if self._follow:
                return wrap_signature(key.type, follow=True)(provider)
            raise


class DontInjectServiceInfo(IServiceInfo):
    __slots__ = ('_msg')

    def __init__(self, msg: str) -> None:
        super().__init__()
        self._msg = msg

    @override
    def get_service(self, provider: IServiceProvider) -> NoReturn:
        raise TypeError(self._msg)


def get_type_and_metadatas(annotation: object) -> tuple[Any, tuple[Any, ...]]:
    assert annotation is not Parameter.empty
    if get_origin(annotation) is Annotated:
        args = get_args(annotation)
        return args[0], args[1:]
    else:
        return annotation, ()

_PARAMETER_KINDS_SINGLE_VALUE = (
    Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
_PARAMETER_KINDS_POSITIONAL = (
    Parameter.POSITIONAL_ONLY, Parameter.VAR_POSITIONAL)
_PARAMETER_KINDS_KEYWORD = (
    Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY, Parameter.VAR_KEYWORD)

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
        params = [p for p in params if p.kind != Parameter.VAR_KEYWORD or p.annotation is not Parameter.empty]
    if len(params) > 1:
        params = [p for p in params if p.kind != Parameter.VAR_POSITIONAL]

    def get_injectinfo_from_annotation(metadatas: Iterable[Any]) \
            -> DontInject | InjectBy | InjectByGroup | InjectWithValue | InjectFrom | None:
        '''
        Get Inject annotation from parameter annotation.
        '''
        if sis := [x for x in metadatas if isinstance(x, (DontInject, InjectBy, InjectByGroup, InjectWithValue, InjectFrom))]:
            if len(sis) > 1:
                _logger.warning('Too many annotated InjectBy')
            return sis[0]

    def get_adapter(param: Parameter) -> ParameterAdapter | None:

        if param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY):
            try:
                return ParameterAdapter(param.name, ValueServiceInfo(override_kwargs[param.name]))
            except KeyError:
                pass

        if param.annotation is not Parameter.empty:
            tp, md = get_type_and_metadatas(param.annotation)
            ji = get_injectinfo_from_annotation(md)

            def raises_for_parameter() -> NoReturn:
                raise TypeError(f'{type(ji)} is not allowed on {param.kind.name} parameter')

            if param.kind is Parameter.VAR_KEYWORD:
                match ji:
                    case DontInject():
                        return ParameterAdapter(param.name, ValueServiceInfo(DontInject), unpack=True)

                    case None:
                        return ParameterAdapter(param.name, ValueServiceInfo(tp), unpack=True)

                    case _:
                        raises_for_parameter()

            elif param.kind == Parameter.VAR_POSITIONAL:
                match ji:
                    case DontInject():
                        si = ValueServiceInfo(()) # empty args

                    case None:
                        # create ServiceInfo for type annotation
                        si = GetManyServiceInfo(tp)

                    case InjectBy() as jb if jb.has_name():
                        raise ValueError('name is invalid for VAR_POSITIONAL parameter.')

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

                    case InjectWithValue() | InjectFrom():
                        raises_for_parameter()

                    case _:
                        raise NotImplementedError

                return ParameterAdapter(param.name, si, unpack=True)

            else:
                assert param.kind in _PARAMETER_KINDS_SINGLE_VALUE
                match ji:
                    case DontInject():
                        if param.default is Parameter.empty:
                            si = DontInjectServiceInfo(f'Missing required argument: {param!r}')
                        else:
                            si = ValueServiceInfo(param.default)

                    case None:
                        # create ServiceInfo from type annotation
                        key = NamedType(param.name, tp)
                        si = (
                            GetOrRaisesServiceInfo(key) if param.default is Parameter.empty
                            else GetOrDefaultServiceInfo(key, param.default)
                        )
                        si = NamedTypeServiceInfoProxy(key, si, follow=follow)

                    case InjectBy(default=default, lifetime=lifetime) as jb:
                        if jb.has_key():
                            key = jb.key
                        else:
                            assert jb.has_name()
                            key = NamedType(cast(str, jb.name), tp)

                        si = (
                            GetOrDefaultServiceInfo(key, default) if jb.has_default()
                            else GetOrRaisesServiceInfo(key)
                        )

                        if isinstance(key, NamedType):
                            si = NamedTypeServiceInfoProxy(key, si, follow=follow)

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

                    case InjectFrom(func=func, enter_context=enter_context):
                        from ._service_info.extra import TransientServiceInfo
                        si = TransientServiceInfo(func, service_provider=None, key=None, enter_context=enter_context)

                    case _:
                        raise NotImplementedError

                return ParameterAdapter(param.name, si, unpack=False)

        elif param.name in SERVICEPROVIDER_NAMING_CONVENTION and param.kind in _PARAMETER_KINDS_SINGLE_VALUE:
            return ParameterAdapter(param.name, ProviderServiceInfo.get_singleton_instance())

    param_adapters = [get_adapter(p) for p in params]

    if not params:
        return FactoryAdapter(func)

    # auto inject if only single unknown parameter:
    if len([True for x in param_adapters if x is None]) == 1:
        assert None in param_adapters, param_adapters
        index = param_adapters.index(None)
        param = params[index]
        if param.kind in _PARAMETER_KINDS_POSITIONAL:
            # does not need to wrap.
            param_adapters[index] = ParameterAdapter(param.name, ProviderServiceInfo.get_singleton_instance()) # not unpack

        else:
            assert param.kind in _PARAMETER_KINDS_KEYWORD
            param_name = 'provider' if param.kind == Parameter.VAR_KEYWORD else param.name
            try:
                adapter = ParameterAdapter(param_name, ValueServiceInfo(override_kwargs[param_name]))
            except KeyError:
                adapter = ParameterAdapter(param_name, ProviderServiceInfo.get_singleton_instance())
            param_adapters[index] = adapter

    if all(param_adapters):
        # all params are annotated with InjectBy(key=...)
        param_adapters = cast(list[ParameterAdapter], param_adapters)
        return FactoryAdapter(
            func,
            p_params=[
                pa for p, pa in zip(params, param_adapters, strict=True)
                if p.kind in _PARAMETER_KINDS_POSITIONAL
            ],
            k_params={
                pa.param_name: pa for p, pa in zip(params, param_adapters, strict=True)
                if p.kind not in _PARAMETER_KINDS_POSITIONAL
            },
        )

    else:
        raise TypeError('factory has too many parameters.')


class ParameterAdapter:
    __slots__ = (
        'param_name',
        'service_info',
        'unpack',
    )

    def __init__(self, name: str, service_info: IServiceInfo, *, unpack: bool = False) -> None:
        self.param_name = name
        self.service_info = service_info
        self.unpack = unpack

    def append_args(self, ioc: IServiceProvider, args: list[Any], /) -> None:
        val = self.service_info.get_service(ioc)
        if self.unpack: # var args
            args.extend(val)
        else:
            args.append(val)

    def append_kwargs(self, ioc: IServiceProvider, kwargs: dict[str, Any], /) -> None:
        name = self.param_name
        if self.unpack: # var kwargs
            assert type(self.service_info) is ValueServiceInfo
            value = self.service_info._value
            if value is DontInject: # DontInject()
                pass
            else:
                types: list[NamedType] = ioc.get_many(_NamedTypeListKey(self.service_info._value))
                for tp in types:
                    if tp.name not in kwargs:
                        kwargs[tp.name] = ioc[tp]
        else:
            if name not in kwargs: # do not overwrite
                kwargs[name] = self.service_info.get_service(ioc)


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

    def __call__(self, ioc: IServiceProvider, /) -> R:
        with cast(Any, ioc).register_value(Symbols.dependent, self.origin_func):

            if self.p_params:
                args = []
                for param in self.p_params:
                    param.append_args(ioc, args)
            else:
                args = ()

            if self.k_params:
                kwargs = {}
                for param in self.k_params.values():
                    param.append_kwargs(ioc, kwargs)
            else:
                kwargs = _EMPTY_STR_MAPPING

        return self.func(*args, **kwargs)

    def __repr__(self) -> str:
        return f'<Adapter of {self.origin_func!r} at {hex(id(self))}>'


def create_service[T](
        provider: IServiceProvider,
        factory: Factory[T],
        enter_context: bool | None = None,
        options: ProviderOptions | None = None,
    ) -> T:


    service = factory(provider)

    if enter_context is not None:
        if enter_context:
            try:
                service = provider.enter(service) # type: ignore
            except TypeError:
                if inspect.isgenerator(service):
                    service = provider.enter(
                        contextlib.contextmanager(lambda: cast(GeneratorType, service))()
                    )
                else:
                    raise

    else:
        options = provider[Symbols.provider_options] if options is None else options
        if options['auto_enter']:
            wrapped = getattr(factory, 'origin_func', factory)
            # We must ensure that the original object is a ContextManager.
            # If the original object is a factory function and
            # the ContextManager service is merely the return value of that function,
            # then __enter__ should not be called automatically.
            if isinstance(wrapped, SupportsContext) and isinstance(service, SupportsContext):
                service = provider.enter(service)

    return service # type: ignore
