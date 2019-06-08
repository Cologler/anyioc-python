# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import Optional, Iterable, Any

from .utils import inject_by_name
from .ioc import ScopedServiceProvider, LifeTime
from .ioc_service_info import BindedServiceInfo


def _get_keys(target, keys):
    if keys is None:
        keys = []

        try:
            # only hashable() canbe key
            hash(target)
            keys.append(target)
        except TypeError:
            pass

        try:
            name = getattr(target, '__name__')
            keys.append(name)
        except AttributeError:
            pass

    if len(keys) == 0:
        raise RuntimeError('if keys is empty, how do you get it ?')

    return keys



class ServiceProviderDecorator:
    __slots__ = ('_service_provider')

    def __init__(self, service_provider: ScopedServiceProvider):
        self._service_provider = service_provider

    def _register_with(self, lifetime, target, *, keys, inject_by):

        def wrapper(factory):
            nonlocal keys
            id = object()
            keys = _get_keys(factory, keys)
            self._service_provider.register(id, factory, lifetime, inject_by=inject_by)
            for k in keys:
                self._service_provider.register_bind(k, id)
            return factory

        return wrapper(target) if target else wrapper

    def singleton(self, factory=None, *, inject_by = None, keys: Optional[Iterable[Any]] = None):
        '''
        a decorator use for register factory.
        factory which should have signature `(ioc) => any` or `() => any`.

        you can use `inject_by` function to convert `factory` signature to `ioc => any`.
        you can found some `inject_by_*` in `anyioc.utils`.

        if `keys` is not `None`, it should be the keys list;
        otherwish anyioc will use `factory` and `factory.__name__` (if exists) as keys.

        return factory itself.
        '''
        return self._register_with(
            LifeTime.singleton, factory,
            inject_by=inject_by, keys=keys
        )

    def scoped(self, factory=None, *, inject_by = None, keys: Optional[Iterable[Any]] = None):
        '''
        a decorator use for register factory.
        factory which should have signature `(ioc) => any` or `() => any`.

        you can use `inject_by` function to convert `factory` signature to `ioc => any`.
        you can found some `inject_by_*` in `anyioc.utils`.

        if `keys` is not `None`, it should be the keys list;
        otherwish anyioc will use `factory` and `factory.__name__` (if exists) as keys.

        return factory itself.
        '''
        return self._register_with(
            LifeTime.scoped, factory,
            inject_by=inject_by, keys=keys
        )

    def transient(self, factory=None, *, inject_by = None, keys: Optional[Iterable[Any]] = None):
        '''
        a decorator use for register factory.
        factory which should have signature `(ioc) => any` or `() => any`.

        you can use `inject_by` function to convert `factory` signature to `ioc => any`.
        you can found some `inject_by_*` in `anyioc.utils`.

        if `keys` is not `None`, it should be the keys list;
        otherwish anyioc will use `factory` and `factory.__name__` (if exists) as keys.

        return factory itself.
        '''
        return self._register_with(
            LifeTime.transient, factory,
            inject_by=inject_by, keys=keys
        )
