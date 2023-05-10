# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------


class _Symbol:
    'a symbol _Symbol with description'

    __slots__ = ('_name', )

    def __init__(self, name=''):
        self._name = name

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f'Symbol({self._name})'


class Symbols:
    '''
    the symbols use for ioc.

    this keys are predefined in `ServiceProvider`.
    overwrite this keys will break the expected behavior.
    '''

    # current scoped `IServiceProvider`
    provider = _Symbol('provider')

    # the root `IServiceProvider`
    provider_root = _Symbol('provider_root')

    # the parent of current `IServiceProvider`
    provider_parent = _Symbol('provider_parent')

    # the cache dict to store scoped instances
    cache = _Symbol('cache')

    # the missing resolver from `IServiceProvider`
    missing_resolver = _Symbol('missing_resolver')

    # get frame info of caller
    caller_frame = _Symbol('caller_frame')

    # the options for the `ServiceProvider`, value is a dict like object.
    provider_options = _Symbol('provider_options')

    # is current stage of the `IServiceProvider` is initializing
    at_init = _Symbol('at_init')
