# -*- coding: utf-8 -*-
#
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import types
from dataclasses import dataclass
from typing import Type, get_args

from ._primitive_symbol import TypedSymbol


@dataclass(frozen=True, slots=True)
class _NamedTypeListKey:
    '''
    Internal use only.
    '''
    type: 'type | types.GenericAlias'


@dataclass(frozen=True, slots=True)
class NamedType[T]:
    '''
    The NamedType can inject into the `**kwargs`.
    '''
    name: str
    type: Type[T] | types.GenericAlias | types.UnionType

    def __post_init__(self) -> None:
        if not isinstance(self.type, (type, types.GenericAlias, types.UnionType)):
            raise TypeError(self.type)

    def get_types(self) -> 'tuple[type | types.GenericAlias, ...]':
        if isinstance(self.type, types.UnionType):
            return get_args(self.type)
        else:
            return (self.type, )


__all__ = [
    'TypedSymbol',
    'NamedType',
]
