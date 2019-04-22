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

ioc_decorator = ioc.decorator()

ioc_singleton = ioc_decorator.singleton
ioc_scoped = ioc_decorator.scoped
ioc_transient = ioc_decorator.transient
ioc_singleton_cls = ioc_decorator.singleton_cls
ioc_scoped_cls = ioc_decorator.scoped_cls
ioc_transient_cls = ioc_decorator.transient_cls
ioc_bind = ioc_decorator.bind
