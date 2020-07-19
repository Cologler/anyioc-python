# anyioc

![GitHub](https://img.shields.io/github/license/Cologler/anyioc-python.svg)
[![Build Status](https://travis-ci.com/Cologler/anyioc-python.svg?branch=master)](https://travis-ci.com/Cologler/anyioc-python)
[![PyPI](https://img.shields.io/pypi/v/anyioc.svg)](https://pypi.org/project/anyioc/)

Another simple ioc framework for python.

## Usage

``` py
from anyioc import ServiceProvider
provider = ServiceProvider()
provider.register_singleton('the key', lambda ioc: 102) # ioc will be a `IServiceProvider`
value = provider.get('the key')
assert value == 102
```

## Details

### Register and resolve

By default, you can use following methods to register services:

- `ServiceProvider.register_singleton(key, factory)`
- `ServiceProvider.register_scoped(key, factory)`
- `ServiceProvider.register_transient(key, factory)`
- `ServiceProvider.register(key, factory, lifetime)`
- `ServiceProvider.register_value(key, value)`
- `ServiceProvider.register_group(key, keys)`
- `ServiceProvider.register_bind(new_key, target_key)`

And use following methods to resolve services:

- `ServiceProvider.__getitem__(key)`
- `ServiceProvider.get(key)`
- `ServiceProvider.get_many(key)`

*`get` return `None` if the service was not found, but `__getitem__` will raise a `ServiceNotFoundError`.*

### Thread safety

- Root `ServiceProvider` is thread-safe.
- Scoped `ServiceProvider` is **NOT** thread-safe.
- Singleton service is thread-safe.
- Value service is thread-safe.

Read full [documentation](https://github.com/Cologler/anyioc-python/wiki).
