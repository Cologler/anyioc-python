# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from .ioc import ScopedServiceProvider, LifeTime
from .symbols import Symbols, _Symbol

class ServiceProviderBuilder:
    '''
    provide decorator api for `ServiceProvider`.
    '''
    __slots__ = ('_provider', '_last_added_key')

    def __init__(self, provider: ScopedServiceProvider):
        self._provider = provider
        self._last_added_key = None

    @property
    def last_added_key(self):
        return self._last_added_key

    def _on_key_added(self, key):
        self._last_added_key = key

    def register(self, lifetime: LifeTime, key=None, factory=None, *, inject_by=None):
        '''
        register a service factory by key.

        `factory` accept a function which require one or zero parameter.
        if the count of parameter is 1, pass a `IServiceProvider` as the argument.

        - if `key` is `None`, use `factory` as key;
        - if `key` is a list, use each item in it as key;

        this function can use like a decorator if `factory` is `None`.

        `inject_by`: you can pass a function to convert `factory` signature to `ioc => any`;
        there are some `inject_by_*` helper functions in `anyioc.utils`.

        returns:

        - decorator return the factory.
        - non-decorator always return None
        '''

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
        register a service factory by key.

        `factory` accept a function which require one or zero parameter.
        if the count of parameter is 1, pass a `IServiceProvider` as the argument.

        - if `key` is `None`, use `factory` as key;
        - if `key` is a list, use each item in it as key;

        this function can use like a decorator if `factory` is `None`.

        `inject_by`: you can pass a function to convert `factory` signature to `ioc => any`;
        there are some `inject_by_*` helper functions in `anyioc.utils`.

        returns:

        - decorator return the factory.
        - non-decorator always return None
        '''
        return self.register(LifeTime.singleton, key, factory, inject_by=inject_by)

    def scoped(self, key=None, factory=None, *, inject_by=None):
        '''
        register a service factory by key.

        `factory` accept a function which require one or zero parameter.
        if the count of parameter is 1, pass a `IServiceProvider` as the argument.

        - if `key` is `None`, use `factory` as key;
        - if `key` is a list, use each item in it as key;

        this function can use like a decorator if `factory` is `None`.

        `inject_by`: you can pass a function to convert `factory` signature to `ioc => any`;
        there are some `inject_by_*` helper functions in `anyioc.utils`.

        returns:

        - decorator return the factory.
        - non-decorator always return None
        '''
        return self.register(LifeTime.scoped, key, factory, inject_by=inject_by)

    def transient(self, key=None, factory=None, *, inject_by=None):
        '''
        register a service factory by key.

        `factory` accept a function which require one or zero parameter.
        if the count of parameter is 1, pass a `IServiceProvider` as the argument.

        - if `key` is `None`, use `factory` as key;
        - if `key` is a list, use each item in it as key;

        this function can use like a decorator if `factory` is `None`.

        `inject_by`: you can pass a function to convert `factory` signature to `ioc => any`;
        there are some `inject_by_*` helper functions in `anyioc.utils`.

        returns:

        - decorator return the factory.
        - non-decorator always return None
        '''
        return self.register(LifeTime.transient, key, factory, inject_by=inject_by)

    def value(self, key, *value):
        '''
        register a value by key.

        this function can use like a decorator if only have 1 arguments.

        if `key` is `None`, use a new `object()` as key.
        you can get the generated new key by access `ServiceProviderBuilder.last_added_key`.

        return the value.
        '''
        if len(value) > 1:
            raise TypeError(f'takes 1 or 2 arguments but {len(value)+1} was given')

        def decorator(value):
            safe_key = key if key is not None else object()
            self._provider.register_value(safe_key, value)
            self._on_key_added(safe_key)
            return value

        return decorator(value[0]) if value else decorator

    def group(self, group_key=None):
        '''
        add a new group into `ServiceProvider` by key `group_key`.

        if `group_key` is `None`, use return value as key.

        return a `Group` instance as the unique key.
        '''
        from .utils import make_group

        group = Group(self._provider)
        self._provider.register_group(group, group)
        self._on_key_added(group)
        if group_key is not None:
            self._provider.register_bind(group_key, group)
            sym = Symbols.get_symbol_for_group_src(group_key)
            self._provider.register_value(sym, group)
        return group


class Group(ServiceProviderBuilder):
    '''
    a `Group` class use for build `ServiceProvider` and use as unique group key.
    '''
    __slots__ = ('_group_keys_list', )

    def __init__(self, provider: ScopedServiceProvider):
        super().__init__(provider)
        self._group_keys_list = []

    def __iter__(self):
        return iter(self._group_keys_list)

    def _on_key_added(self, key):
        self._group_keys_list.append(key)
        super()._on_key_added(key)
