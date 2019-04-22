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

_decorator = ioc.decorator()

ioc_singleton = _decorator.singleton
ioc_scoped = _decorator.scoped
ioc_transient = _decorator.transient
ioc_singleton_cls = _decorator.singleton_cls
ioc_scoped_cls = _decorator.scoped_cls
ioc_transient_cls = _decorator.transient_cls
ioc_bind = _decorator.bind
