# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from importlib import import_module

from .ioc import ServiceProvider
from .ioc_service_info import LifeTime
from .builder import inject_by_table
from .utils import inject_by_keys


class BadConfError(Exception):
    '''
    raise when the conf dict was incorrect.
    '''

def _iter_list_with_path(path: str, l: list):
    'yield a (path, item) tuple from list.'
    for i, v in enumerate(l):
        yield f'{path}[{i!r}]', v

def _iter_dict_with_path(path: str, d: dict):
    'yield a (path, key, value) tuple from dict.'
    for k, v in d.items():
        yield f'{path}[{k!r}]', k, v

def _ensure_is_dict(path: str, obj, fields=()):
    if not isinstance(obj, dict):
        raise BadConfError(f'<{path}> must be a dict.')
    if fields:
        for field in fields:
            if field not in obj:
                raise BadConfError(f'<{path}> miss {field!r} field.')

def _factory_getattr_from_module(path: str, mod, fullname: str):
    names = fullname.split('.')
    assert names
    if not all(n for n in names):
        raise BadConfError(f'name of <{path}> contain empty part.')
    try:
        attr = mod
        for name in names:
            attr = getattr(attr, name)
        return attr
    except AttributeError:
        raise BadConfError(f'<{path}>: no such attr {fullname!r} on module {mod.__name__!r}.')

class _ConfLoader:
    def __init__(self, provider: ServiceProvider):
        super().__init__()
        self.provider = provider

    def load_conf(self, conf: dict):
        if not isinstance(conf, dict):
            raise TypeError('conf is not a dict.')

        self._on_services('/services', conf.get('services'))
        self._on_values('/values', conf.get('values'))
        self._on_groups('/groups', conf.get('groups'))
        self._on_binds('/binds', conf.get('binds'))

    def _on_services(self, path: str, services):
        if not services:
            return

        if isinstance(services, dict):
            for p, k, v in _iter_dict_with_path(path, services):
                _ensure_is_dict(p, v)
                key = v.get('key', k)
                if key != k:
                    raise BadConfError(f'<{p}> already contains another key: {key!r}.')
                self._on_service_item(p, v, k)
        elif isinstance(services, list):
            for p, v in _iter_list_with_path(path, services):
                _ensure_is_dict(p, v, ('key', ))
                self._on_service_item(p, v, v['key'])
        else:
            raise BadConfError(f'<{path}> is not either dict or list.')

    def _on_service_item(self, path: str, service_conf: dict, key):
        service_conf = service_conf.copy() # ensure we did not modify the origin dict

        # factory
        factory = service_conf.pop('factory', None)
        if factory is None:
            raise BadConfError(f'<{path}/factory> is null, which is required.')
        elif callable(factory):
            # conf was create in python process instead read from a conf file
            pass
        else:
            if isinstance(factory, str):
                # parse like console_scripts
                parts = factory.split(':')
                if len(parts) != 2:
                    raise BadConfError(
                        f'value of <{path}/factory> should be a `module-name:callable-name` like str.')
                factory_module_name, factory_name = parts
            elif isinstance(factory, dict):
                factory = factory.copy()
                factory_module_name = factory.pop('module', None)
                if not isinstance(factory_module_name, str):
                    raise BadConfError(f'value of <{path}/factory/module> should be a str.')
                factory_name = factory.pop('name', None)
                if not isinstance(factory_name, str):
                    raise BadConfError(f'value of <{path}/factory/name> should be a str.')
            else:
                raise BadConfError(f'value of <{path}/factory> is not either str or dict.')

            if not factory_module_name:
                raise BadConfError(f'value of <{path}/factory/module> is empty.')
            if not factory_name:
                raise BadConfError(f'value of <{path}/factory/name> is empty.')

            try:
                mod = import_module(factory_module_name)
            except ImportError:
                raise BadConfError(f'<{path}/factory> required a unable import module `{factory_module_name}`.')
            factory = _factory_getattr_from_module(f'{path}/factory', mod, factory_name)
            if not callable(factory):
                raise BadConfError(f'<{path}/factory> is not a callable.')

        # lifetime
        lifetime = service_conf.pop('lifetime', LifeTime.transient)
        if isinstance(lifetime, LifeTime):
            pass
        else:
            if not isinstance(lifetime, str) or lifetime not in LifeTime.__members__:
                one_of = ', '.join(LifeTime.__members__)
                raise BadConfError(
                    f'value of <{path}/lifetime> ({lifetime!r}) is not one of ({one_of}).')
            lifetime = LifeTime.__members__[lifetime]

        # inject_by
        inject_by = service_conf.pop('inject_by', None)
        if inject_by is not None:
            if callable(inject_by):
                # conf was create in python process instead read from a conf file
                pass
            elif isinstance(inject_by, str):
                try:
                    inject_by_decorator = inject_by_table[inject_by]
                except (TypeError, KeyError):
                    # maybe `inject_by` is unhashable.
                    inject_by_decorator = None
                if inject_by_decorator is None:
                    one_of = ', '.join(inject_by_table)
                    raise BadConfError(
                        f'value of <{path}/inject_by> ({inject_by!r}) is not one of ({one_of}).')
                inject_by = inject_by_decorator
            elif isinstance(inject_by, dict):
                keys = {}
                for name in inject_by:
                    if not isinstance(name, str):
                        raise BadConfError(
                            f'key of <{path}/inject_by> must be str.')
                inject_by = inject_by_keys(**inject_by.copy())
            else:
                raise BadConfError(f'<{path}/inject_by> is not either str or dict.')
            factory = inject_by(factory)

        # enter
        enter = bool(service_conf.pop('enter', False))

        # register
        def service_factory(ioc: ServiceProvider):
            obj = factory(ioc)
            if enter:
                ioc.enter(obj)
            return obj

        self.provider.register(key, service_factory, lifetime)

    def _on_values(self, path: str, values):
        if not values:
            return

        if isinstance(values, dict):
            for k, v in values.items():
                self.provider.register_value(k, v)
        elif isinstance(values, list):
            fields = ('key', 'value')
            for p, conf in _iter_list_with_path(path, values):
                _ensure_is_dict(p, conf, fields)
                values = [conf[f] for f in fields]
                self.provider.register_value(*values)
        else:
            raise BadConfError(f'<{path}> is not either dict or list.')

    def _on_groups(self, path: str, groups):
        if not groups:
            return

        if isinstance(groups, dict):
            for k, v in groups.items():
                if not isinstance(v, list):
                    raise BadConfError(f'value of <{path}[{k!r}]> is not a list.')
                self.provider.register_group(k, v)
        elif isinstance(groups, list):
            fields = ('key', 'keys')
            for p, conf in _iter_list_with_path(path, groups):
                _ensure_is_dict(p, conf, fields)
                k, gk = [conf[f] for f in fields]
                if not isinstance(gk, list):
                    raise BadConfError(f'<{p}/keys> is not a list.')
                self.provider.register_group(k, gk)
        else:
            raise BadConfError(f'<{path}> is not either dict or list.')


    def _on_binds(self, path: str, binds):
        if not binds:
            return

        if isinstance(binds, dict):
            for k, v in binds.items():
                self.provider.register_bind(k, v)
        elif isinstance(binds, list):
            fields = ('key', 'target')
            for p, conf in _iter_list_with_path(path, binds):
                _ensure_is_dict(p, conf, fields)
                values = [conf[f] for f in fields]
                self.provider.register_bind(*values)
        else:
            raise BadConfError(f'<{path}> is not either dict or list.')


def load_conf(provider: ServiceProvider, conf: dict) -> None:
    '''
    load a conf dict and build the `ServiceProvider`.

    if conf dict was incorrect, raise `BadConfError` with useful message.
    '''
    _ConfLoader(provider).load_conf(conf)
