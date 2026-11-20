# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from logging import Logger

from anyioc import LifeTime
from anyioc._service_info import FactoryServiceInfo
from anyioc.ioc import ServiceProvider
from anyioc.utils import (
    debug_ioc,
    get_logger,
    get_scope_depth,
    is_root,
)


def test_get_logger() -> None:
    provider = ServiceProvider()
    provider.register_transient('logger', get_logger)
    logger = provider['logger']
    assert isinstance(logger, Logger)
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


def test_debug_ioc_follows_registration_order() -> None:
    def fail_if_called() -> None:
        raise AssertionError('Debugging should not initialize the provider or resolve factories.')

    with ServiceProvider() as root, root.scope() as scoped:
        root.register_value('service', 'root')
        root.register_service_info('factory', FactoryServiceInfo(lambda _: fail_if_called()))
        scoped.register_value('service', 'older')
        scoped.register_value('service', 'newer')
        root.add_init_hook(fail_if_called)

        lines = debug_ioc(scoped).splitlines()

    assert lines[:4] == [
        'Scope (depth 1)',
        "  'service': <(_) => 'newer'>",
        "  'service': <(_) => 'older'>",
        'Root',
    ]
    assert "  'service': <(_) => 'root'>" in lines
    assert any(line.startswith("  'factory':") for line in lines)


def test_debug_ioc_includes_factory_group_and_bind_registrations() -> None:
    def factory() -> None:
        raise AssertionError('Debugging should not resolve factories.')

    ioc = ServiceProvider()
    ioc.register('explicit', factory, LifeTime.scoped)
    ioc.register_singleton('singleton', factory)
    ioc.register_scoped('scoped', factory)
    ioc.register_transient('transient', factory)
    ioc.register_group('group', ('singleton', 'transient'))
    ioc.register_group('single_member_group', ('singleton',))
    ioc.register_group('empty_group', ())
    ioc.register_bind('alias', 'singleton')

    output = debug_ioc(ioc)
    print(output)
    lines = output.splitlines()

    for key, lifetime in (
        ('explicit', LifeTime.scoped),
        ('singleton', LifeTime.singleton),
        ('scoped', LifeTime.scoped),
        ('transient', LifeTime.transient),
    ):
        assert any(
            line.startswith(f'  {key!r}: <{lifetime} service from ') and repr(factory) in line
            for line in lines
        )

    assert "  'group': <(ioc) => (ioc['singleton'], ioc['transient'])>" in lines
    assert "  'single_member_group': <(ioc) => (ioc['singleton'],)>" in lines
    assert "  'empty_group': <(ioc) => ()>" in lines
    assert "  'alias': <(ioc) => ioc['singleton']>" in lines
