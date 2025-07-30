# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from . import ioc  # noqa: F401


class InjectBy:
    _UNSET = object()

    def __init__(self, key: Any, default: Any=_UNSET) -> None:
        self.key = key
        self.default = default

    def get_service(self, provider: 'ioc.IServiceProvider'):
        if self.default is self._UNSET:
            return provider[self.key]
        else:
            return provider.get(self.key, self.default)
