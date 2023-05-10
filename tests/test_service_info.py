# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import pytest

from anyioc import ServiceProvider
from anyioc.ioc_service_info import (
    BindedServiceInfo,
    GroupedServiceInfo,
    LifeTime,
    ProviderServiceInfo,
    ServiceInfo
)
from anyioc.symbols import Symbols


def test_service_info():
    other_kwargs = {
        'service_provider': ServiceProvider(),
        'key': 'test-key',
        'lifetime': LifeTime.transient,
    }

    # without parameters
    si = ServiceInfo(factory=lambda: 15, **other_kwargs)
    assert si.get(other_kwargs['service_provider']) == 15

    # with one parameter
    si = ServiceInfo(factory=lambda _: 15, **other_kwargs)
    assert si.get(other_kwargs['service_provider']) == 15

    # with one keyword parameter
    si = ServiceInfo(factory=lambda *, sr2fe: 15, **other_kwargs)
    assert si.get(other_kwargs['service_provider']) == 15

@pytest.mark.parametrize('key', [
    Symbols.cache,
    Symbols.provider_options
])
def test_service_info_not_allowed_keys(key):
    service_provider = ServiceProvider()
    with pytest.raises(ValueError):
        ServiceInfo(service_provider, key, lambda: None, LifeTime.transient)

def test_provider_service_info():
    src = {}
    si = ProviderServiceInfo()
    assert src is si.get(src)

def test_grouped_service_info():
    src = {1: 2, 3: 4, 5: 6}
    group = []
    si = GroupedServiceInfo(group)

    ret = si.get(src)
    assert isinstance(ret, tuple)
    assert ret == ()

    group.append(1)
    ret = si.get(src)
    assert isinstance(ret, tuple)
    assert ret == (2, )

    group.append(3)
    ret = si.get(src)
    assert isinstance(ret, tuple)
    assert ret == (2, 4)

def test_binded_service_info():
    src = {1: 2, 3: 4, 5: 6}
    si = BindedServiceInfo(3)
    assert si.get(src) == 4
