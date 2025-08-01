# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import contextlib
import itertools
from typing import Any, Iterable
from unittest.mock import MagicMock

from pytest import raises

from anyioc import IServiceProvider, ServiceNotFoundError, ServiceProvider
from anyioc.symbols import Symbols


def assert_value_is_singleton(providers: Iterable[ServiceProvider], key: Any):
    for left, right in itertools.combinations_with_replacement(providers, 2):
        assert left[key] is right[key]

def assert_value_is_scoped(providers: Iterable[ServiceProvider], key: Any):
    for left, right in itertools.combinations_with_replacement(providers, 2):
        assert (left is right) == (left[key] is right[key])

def assert_value_is_transient(providers: Iterable[ServiceProvider], key: Any):
    for left, right in itertools.combinations_with_replacement(providers, 2):
        assert left[key] is not right[key]


def test_register_singleton():
    root_provider = ServiceProvider()
    with root_provider.scope() as owner_provider:
        owner_provider.register_singleton(1, lambda: object())
        owner_provider.register_singleton(2, lambda ioc: ioc)

        with owner_provider.scope() as scoped_provider:
            with scoped_provider.scope() as child_provider:
                assert_value_is_singleton([owner_provider, scoped_provider, child_provider], 1)
                assert child_provider[2] is owner_provider

def test_register_scoped():
    root_provider = ServiceProvider()
    with root_provider.scope() as owner_provider:
        owner_provider.register_scoped(1, lambda: object())
        owner_provider.register_scoped(2, lambda ioc: ioc)

        with owner_provider.scope() as scoped_provider:
            with scoped_provider.scope() as child_provider:
                assert_value_is_scoped([owner_provider, scoped_provider, child_provider], 1)
                assert child_provider[2] is child_provider

def test_register_transient():
    root_provider = ServiceProvider()
    with root_provider.scope() as owner_provider:
        owner_provider.register_transient(1, lambda: object())
        owner_provider.register_transient(2, lambda ioc: ioc)

        with owner_provider.scope() as scoped_provider:
            with scoped_provider.scope() as child_provider:
                assert_value_is_transient([owner_provider, scoped_provider, child_provider], 1)
                assert child_provider[2] is child_provider

def test_register_group():
    provider = ServiceProvider()
    provider.register_transient('str', lambda: 'name')
    provider.register_transient('int', lambda: 1)
    provider.register_value('float', 1.1)
    group_keys = ['str', 'int']
    provider.register_group('any', group_keys)
    assert provider['any'] == ('name', 1)
    # always transient:
    assert provider['any'] is not provider['any']

    # if we add later, nothing changes:
    group_keys.append('float')
    assert provider['any'] == ('name', 1)

def test_register_value():
    provider = ServiceProvider()

    provider.register_value('k', 'value')
    assert provider['k'] == 'value'

    with provider.register_value('k', 'context_value'):
        assert provider['k'] == 'context_value'

    assert provider['k'] == 'value'

def test_register_bind():
    provider = ServiceProvider()
    provider.register_value('k', 'value')
    provider.register_bind('b', 'k')
    assert provider['b'] == 'value'

def test_get_item_missing_service():
    provider = ServiceProvider()
    provider.register_transient('a', lambda ioc: ioc['b'])
    provider.register_transient('b', lambda ioc: ioc['c'])
    provider.register_transient('c', lambda ioc: ioc['d'])

    with raises(ServiceNotFoundError):
        provider['any']

    with raises(ServiceNotFoundError, match="unknown service: 'd'; resolve chain: 'a'->'b'->'c'->'d'"):
        provider['a']

def test_get_or_def_missing_service():
    assert ServiceProvider().get('any') is None

def test_get_many():
    provider = ServiceProvider()
    provider.register_transient('a', lambda: 1)
    provider.register_transient('a', lambda: 2)
    provider.register_transient('a', lambda: 3)

    assert [3, 2, 1] == provider.get_many('a')

def test_get_many_from_multilevel():
    provider = ServiceProvider()
    provider.register_transient('a', lambda ioc: 10)
    provider.register_transient('a', lambda ioc: 11)

    provider2 = provider.scope()
    provider2.register_transient('a', lambda ioc: 20)
    provider2.register_transient('a', lambda ioc: 21)

    provider3 = provider2.scope()
    provider3.register_transient('a', lambda ioc: 30)
    provider3.register_transient('a', lambda ioc: 31)

    provider4 = provider3.scope()
    provider4.register_transient('a', lambda ioc: 40)
    provider4.register_transient('a', lambda ioc: 41)

    assert [31, 30, 21, 20, 11, 10] == provider3.get_many('a')

def test_get_many_missing_service():
    provider = ServiceProvider()
    assert [] == provider.get_many('a') # wont raise error

def test_resolve():
    provider = ServiceProvider()
    provider.register_value(str, 'v')
    def factory(s: str):
        return s
    assert provider.resolve(factory) == 'v'

def test_resolve_with_follow():
    provider = ServiceProvider()
    provider.register_value(str, 'v')
    class A:
        def __init__(self, s: str) -> None:
            self.s = s
    class B:
        def __init__(self, a: A) -> None:
            self.a = a
    def factory(x: B):
        return x
    b = provider.resolve(factory, follow=True)
    assert b.a.s == 'v'

def test_resolve_with_override_kwargs():
    provider = ServiceProvider()
    provider.register_value(bool, False)

    def func(is_call_from_ioc: bool):
        return is_call_from_ioc

    assert False is provider.resolve(func)
    assert True is provider.resolve(func, kwargs={'is_call_from_ioc': True})

    def kw_only_func(*, is_call_from_ioc: bool):
        return is_call_from_ioc

    assert False is provider.resolve(kw_only_func)
    assert True is provider.resolve(kw_only_func, kwargs={'is_call_from_ioc': True})

def test_enter():
    provider = ServiceProvider()
    callback = MagicMock()
    @contextlib.contextmanager
    def ctx():
        yield
        callback()
    with provider.scope() as scoped:
        scoped.enter(ctx())
        callback.assert_not_called()
    callback.assert_called_once()

def test_predefined_keys():
    map_to_self_keys = (
        # str
        'ioc', 'provider', 'service_provider',
        # type
        ServiceProvider, IServiceProvider,
        # symbol
        Symbols.provider
    )

    provider = ServiceProvider()
    with provider.scope() as s1:
        with provider.scope() as s2:
            with provider.scope() as s3:
                for k in map_to_self_keys:
                    assert_value_is_scoped([provider, s1, s2, s3], k)

def test_scope_types():
    # since scoped is scoped[ServiceProvider]
    provider = ServiceProvider()
    with provider.scope() as scope:
        assert isinstance(scope, ServiceProvider)
