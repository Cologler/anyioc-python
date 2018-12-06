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
    ioc.register_singleton(func.__name__, func)
    return func

def ioc_scoped(func):
    ioc.register_scoped(func.__name__, func)
    return func

def ioc_transient(func):
    ioc.register_transient(func.__name__, func)
    return func

def ioc_singleton_cls(wrap=inject_by_name):
    def wrapper(cls: type):
        wraped_cls = wrap(cls) if wrap else cls
        ioc.register_singleton(cls, wraped_cls)
        ioc.register_singleton(cls.__name__, lambda x: x[cls])
        return cls
    return wrapper

def ioc_scoped_cls(wrap=inject_by_name):
    def wrapper(cls: type):
        wraped_cls = wrap(cls) if wrap else cls
        ioc.register_scoped(cls, wraped_cls)
        ioc.register_scoped(cls.__name__, lambda x: x[cls])
        return cls
    return wrapper

def ioc_transient_cls(wrap=inject_by_name):
    def wrapper(cls: type):
        wraped_cls = wrap(cls) if wrap else cls
        ioc.register_transient(cls, wraped_cls)
        ioc.register_transient(cls.__name__, lambda x: x[cls])
        return cls
    return wrapper

def ioc_bind(new_key):
    '''
    bind with new key.
    '''
    def binding(cls):
        name = cls.__name__
        ioc.register_transient(new_key, lambda x: x[name])
        return cls
    return binding
