# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from .utils import inject_by_name
from .ioc import ScopedServiceProvider

class ServiceProviderDecorator:
    __slots__ = ('_service_provider')

    def __init__(self, service_provider: ScopedServiceProvider):
        self._service_provider = service_provider

    def singleton(self, func):
        '''
        a decorator use for register function which should have signature `(ioc) => any` or `() => any`.

        you can get the return value from ServiceProvider with key: `func.__name__`
        '''
        self._service_provider.register_singleton(func.__name__, func)
        return func

    def scoped(self, func):
        '''
        a decorator use for register function which should have signature `(ioc) => any` or `() => any`.

        you can get the return value from ServiceProvider with key: `func.__name__`
        '''
        self._service_provider.register_scoped(func.__name__, func)
        return func

    def transient(self, func):
        '''
        a decorator use for register function which should have signature `(ioc) => any` or `() => any`.

        you can get the return value from ServiceProvider with key: `func.__name__`
        '''
        self._service_provider.register_transient(func.__name__, func)
        return func

    def singleton_cls(self, cls=None, *, inject_by=inject_by_name):
        '''
        a decorator use for register class. the `class()` will wrap by `inject_by`.

        you can get instance from ServiceProvider with key: `cls` or `cls.__name__`
        '''
        def wrapper(cls: type):
            wraped_cls = inject_by(cls) if inject_by else cls
            self._service_provider.register_singleton(cls, wraped_cls)
            self._service_provider.register_singleton(cls.__name__, lambda x: x[cls])
            return cls

        return wrapper(cls) if cls else wrapper

    def scoped_cls(self, cls=None, *, inject_by=inject_by_name):
        '''
        a decorator use for register class. the `class()` will wrap by `inject_by`.

        you can get instance from ServiceProvider with key: `cls` or `cls.__name__`
        '''
        def wrapper(cls: type):
            wraped_cls = inject_by(cls) if inject_by else cls
            self._service_provider.register_scoped(cls, wraped_cls)
            self._service_provider.register_scoped(cls.__name__, lambda x: x[cls])
            return cls

        return wrapper(cls) if cls else wrapper

    def transient_cls(self, cls=None, *, inject_by=inject_by_name):
        '''
        a decorator use for register class. the `class()` will wrap by `inject_by`.

        you can get instance from ServiceProvider with key: `cls` or `cls.__name__`
        '''
        def wrapper(cls: type):
            wraped_cls = inject_by(cls) if inject_by else cls
            self._service_provider.register_transient(cls, wraped_cls)
            self._service_provider.register_transient(cls.__name__, lambda x: x[cls])
            return cls

        return wrapper(cls) if cls else wrapper

    def bind(self, new_key):
        '''
        a decorator use for bind class or function to a alias key.
        '''
        def binding(cls_or_func):
            name = cls_or_func.__name__
            self._service_provider.register_bind(new_key, name)
            return cls_or_func
        return binding
