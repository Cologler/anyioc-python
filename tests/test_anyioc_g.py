# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from pytest import raises

from anyioc.g import ServiceProvider, _module_scoped_providers, get_module_provider, get_pkgroot_provider, reset
from anyioc.symbols import Symbols


def test_reset():
    reset()
    assert len(_module_scoped_providers) == 0
    assert get_module_provider('A') is not None
    assert get_module_provider('B') is not None
    assert len(_module_scoped_providers) == 2
    reset()
    assert len(_module_scoped_providers) == 0

def test_get_module_provider():
    mp = get_module_provider('A')
    assert isinstance(mp, ServiceProvider)
    assert mp is not get_module_provider('B')
    assert mp is get_module_provider('A')

def test_get_module_provider_without_args():
    mp = get_module_provider()
    assert isinstance(mp, ServiceProvider)
    assert mp is get_module_provider(__name__)
    assert mp is get_module_provider('test_anyioc_g')

def test_get_pkgroot_provider():
    pp = get_pkgroot_provider('A')
    assert isinstance(pp, ServiceProvider)
    assert pp is not get_pkgroot_provider('B')
    assert pp is get_pkgroot_provider('A.B.C')
    assert pp is get_pkgroot_provider('A.C.E')

def test_get_pkgroot_provider_without_args():
    pp = get_pkgroot_provider()
    assert isinstance(pp, ServiceProvider)
    assert pp is get_pkgroot_provider(__name__)
    assert pp is get_pkgroot_provider('test_anyioc_g')

def test_scoped_provider_is_provider_root():
    provider = get_pkgroot_provider('a.b')
    assert provider[Symbols.provider_root] is provider

def test_get_module_provider_auto_conf_ioc():
    provider = get_module_provider('module1')
    assert provider['name'] == '6c660c7f-ff95-46cf-9d24-a92a9489913c'

def test_get_module_provider_args_must_be_string():
    with raises(TypeError):
        get_module_provider(object()) # type: ignore

def test_get_pkgroot_provider_args_must_be_string():
    with raises(TypeError):
        get_pkgroot_provider(object()) # type: ignore
