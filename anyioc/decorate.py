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
    __slots__ = ('_service_provider', 'inject_by')

    def __init__(self, service_provider: ScopedServiceProvider):
        self._service_provider = service_provider
        self.inject_by = None

    def _register_with(self, lifetime, target, wraped_target, keys):
        id = object()
        self._service_provider.register(id, wraped_target, lifetime)
        for k in _get_keys(target, keys):
            self._service_provider.register_bind(k, id)

    def singleton(self, factory=None, *, inject_by = None, keys: Optional[Iterable[Any]] = None):
        '''
        a decorator use for register factory.
        factory which should have signature `(ioc) => any` or `() => any`.

        if factory don't have the signature, you need to set `inject_by`.
        `inject_by` is a function that use to convert `factory` signature to `ioc => any`.

        if `inject_by` is None, we will fallback to use `self.inject_by`;
        if `self.inject_by` also be `None`, mean `factory` do not need to convert.

        you can found some `inject_by_*` from `anyioc.utils`.

        if `keys` is not None, it should be a keys list;
        otherwish we will use `factory` and `factory.__name__` (if exists) as keys.
        '''
        def wrapper(target):
            wrapfunc = inject_by or self.inject_by
            wraped_target = wrapfunc(target) if wrapfunc else target
            self._register_with(LifeTime.singleton, target, wraped_target, keys)
            return target

        return wrapper(factory) if factory else wrapper

    def scoped(self, factory=None, *, inject_by = None, keys: Optional[Iterable[Any]] = None):
        '''
        a decorator use for register factory.
        factory which should have signature `(ioc) => any` or `() => any`.

        if factory don't have the signature, you need to set `inject_by`.
        `inject_by` is a function that use to convert `factory` signature to `ioc => any`.

        if `inject_by` is None, we will fallback to use `self.inject_by`;
        if `self.inject_by` also be `None`, mean `factory` do not need to convert.

        you can found some `inject_by_*` from `anyioc.utils`.

        if `keys` is not None, it should be a keys list;
        otherwish we will use `factory` and `factory.__name__` (if exists) as keys.
        '''
        def wrapper(target):
            wraped_target = inject_by(target) if inject_by else target
            self._register_with(LifeTime.scoped, target, wraped_target, keys)
            return target

        return wrapper(factory) if factory else wrapper

    def transient(self, factory=None, *, inject_by = None, keys: Optional[Iterable[Any]] = None):
        '''
        a decorator use for register factory.
        factory which should have signature `(ioc) => any` or `() => any`.

        if factory don't have the signature, you need to set `inject_by`.
        `inject_by` is a function that use to convert `factory` signature to `ioc => any`.

        if `inject_by` is None, we will fallback to use `self.inject_by`;
        if `self.inject_by` also be `None`, mean `factory` do not need to convert.

        you can found some `inject_by_*` from `anyioc.utils`.

        if `keys` is not None, it should be a keys list;
        otherwish we will use `factory` and `factory.__name__` (if exists) as keys.
        '''
        def wrapper(target):
            wraped_target = inject_by(target) if inject_by else target
            self._register_with(LifeTime.transient, target, wraped_target, keys)
            return target

        return wrapper(factory) if factory else wrapper

    def bind(self, new_key, target_key=None):
        '''
        a decorator use for bind class or function to a alias key.

        if `target_key` is `None`, use `__name__` as `target_key`.
        '''
        def binding(target):
            key = target.__name__ if target_key is None else target_key
            self._service_provider.register_bind(new_key, key)
            return target

        return binding
