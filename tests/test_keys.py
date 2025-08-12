# -*- coding: utf-8 -*-
# 
# Copyright (c) 2025~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from unittest.mock import MagicMock

from pytest import raises

from anyioc import ServiceNotFoundError, ServiceProvider
from anyioc.keys import NamedType


def test_named_key_register_and_dispose() -> None:
    provider = ServiceProvider()
    disposable = provider.register_value(NamedType('name1', int), 1)
    assert provider.get_many(NamedType('name1', int)) == [1]
    disposable()
    assert provider.get_many(NamedType('name1', int)) == []

def test_named_key_for_kwargs() -> None:
    provider = ServiceProvider()

    def func_with_1_kwargs(name1: int) -> int:
        return name1

    with raises(ServiceNotFoundError):
        provider.resolve(func_with_1_kwargs)

    provider.register_value(int, 0)
    assert provider.resolve(func_with_1_kwargs) == 0

    provider.register_value(NamedType('name1', int), 1)
    assert provider.resolve(func_with_1_kwargs) == 1

    provider.register_value(int, 4)
    assert provider.resolve(func_with_1_kwargs) == 1, 'perfer named type'

    def func_with_2_kwargs(name1: int, name2: int) -> tuple[int, int]:
        return name1, name2

    provider.register_value(NamedType('name2', int), 2)
    assert provider.resolve(func_with_2_kwargs) == (1, 2)

def test_named_key_for_var_kwargs() -> None:
    provider = ServiceProvider()

    def func_with_var_kwargs(**kwargs: int) -> dict[str, int]:
        return kwargs

    assert provider.resolve(func_with_var_kwargs) == {}

    provider.register_value(NamedType('name1', int), 1)
    provider.register_value(NamedType('name2', int), 2)
    assert provider.resolve(func_with_var_kwargs) == {
        'name1': 1,
        'name2': 2
    }

def test_named_key_for_any_kwargs_with_override_keywords() -> None:
    returns_1 = MagicMock(return_value=1)
    returns_2 = MagicMock(return_value=2)

    provider = ServiceProvider()
    provider.register_transient(NamedType('name1', int), returns_1)
    provider.register_transient(NamedType('name2', int), returns_2)

    def func_with_any_kwargs(
            name1,  # noqa: ANN001 Missing type annotation
            **kwargs: int
        ) -> tuple[object, dict[str, int]]:
        return name1, kwargs

    assert provider.resolve(func_with_any_kwargs) == (provider, { 'name2': 2 }), \
        '`name1` is injected as ServiceProvider.'

    # only resolved factories are called:
    returns_1.assert_not_called()
    returns_2.assert_called_once()

    def func_with_annotated_keyword_and_kwargs(
            name1: int,  # noqa: ANN001 Missing type annotation
            **kwargs: int
        ) -> tuple[object, dict[str, int]]:
        return name1, kwargs

    assert provider.resolve(func_with_annotated_keyword_and_kwargs) == (1, { 'name2': 2 }), \
        '`name1` is injected from NamedType.'

    returns_1.assert_called_once()
    assert returns_2.call_count == 2
