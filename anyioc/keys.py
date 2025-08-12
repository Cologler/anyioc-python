# -*- coding: utf-8 -*-
#
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import types
from dataclasses import dataclass
from typing import Type, cast, get_args

from ._primitive_symbol import TypedSymbol


@dataclass(frozen=True, slots=True)
class _NamedTypeListKey:
    '''
    Internal use only.
    '''
    type: type


@dataclass(frozen=True, slots=True)
class NamedType[T]:
    '''
    The NamedType can inject into the `**kwargs`.
    '''
    name: str
    type: Type[T]
    is_optional: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.type, (type, types.GenericAlias)):
            raise TypeError(self.type)

    @staticmethod
    def create(name: str, type_: object) -> 'NamedType':
        is_optional = False
        if isinstance(type_, types.UnionType):
            union_types = get_args(type_)
            required_types = [x for x in union_types if x not in (None, types.NoneType)]
            if len(required_types) == 1 and len(union_types) > 1:
                type_ = union_types[0]
                is_optional = True
        return NamedType(name, cast(type, type_), is_optional=is_optional)


__all__ = [
    'TypedSymbol',
    'NamedType',
]
