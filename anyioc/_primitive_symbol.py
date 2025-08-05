# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import ForwardRef, Type, get_args

# symbol is primitive type, import any modules from . is not allowed.


class _Symbol:
    '''
    Symbol with description.
    '''

    __slots__ = ('_name', )

    def __init__(self, name: str='') -> None:
        self._name = name

    def __str__(self) -> str:
        return f'Symbol({self._name})'

    def __repr__(self) -> str:
        return f'Symbol({self._name!r})'


class TypedSymbol[T](_Symbol):
    '''
    Symbol with type.

    Must use `TypedSymbol[int](...)` instead of `TypedSymbol(...)` directly.
    '''

    __slots__ = (
        '__orig_class__',
        '_type', # for cached property
    )

    def __str__(self) -> str:
        ta = self._get_type_args()
        tn = ta.__forward_arg__ if isinstance(ta, ForwardRef) else ta.__name__
        return f'TypedSymbol[{tn}]({self._name})'

    def __repr__(self) -> str:
        ta = self._get_type_args()
        tn = repr(ta) if isinstance(ta, ForwardRef) else ta.__name__
        return f'TypedSymbol[{tn}]({self._name!r})'

    def _get_type_args(self) -> Type[T]:
        if (oc := getattr(self, '__orig_class__', None)) is not None:
            return get_args(oc)[0]
        raise TypeError('TypedSymbol is created without type args')

    def get_type(self) -> type:
        '''
        Get the type of this symbol
        '''
        if not hasattr(self, '_type'):
            self._type = self._get_type_args()
        return self._type
