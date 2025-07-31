# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------


import inspect
from typing import TYPE_CHECKING

from ._primitive_symbol import TypedSymbol

if TYPE_CHECKING:
    from typing import Any  # noqa: F401

    from . import (
        ioc,  # noqa: F401
        ioc_resolver,  # noqa: F401
    )
    from ._internal import LockedMapping, ProviderOptions  # noqa: F401


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
    cache = TypedSymbol['LockedMapping[Any, Any]']('cache')

    # the missing resolver from `IServiceProvider`
    missing_resolver = TypedSymbol['ioc_resolver.ServiceInfoChainResolver']('missing_resolver')

    # get frame info of caller
    caller_frame = TypedSymbol[inspect.FrameInfo]('caller_frame')

    # the options for the `ServiceProvider`, value is a dict like object.
    provider_options = TypedSymbol['ProviderOptions']('provider_options')

    # is current stage of the `IServiceProvider` is initializing
    at_init = TypedSymbol[bool]('at_init')
