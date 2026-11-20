# -*- coding: utf-8 -*-
# 
# Copyright (c) 2023~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from threading import Event

import pytest

from anyioc._servicesmap import ServicesMap


def test_servicesmap_get_many() -> None:
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

def test_servicesmap_with_context() -> None:
    srvmap = ServicesMap()

    key = 1
    value = object()

    with srvmap.add(key, value):
        assert srvmap.get(key) is value

    assert srvmap.get(key) is None

def test_servicesmap_with_context_release_ordered() -> None:
    srvmap = ServicesMap()

    key = 1
    item1 = object()
    item2 = object()
    pop_first = srvmap.add(key, item1)
    srvmap.add(key, item2)
    pop_last = srvmap.add(key, item1)

    assert list(srvmap.get_many(key)) == [item1, item2, item1]
    pop_first()
    assert list(srvmap.get_many(key)) == [item1, item2]
    pop_last()
    assert list(srvmap.get_many(key)) == [item2]

def test_servicesmap_with_context_release_ordered_reversed() -> None:
    srvmap = ServicesMap()

    key = 1
    item1 = object()
    item2 = object()
    pop_first = srvmap.add(key, item1)
    srvmap.add(key, item2)
    pop_last = srvmap.add(key, item1)

    assert list(srvmap.get_many(key)) == [item1, item2, item1]
    pop_last()
    assert list(srvmap.get_many(key)) == [item2, item1]
    pop_first()
    assert list(srvmap.get_many(key)) == [item2]

def test_servicesmap_with_context_release_multi_times_should_ok() -> None:
    srvmap = ServicesMap()

    with srvmap.add(1, object()) as disposable:
        pass
    with disposable:
        pass
    with disposable:
        pass

def test_servicesmap_freeze() -> None:
    srvmap = ServicesMap()

    srvmap.add(1, object())

    srvmap.freeze_key(1)
    srvmap.freeze_key(2)

    with pytest.raises(RuntimeError):
        srvmap.add(1, object())
    with pytest.raises(RuntimeError):
        srvmap.add(2, object())


@pytest.mark.parametrize('use_lock', [False, True])
def test_scope_shares_ancestor_layers_and_uses_its_own_lock_setting(use_lock: bool) -> None:
    root = ServicesMap[int, str]({1: [('root',)]})
    parent = root.scope()
    scope = parent.scope(use_lock=use_lock)
    started = Event()

    def read() -> str:
        started.set()
        return scope[1]

    assert scope._layers[1] is parent._layers[0]
    assert scope._layers[2] is root._layers[0]
    assert isinstance(parent._layers[0].lock, nullcontext)
    assert isinstance(scope._layers[0].lock, nullcontext) is (not use_lock)

    with ThreadPoolExecutor(max_workers=1) as executor:
        with root._layers[0].lock:
            reader = executor.submit(read)
            assert started.wait(timeout=5)
            with pytest.raises(TimeoutError):
                reader.result(timeout=0.05)

        assert reader.result(timeout=5) == 'root'


def test_resolve_keeps_a_snapshot_without_holding_the_layer_lock() -> None:
    root = ServicesMap[int, str]()
    remove_old = root.add(1, 'old')
    root.add(1, 'new')
    values = root.scope().resolve(1)
    assert next(values) == 'new'

    with ThreadPoolExecutor(max_workers=1) as executor:
        writer = executor.submit(remove_old)
        try:
            writer.result(timeout=5)
            assert list(values) == ['old']
        finally:
            values.close()

    assert root.get_many(1) == ['new']
