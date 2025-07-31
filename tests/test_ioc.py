# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import contextlib
import itertools
from unittest.mock import MagicMock
from typing import Iterable, Any

from anyioc import IServiceProvider, ServiceProvider
from anyioc.symbols import Symbols


def assert_value_is_singleton(providers: Iterable[ServiceProvider], key: Any):
    for left, right in itertools.combinations_with_replacement(providers, 2):
        assert left.get(key) is right.get(key)

def assert_value_is_scoped(providers: Iterable[ServiceProvider], key: Any):
    for left, right in itertools.combinations_with_replacement(providers, 2):
        assert (left is right) == (left.get(key) is right.get(key))

def assert_value_is_transient(providers: Iterable[ServiceProvider], key: Any):
    for left, right in itertools.combinations_with_replacement(providers, 2):
        assert left.get(key) is not right.get(key)


def test_singleton():
    provider = ServiceProvider()
    provider.register_singleton(1, lambda: object())
    with provider.scope() as s1:
        with provider.scope() as s2:
            with provider.scope() as s3:
                assert_value_is_singleton([provider, s1, s2, s3], 1)

def test_scope():
    provider = ServiceProvider()
    provider.register_scoped(1, lambda: object())
    with provider.scope() as s1:
        with provider.scope() as s2:
            with provider.scope() as s3:
                assert_value_is_scoped([provider, s1, s2, s3], 1)

def test_transient():
    provider = ServiceProvider()
    provider.register_transient(1, lambda: object())
    with provider.scope() as s1:
        with provider.scope() as s2:
            with provider.scope() as s3:
                assert_value_is_transient([provider, s1, s2, s3], 1)

def test_group():
    provider = ServiceProvider()
    provider.register_transient('str', lambda: 'name')
    provider.register_transient('int', lambda: 1)
    provider.register_value('float', 1.1)
    group_keys = ['str', 'int']
    provider.register_group('any', group_keys)
    assert provider['any'] == ('name', 1)
    # always transient:
    assert provider['any'] is not provider['any']
    # allow to add later
    group_keys.append('float')
    # nothing changes:
    assert provider['any'] == ('name', 1)

def test_value():
    provider = ServiceProvider()

    provider.register_value('k', 'value')
    assert provider['k'] == 'value'

    with provider.register_value('k', 'context_value'):
        assert provider['k'] == 'context_value'

    assert provider['k'] == 'value'

def test_bind():
    provider = ServiceProvider()
    provider.register_value('k', 'value')
    provider.register_bind('b', 'k')
    assert provider['b'] == 'value'

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
