# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from logging import Logger

from anyioc.ioc import ServiceProvider
from anyioc.utils import (
    get_logger,
    get_scope_depth,
    is_root,
)


def test_get_logger() -> None:
    provider = ServiceProvider()
    provider.register_transient('logger', get_logger)
    logger: Logger = provider['logger']
    assert logger.name == __name__
    assert logger.name == 'test_utils'

def test_get_logger_from_external_module() -> None:
    provider = ServiceProvider()
    provider.register_transient(Logger, get_logger)

    from module2 import LoggerDependentClass, loggerDependentFunc

    class_logger = provider.resolve(LoggerDependentClass).logger
    assert class_logger.name == 'module2.LoggerDependentClass'

    func_logger = provider.resolve(loggerDependentFunc)
    assert func_logger.name == 'module2.loggerDependentFunc'

    # bool params should not inject into the function:
    provider.register_value(bool, True)
    assert provider.resolve(loggerDependentFunc).name == 'module2.loggerDependentFunc'

def test_get_logger_from_external_module_with_module_name_only() -> None:
    provider = ServiceProvider()
    provider.register_transient(Logger, get_logger(module_name_only=True))

    from module2 import LoggerDependentClass, loggerDependentFunc

    class_logger = provider.resolve(LoggerDependentClass).logger
    assert class_logger.name == 'module2'

    func_logger = provider.resolve(loggerDependentFunc)
    assert func_logger.name == 'module2'


def test_is_root() -> None:
    provider = ServiceProvider()
    assert is_root(provider)
    with provider.scope() as scoped:
        assert not is_root(scoped)

def test_get_scope_depth() -> None:
    root = ServiceProvider()
    assert get_scope_depth(root) == 0
    with root.scope() as s1:
        assert get_scope_depth(s1) == 1
        with s1.scope() as s2:
            assert get_scope_depth(s2) == 2
