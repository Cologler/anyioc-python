# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from anyioc.ioc_service_info import (
    ServiceInfo,
    ProviderServiceInfo,
    GroupedServiceInfo,
    BindedServiceInfo,
)

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
