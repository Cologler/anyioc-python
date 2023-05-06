# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from .ioc import ServiceProvider, LifeTime
from .symbols import _Symbol
from .utils import inject_by_anno, inject_by_name

inject_by_table = {
    'anno': inject_by_anno,
    'inject_by_anno': inject_by_anno,
    'name': inject_by_name,
    'inject_by_name': inject_by_name
}

class ServiceProviderBuilder:
    '''
    a decorator api helper class for `ServiceProvider`.
    '''
    __slots__ = ('_provider')

    def __init__(self, provider: ServiceProvider):
        self._provider = provider

    def _on_key_added(self, key):
        pass

    def register(self, lifetime: LifeTime, key=None, factory=None, *, inject_by=None):
        '''
        Register a service factory by `key` with `lifetime`,
        can be use as decorator if the `factory` set `None`.

        If the `key` is `None`, use the `factory` as key. This is helpful to use a `type` as factory.
        Special, if the `key` is a `list`, use each item in it as key;

        By default, the parameter `factory` accept a callable like `() -> Any` or `(ioc) -> Any`,
        but you can pass a `inject_by` function to wrap the `factory` to `(ioc) -> Any`.
        `anyioc` include some useful `inject_by_*` helper functions in `anyioc.utils`.

        returns:

        - decorator mode return the factory.
        - non-decorator mode always return None
        '''

        if isinstance(inject_by, str):
            if inject_by in inject_by_table:
                inject_by = inject_by_table[inject_by]
            else:
                raise ValueError(f'{inject_by} is not one of known `inject by` action.')

        def decorator(func):
            aliases = ()
            if key is None:
                safe_key = func
            elif isinstance(key, list):
                if not key:
                    raise ValueError('cannot use empty list as key list')
                safe_key = _Symbol(f'ref-for-{key[0]}')
                aliases = key
            else:
                safe_key = key

            wraped_func = inject_by(func) if inject_by else func
            self._provider.register(safe_key, wraped_func, lifetime)
            self._on_key_added(safe_key)
            for k in aliases:
                self._provider.register_bind(k, safe_key)
            return func

        if factory is None:
            return decorator
        else:
            decorator(factory)

    def singleton(self, key=None, factory=None, *, inject_by=None):
        '''
        Call `register()` with `LifeTime.singleton`.

        See `register()` for more details.
        '''
        return self.register(LifeTime.singleton, key, factory, inject_by=inject_by)

    def scoped(self, key=None, factory=None, *, inject_by=None):
        '''
        Call `register()` with `LifeTime.scoped`.

        See `register()` for more details.
        '''
        return self.register(LifeTime.scoped, key, factory, inject_by=inject_by)

    def transient(self, key=None, factory=None, *, inject_by=None):
        '''
        Call `register()` with `LifeTime.transient`.

        See `register()` for more details.
        '''
        return self.register(LifeTime.transient, key, factory, inject_by=inject_by)

    def value(self, key):
        '''
        get a decorator that use to register a singleton value by key.
        '''

        def decorator(value):
            self._provider.register_value(key, value)
            self._on_key_added(key)
            return value

        return decorator

    def group(self, *keys):
        '''
        add a new group into `ServiceProvider` by keys,
        return a group scoped `ServiceProviderBuilder` to build sub services.

        the return instance can also use like a unique key.
        '''
        group = Group(self._provider)
        self._provider.register_group(group, group)
        self._on_key_added(group)
        for k in keys:
            self._provider.register_bind(k, group)
        return group


class Group(ServiceProviderBuilder):
    '''
    a `Group` class use for build `ServiceProvider` and use as unique group key.
    '''
    __slots__ = ('_group_keys_list', )

    def __init__(self, provider: ServiceProvider):
        super().__init__(provider)
        self._group_keys_list = []

    def __iter__(self):
        return iter(self._group_keys_list)

    def _on_key_added(self, key):
        self._group_keys_list.append(key)
        super()._on_key_added(key)
