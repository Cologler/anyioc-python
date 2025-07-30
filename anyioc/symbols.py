# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------


from typing import TYPE_CHECKING, Type, get_args, get_type_hints, ForwardRef

if TYPE_CHECKING:
    from . import ioc
    from ._internal import ProviderOptions


class _Symbol:
    '''
    Symbol with description.
    '''

    __slots__ = ('_name', )

    def __init__(self, name: str=''):
        self._name = name

    def __str__(self):
        return f'Symbol({self._name})'

    def __repr__(self):
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

    def __str__(self):
        ta = self._get_type_args()
        tn = ta.__forward_arg__ if isinstance(ta, ForwardRef) else ta.__name__
        return f'TypedSymbol[{tn}]({self._name})'

    def __repr__(self):
        ta = self._get_type_args()
        tn = repr(ta) if isinstance(ta, ForwardRef) else ta.__name__
        return f'TypedSymbol[{tn}]({self._name!r})'

    def _get_type_args(self) -> Type[T]:
        if (oc := getattr(self, '__orig_class__', None)) is not None:
            return get_args(oc)[0]
        raise TypeError('TypedSymbol is created without type args')

    def get_type(self):
        '''
        Get the type of this symbol
        '''
        if not hasattr(self, '_type'):
            self._type = self._get_type_args()
        return self._type


class Symbols:
    '''
    the symbols use for ioc.

    this keys are predefined in `ServiceProvider`.
    overwrite this keys will break the expected behavior.
    '''

    # current scoped `IServiceProvider`
    provider = TypedSymbol['ioc.ServiceProvider']('provider')

    # the root `IServiceProvider`
    provider_root = TypedSymbol['ioc.ServiceProvider']('provider_root')

    # the parent of current `IServiceProvider`
    provider_parent = TypedSymbol['ioc.ServiceProvider']('provider_parent')

    # the cache dict to store scoped instances
    cache = TypedSymbol[dict]('cache')

    # the missing resolver from `IServiceProvider`
    missing_resolver = _Symbol('missing_resolver')

    # get frame info of caller
    caller_frame = _Symbol('caller_frame')

    # the options for the `ServiceProvider`, value is a dict like object.
    provider_options = TypedSymbol['ProviderOptions']('provider_options')

    # is current stage of the `IServiceProvider` is initializing
    at_init = TypedSymbol[bool]('at_init')
