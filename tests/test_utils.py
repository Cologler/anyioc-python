# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------


from anyioc.ioc import ServiceProvider
from anyioc.utils import (
    get_logger,
    get_scope_depth,
    is_root,
)


def test_helper_get_logger():
    provider = ServiceProvider()
    provider.register_transient('logger', get_logger)
    logger = provider['logger']
    assert logger.name == __name__
    assert logger.name == 'test_utils'

def test_is_root():
    provider = ServiceProvider()
    assert is_root(provider)
    with provider.scope() as scoped:
        assert not is_root(scoped)

def test_get_scope_depth():
    root = ServiceProvider()
    assert get_scope_depth(root) == 0
    with root.scope() as s1:
        assert get_scope_depth(s1) == 1
        with s1.scope() as s2:
            assert get_scope_depth(s2) == 2
