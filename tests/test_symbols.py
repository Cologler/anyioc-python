# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import inspect
from pytest import raises

from anyioc import ServiceProvider
from anyioc.symbols import Symbols

def test_symbol_caller_frame():
    provider = ServiceProvider()
    fr = provider[Symbols.caller_frame]
    mo = inspect.getmodule(fr.frame)
    assert mo.__name__ == 'test_symbols'

def test_symbol_caller_frame_from_deep():
    provider = ServiceProvider()
    def get_name(ioc):
        fr = ioc[Symbols.caller_frame]
        mo = inspect.getmodule(fr.frame)
        return mo.__name__
    provider.register_transient('name', get_name)
    assert provider['name'] == 'test_symbols'

def _create_scopes(provider: ServiceProvider, count: int=5):
    providers = [provider]
    for i in range(0, count):
        providers.append(providers[-1].scope())
    return providers

def test_symbol_provider_root():
    root_provider = ServiceProvider()
    providers = _create_scopes(root_provider)
    for provider in providers:
        assert provider[Symbols.provider_root] is root_provider

def test_symbol_provider_root_get_many():
    providers = _create_scopes(ServiceProvider())
    for provider in providers:
        assert len(provider.get_many(Symbols.provider_root)) == 1

def test_symbol_provider_parent_for_root_provider():
    assert ServiceProvider()[Symbols.provider_parent] is None

def test_symbol_provider_parent_for_child_provider():
    providers = _create_scopes(ServiceProvider())
    for parent_index, provider in enumerate(providers[1:]):
        assert provider[Symbols.provider_parent] is providers[parent_index]

def test_symbol_provider_parent_get_many():
    providers = _create_scopes(ServiceProvider())
    for provider in providers:
        assert len(provider.get_many(Symbols.provider_parent)) == 1

def test_symbol_cache():
    providers = _create_scopes(ServiceProvider())
    for provider in providers:
        assert isinstance(provider[Symbols.cache], dict)

def test_symbol_cache_get_many():
    providers = _create_scopes(ServiceProvider())
    for provider in providers:
        assert len(provider.get_many(Symbols.cache)) == 1
