# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import pytest
from pytest import raises

from anyioc import ServiceProvider, LifeTime
from anyioc.utils_conf import BadConfError, load_conf

def from_conf(conf: dict):
    provider = ServiceProvider()
    load_conf(provider, conf)
    return provider

class A:
    'a example class'
    def __init__(self, gerju: int):
        super().__init__()
        self.gerju = gerju
        self.enter = None

    def __enter__(self):
        self.enter = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.enter = False

def test_when_conf_is_not_a_dict():
    with raises(TypeError) as excinfo:
        from_conf([])
    assert excinfo.value.args[0] == "conf is not a dict."

def test_load_conf_with_services_dict():
    provider = from_conf({
        'services': {
            'fsdnj': dict(
                factory=A,
                inject_by='name'
            ),
            'fqufe': dict(
                factory=f'{__name__}:A',
                inject_by='anno',
                lifetime='singleton'
            ),
            'fjndau': dict(
                factory=dict(module=__name__, name='A'),
                enter=True,
                lifetime=LifeTime.scoped
            )
        }
    })
    provider.register_value('gerju', 155)
    provider.register_value(int, 455)

    with provider:
        fsdnj = provider['fsdnj']
        fqufe = provider['fqufe']
        fjndau = provider['fjndau']
        assert isinstance(fsdnj, A)
        assert isinstance(fqufe, A)
        assert isinstance(fjndau, A)
        assert fsdnj.gerju == 155
        assert fqufe.gerju == 455
        assert isinstance(fjndau.gerju, ServiceProvider)
        assert fsdnj.enter is None
        assert fqufe.enter is None
        assert fjndau.enter is True
    assert fjndau.enter is False

def test_load_conf_with_services_list():
    provider = from_conf({
        'services': [
            dict(
                key='fsdnj',
                factory=A,
                inject_by='name'
            ),
            dict(
                key='fhua',
                factory=A,
                inject_by=dict(
                    gerju=int
                )
            )
        ]
    })
    provider.register_value('gerju', 155)
    provider.register_value(int, 455)

    fsdnj = provider['fsdnj']
    assert isinstance(fsdnj, A)
    assert fsdnj.gerju == 155

    fhua = provider['fhua']
    assert isinstance(fhua, A)
    assert fhua.gerju == 455

def test_load_conf_with_services_dict_when_key_conflict():
    with raises(BadConfError) as excinfo:
        from_conf(dict(
            services={
                'fjndau': dict(
                    key='dasdas'
                )
            }
        ))
    assert excinfo.value.args[0] == "</services['fjndau']> already contains another key: 'dasdas'."

def test_services_when_factory_is_a_random_str():
    with raises(BadConfError) as excinfo:
        from_conf(dict(
            services={
                'fjndau': dict(
                    factory='dasdas'
                )
            }
        ))
    assert excinfo.value.args[0] == "</services['fjndau']/factory> should be a `module-name:callable-name` like str."

def test_services_when_factory_module_is_not_a_str():
    with raises(BadConfError) as excinfo:
        from_conf(dict(
            services={
                'fjndau': dict(
                    factory=dict(module=14, name='djsau')
                )
            }
        ))
    assert excinfo.value.args[0] == "</services['fjndau']/factory/module> is not a str."

def test_services_when_factory_name_is_not_a_str():
    with raises(BadConfError) as excinfo:
        from_conf(dict(
            services={
                'fjndau': dict(
                    factory=dict(module=__name__, name=15)
                )
            }
        ))
    assert excinfo.value.args[0] == "</services['fjndau']/factory/name> is not a str."

def test_services_when_factory_is_not_a_str():
    with raises(BadConfError) as excinfo:
        from_conf(dict(
            services={
                'fjndau': dict(
                    factory=15
                )
            }
        ))
    assert excinfo.value.args[0] == "</services['fjndau']/factory> is not either str or dict."

def test_services_when_factory_module_unable_import():
    with raises(BadConfError) as excinfo:
        from_conf(dict(
            services={
                'fjndau': dict(
                    factory=f'djashfiaushfuia:not_callable'
                )
            }
        ))
    assert excinfo.value.args[0] == "</services['fjndau']/factory>: unable import module 'djashfiaushfuia'."

def test_services_when_factory_module_has_no_such_attr():
    with raises(BadConfError) as excinfo:
        from_conf(dict(
            services={
                'fjndau': dict(
                    factory=f'{__name__}:djashfiaushfuia'
                )
            }
        ))
    assert excinfo.value.args[0] == "</services['fjndau']/factory>: no such attr 'djashfiaushfuia' on module 'test_utils_conf'."


not_callable = object()

def test_services_when_factory_is_not_a_callable():
    with raises(BadConfError) as excinfo:
        from_conf(dict(
            services={
                'fjndau': dict(
                    factory=f'{__name__}:not_callable'
                )
            }
        ))
    assert excinfo.value.args[0] == "</services['fjndau']/factory> is not a callable."

def test_services_when_inject_by_is_invaild():
    with raises(BadConfError) as excinfo:
        from_conf(dict(
            services={
                'fjndau': dict(
                    inject_by='dsadsa',
                    factory=from_conf
                )
            }
        ))
    assert excinfo.value.args[0] == "value of </services['fjndau']/inject_by> ('dsadsa') is not one of (anno, inject_by_anno, name, inject_by_name)."

def test_services_when_lifetime_is_invaild():
    with raises(BadConfError) as excinfo:
        from_conf(dict(
            services={
                'fjndau': dict(
                    lifetime='fett',
                    factory=from_conf
                )
            }
        ))
    assert excinfo.value.args[0] == "value of </services['fjndau']/lifetime> ('fett') is not one of (transient, scoped, singleton)."

def test_load_conf_with_values_dict():
    provider = from_conf({
        'values': {
            'k': 'v'
        }
    })
    assert provider['k'] == 'v'

def test_load_conf_with_values_list():
    provider = from_conf({
        'values': [
            {
                'key': 'k',
                'value': 'v'
            }, {
                'key': 'mod-pytest',
                'value': 'pytest',
                'ref': True,
            }, {
                'key': 'obj-pytest.raises',
                'value': 'pytest:raises',
                'ref': True,
            }, {
                'key': 'obj-sp',
                'value': 'anyioc:ServiceProvider',
                'ref': True,
            }
        ]
    })
    assert provider['k'] == 'v'
    assert provider['mod-pytest'] is pytest
    assert provider['obj-pytest.raises'] == raises
    assert provider['obj-sp'] is ServiceProvider

def test_load_conf_with_binds_dict():
    provider = from_conf({
        'binds': {
            'dsaju': 'fansio'
        }
    })
    provider.register_value('fansio', 'gnis')
    assert provider['dsaju'] == 'gnis'

def test_load_conf_with_binds_list():
    provider = from_conf({
        'binds': [
            dict(key='akfw', target='kdsa')
        ]
    })
    provider.register_value('kdsa', 'dsafa')
    assert provider['akfw'] == 'dsafa'

def test_load_conf_with_groups_dict():
    provider = from_conf({
        'groups': {
            'fask': ['fansio', 'geo']
        }
    })
    provider.register_value('fansio', 'gnis')
    provider.register_value('geo', 'egwg')
    assert provider['fask'] == ('gnis', 'egwg')

def test_load_conf_with_groups_list():
    provider = from_conf({
        'groups': [
            dict(key='fasfa', keys=['fansio', 'geo'])
        ]
    })
    provider.register_value('fansio', 'gnis')
    provider.register_value('geo', 'egwg')
    assert provider['fasfa'] == ('gnis', 'egwg')

def test_load_conf_with_groups_list_with_item_is_not_a_list():
    with raises(BadConfError) as excinfo:
        from_conf(dict(
            groups=[
                dict(key='fasfa', keys=['fansio', 'geo']),
                dict(key='fsdgfg', keys=[]),
                dict(key='asfa', keys=object())
            ]
        ))
    assert excinfo.value.args[0] == '</groups[2]/keys> is not a list.'
