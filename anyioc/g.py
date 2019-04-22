# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# a global ioc
# ----------

from functools import partial

from .ioc import ServiceProvider
from .utils import inject_by_name, dispose_at_exit

ioc = ServiceProvider()
dispose_at_exit(ioc)

ioc_decorator = ioc.decorator()

ioc_singleton = ioc_decorator.singleton
ioc_scoped = ioc_decorator.scoped
ioc_transient = ioc_decorator.transient
ioc_singleton_cls = partial(ioc_decorator.singleton, inject_by=inject_by_name)
ioc_scoped_cls = partial(ioc_decorator.scoped, inject_by=inject_by_name)
ioc_transient_cls = partial(ioc_decorator.transient, inject_by=inject_by_name)
ioc_bind = ioc_decorator.bind
