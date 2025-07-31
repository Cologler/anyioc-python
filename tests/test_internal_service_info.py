# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import pytest

from anyioc import ServiceProvider
from anyioc._service_info import BindedServiceInfo, GetAttrServiceInfo, LifeTime, ProviderServiceInfo, ServiceInfo, ValueServiceInfo
from anyioc.symbols import Symbols


def test_service_info():
    other_kwargs = {
        'service_provider': ServiceProvider(),
        'key': 'test-key',
        'lifetime': LifeTime.transient,
    }

    # without parameters
    si = ServiceInfo(factory=lambda: 15, **other_kwargs)
    assert si.get_service(other_kwargs['service_provider']) == 15

    # with one parameter
    si = ServiceInfo(factory=lambda _: 15, **other_kwargs)
    assert si.get_service(other_kwargs['service_provider']) == 15

    # with one keyword parameter
    si = ServiceInfo(factory=lambda *, sr2fe: 15, **other_kwargs)
    assert si.get_service(other_kwargs['service_provider']) == 15

@pytest.mark.parametrize('key', [
    Symbols.cache,
    Symbols.provider_options
])
def test_service_info_not_allowed_keys(key):
    service_provider = ServiceProvider()
    with pytest.raises(ValueError):
        ServiceInfo(service_provider, key, lambda: None, LifeTime.transient)

def test_value_serviceinfo_repr():
    assert repr(ValueServiceInfo('value')) == "<(_) => 'value'>"

def test_provider_service_info():
    sp = ServiceProvider()
    si = ProviderServiceInfo()
    assert sp is si.get_service(sp)

def test_binded_serviceinfo():
    sp = ServiceProvider()
    sp.register_value(1, 2)
    sp.register_value(3, 4)
    sp.register_value(5,6)
    si = BindedServiceInfo(3)
    assert si.get_service(sp) == 4

def test_binded_serviceinfo_repr():
    assert repr(BindedServiceInfo('fromkey')) == "<(ioc) => ioc['fromkey']>"

def test_getattr_serviceinfo_repr():
    assert repr(GetAttrServiceInfo('name')) == "<(ioc) => getattr(ioc, 'name')>"
    assert repr(GetAttrServiceInfo('name', 'default')) == "<(ioc) => getattr(ioc, 'name', 'default')>"
