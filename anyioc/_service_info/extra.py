# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

import inspect
from typing import Any, Callable, override

from .._bases import IServiceInfo, IServiceProvider, LifeTime
from .._utils import create_service, get_frameinfos, wrap_signature
from ..symbols import Symbols
from . import LifetimeServiceInfo


class TransientServiceInfo[T](IServiceInfo[T]):
    __slots__ = (
        '_factory', '_factory_origin',
        # options
        '_options',
    )

    _NOT_ALLOWED_KEYS = frozenset([
        Symbols.provider_options,
    ])

    def __init__(self, service_provider: IServiceProvider, key: Any, factory: Callable[..., T]):
        if key in self._NOT_ALLOWED_KEYS:
            raise ValueError(f'Key {key!r} is not allowed')

        self._factory_origin = factory
        self._factory = wrap_signature(factory)
        self._options = service_provider[Symbols.provider_options]

    def __repr__(self) -> str:
        return f'<Service from {self._factory_origin!r}>'

    @override
    def get_service(self, provider: IServiceProvider) -> T:
        return create_service(provider, self._factory, options=self._options)


def create_lifetime_service_info[T](
        service_provider: IServiceProvider, key: Any, factory: Callable[..., T], lifetime: LifeTime
    ):
    base_service_info = TransientServiceInfo(
        service_provider=service_provider,
        key=key,
        factory=factory
    )
    return LifetimeServiceInfo(
        service_provider=service_provider,
        key=key,
        service_info=base_service_info,
        lifetime=lifetime
    )


class CallerFrameServiceInfo(IServiceInfo[inspect.FrameInfo | None]):
    'a `IServiceInfo` use for get caller frameinfo'

    __slots__ = ()

    @override
    def get_service(self, provider: IServiceProvider):
        for f in get_frameinfos(exclude_anyioc_frames=True):
            return f
