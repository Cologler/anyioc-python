# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# a global ioc
# ----------

from .ioc import ServiceProvider
from .utils import inject_by_name, dispose_at_exit

ioc = ServiceProvider()
dispose_at_exit(ioc)

def ioc_singleton(func):
    '''
    a decorator use for register function which should have signature `(ioc) => any`.

    you can get the return value from `ioc` with key: `func.__name__`
    '''
    ioc.register_singleton(func.__name__, func)
    return func

def ioc_scoped(func):
    '''
    a decorator use for register function which should have signature `(ioc) => any`.

    you can get the return value from `ioc` with key: `func.__name__`
    '''
    ioc.register_scoped(func.__name__, func)
    return func

def ioc_transient(func):
    '''
    a decorator use for register function which should have signature `(ioc) => any`.

    you can get the return value from `ioc` with key: `func.__name__`
    '''
    ioc.register_transient(func.__name__, func)
    return func

def ioc_singleton_cls(cls=None, *, inject_by=inject_by_name):
    '''
    a decorator use for register class which should have signature `(ioc) => any`.

    you can get instance from `ioc` with key: `cls` or `cls.__name__`
    '''
    def wrapper(cls: type):
        wraped_cls = inject_by(cls) if inject_by else cls
        ioc.register_singleton(cls, wraped_cls)
        ioc.register_singleton(cls.__name__, lambda x: x[cls])
        return cls

    return wrapper(cls) if cls else wrapper

def ioc_scoped_cls(cls=None, *, inject_by=inject_by_name):
    '''
    a decorator use for register class which should have signature `(ioc) => any`.

    you can get instance from `ioc` with key: `cls` or `cls.__name__`
    '''
    def wrapper(cls: type):
        wraped_cls = inject_by(cls) if inject_by else cls
        ioc.register_scoped(cls, wraped_cls)
        ioc.register_scoped(cls.__name__, lambda x: x[cls])
        return cls

    return wrapper(cls) if cls else wrapper

def ioc_transient_cls(cls=None, *, inject_by=inject_by_name):
    '''
    a decorator use for register class which should have signature `(ioc) => any`.

    you can get instance from `ioc` with key: `cls` or `cls.__name__`
    '''
    def wrapper(cls: type):
        wraped_cls = inject_by(cls) if inject_by else cls
        ioc.register_transient(cls, wraped_cls)
        ioc.register_transient(cls.__name__, lambda x: x[cls])
        return cls

    return wrapper(cls) if cls else wrapper

def ioc_bind(new_key):
    '''
    a decorator use for bind class or function to a alias key.
    '''
    def binding(cls):
        name = cls.__name__
        ioc.register_transient(new_key, lambda x: x[name])
        return cls
    return binding
