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
    for i, v in enumerate(l):
        yield f'{path}[{i!r}]', v

def _iter_dict_with_path(path: str, d: dict):
    for k, v in d.items():
        yield f'{path}[{k!r}]', v

def _iter_convlist_with_path(path: str, l: list):
    for v in l:
        k = v['key']
        yield f'{path}[{k!r}]', v

def _ensure_items_of_list_are_dict(path: str, l: list):
    for p, v in _iter_list_with_path(path, l):
        if not isinstance(v, dict):
            raise BadConfError(f'<{p}> must be a dict.')

def _ensure_values_of_dict_are_dict(path: str, d: dict):
    for p, v in _iter_dict_with_path(path, d):
        if not isinstance(v, dict):
            raise BadConfError(f'<{p}> must be a dict.')

def _ensure_items_of_list_has_field(path: str, l: list, field: str):
    for p, v in _iter_list_with_path(path, l):
        if field not in v:
            raise BadConfError(f'<{p}> miss {field!r} field.')


def _convert_dict_to_list(path: str, d: dict) -> list:
    '''
    convert dict to list. put the keys of dict into item of list.
    '''
    rv = []
    for k, v in d.items():
        if 'key' in v:
            if v['key'] != k:
                e = v['key']
                raise BadConfError(f'<{path}[{k!r}]> already contains another key: {e!r}.')
            else:
                pass
        else:
            v = v.copy() # ensure we did not modify the origin dict
            v['key'] = k
        rv.append(v)
    return rv


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
            _ensure_values_of_dict_are_dict(path, services)
            services_list = _convert_dict_to_list(path, services)
            for p, v in _iter_convlist_with_path(path, services_list):
                self._on_service_item(p, v)
        elif isinstance(services, list):
            _ensure_items_of_list_are_dict(path, services)
            _ensure_items_of_list_has_field(path, services, 'key')
            for p, v in _iter_list_with_path(path, services):
                self._on_service_item(p, v)
        else:
            raise BadConfError(f'<{path}> is not either dict or list.')

    def _on_service_item(self, path: str, service_conf: dict):
        service_conf = service_conf.copy() # ensure we did not modify the origin dict

        # key
        key = service_conf.pop('key')

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
                fac_mod_name, fac_func_name = parts
            elif isinstance(factory, dict):
                factory = factory.copy()
                fac_mod_name = factory.pop('module', None)
                if not isinstance(fac_mod_name, str):
                    raise BadConfError(f'value of <{path}/factory/module> should be a str.')
                fac_func_name = factory.pop('name', None)
                if not isinstance(fac_func_name, str):
                    raise BadConfError(f'value of <{path}/factory/name> should be a str.')
            else:
                raise BadConfError(f'value of <{path}/factory> is not either str or dict.')

            try:
                mod = import_module(fac_mod_name)
            except ImportError:
                raise BadConfError(f'<{path}/factory> required a unable import module `{fac_mod_name}`.')
            try:
                factory = getattr(mod, fac_func_name)
            except AttributeError:
                raise BadConfError(f'<{path}/factory>: no such attr {fac_func_name!r} on module {fac_mod_name!r}.')
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
            _ensure_items_of_list_are_dict(path, values)
            for f in fields:
                _ensure_items_of_list_has_field(path, values, f)
            for p, conf in _iter_list_with_path(path, values):
                conf = conf.copy() # ensure we did not modify the origin dict
                values = [conf.pop(f) for f in fields]
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
            _ensure_items_of_list_are_dict(path, groups)
            for f in fields:
                _ensure_items_of_list_has_field(path, groups, f)
            for p, conf in _iter_list_with_path(path, groups):
                conf = conf.copy() # ensure we did not modify the origin dict
                k, gk = [conf.pop(f) for f in fields]
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
            _ensure_items_of_list_are_dict(path, binds)
            for f in fields:
                _ensure_items_of_list_has_field(path, binds, f)
            for p, conf in _iter_list_with_path(path, binds):
                conf = conf.copy() # ensure we did not modify the origin dict
                values = [conf.pop(f) for f in fields]
                self.provider.register_bind(*values)
        else:
            raise BadConfError(f'<{path}> is not either dict or list.')


def load_conf(provider: ServiceProvider, conf: dict) -> None:
    '''
    load a conf dict and build the `ServiceProvider`.

    if conf dict was incorrect, raise `BadConfError` with useful message.
    '''
    _ConfLoader(provider).load_conf(conf)
