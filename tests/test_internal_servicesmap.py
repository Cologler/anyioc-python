# -*- coding: utf-8 -*-
# 
# Copyright (c) 2023~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

import pytest

from anyioc._servicesmap import ServicesMap

def test_servicesmap_get_many():
    srvmap = ServicesMap()

    key = 1
    item1 = object()
    item2 = object()
    item3 = object()

    srvmap.add(key, item1)
    srvmap.add(key, item2)
    srvmap.add(key, item3)

    assert srvmap.get(key) is item3
    assert list(srvmap.get_many(key)) == [item3, item2, item1]

def test_servicesmap_with_context():
    srvmap = ServicesMap()

    key = 1
    value = object()

    with srvmap.add(key, value):
        assert srvmap.get(key) is value

    assert srvmap.get(key) is None

def test_servicesmap_with_context_release_ordered():
    srvmap = ServicesMap()

    key = 1
    item1 = object()
    item2 = object()
    pop_first = srvmap.add(key, item1)
    srvmap.add(key, item2)
    pop_last = srvmap.add(key, item1)

    assert list(srvmap.get_many(key)) == [item1, item2, item1]
    pop_first()
    with pytest.raises(RuntimeError):
        pop_first()
    assert list(srvmap.get_many(key)) == [item1, item2]
    pop_last()
    assert list(srvmap.get_many(key)) == [item2]

def test_servicesmap_with_context_release_ordered_reversed():
    srvmap = ServicesMap()

    key = 1
    item1 = object()
    item2 = object()
    pop_first = srvmap.add(key, item1)
    srvmap.add(key, item2)
    pop_last = srvmap.add(key, item1)

    assert list(srvmap.get_many(key)) == [item1, item2, item1]
    pop_last()
    with pytest.raises(RuntimeError):
        pop_last()
    assert list(srvmap.get_many(key)) == [item2, item1]
    pop_first()
    assert list(srvmap.get_many(key)) == [item2]

def test_servicesmap_with_context_release_twice_should_raise_error():
    srvmap = ServicesMap()

    with srvmap.add(1, object()) as disposable:
        pass

    with pytest.raises(RuntimeError):
        with disposable:
            pass
