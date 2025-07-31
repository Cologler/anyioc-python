# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from abc import ABC, abstractmethod

class IServiceInfo[T](ABC):
    __slots__ = ()

    @abstractmethod
    def get_service(self, provider, /) -> T:
        raise NotImplementedError
