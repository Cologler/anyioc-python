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

### Global `ServiceProvider`

#### Process scoped

By default, you should create your `ServiceProvider`.

However, anyioc provide a singleton global `ServiceProvider` to share services in python process.

``` py
from anyioc.g import ioc

# ioc just a global `ServiceProvider` instance
```

This is helpful if you writing a final application instead of a library/package.

#### Module scoped and namespace scoped

anyioc also provide module scoped `ServiceProvider` and namespace scoped `ServiceProvider`.

If you have a project:

``` tree
src/
  |- your_package/
     |- __init__.py
     |- a/
        |- __init__.py
        |- b.py
```

Then module scoped `ServiceProvider`:

``` py
# file: b.py
from anyioc.g import get_module_provider

provider = get_module_provider()
assert provider is get_module_provider('your_package.a.b')
```

and namespace scoped `ServiceProvider`:

``` py
# file: b.py
from anyioc.g import get_namespace_provider

provider = get_namespace_provider()
assert provider is get_module_provider('your_package')
```

### Predefined keys

There are some predefined string keys you can use direct, but you still can overwrite it:

- `ioc` - get current scoped `ServiceProvider` instance.
- `provider` - alias of `ioc`
- `service_provider` - alias of `ioc`

And predefined types:

- `ServiceProvider` - alias of `ioc`
- `IServiceProvider` - alias of `ioc`

### IServiceInfoResolver

By default, you can get a service after you register it;

If you want to dynamic get it without register, you can do that by use `IServiceInfoResolver`:

``` py
from anyioc import ServiceProvider
from anyioc.symbols import Symbols
from anyioc.ioc_resolver import ImportServiceInfoResolver

import sys
provider = ServiceProvider()
resolver = ImportServiceInfoResolver().cache() # use `.cache()` can cache the results and prevent resolve again.
provider[Symbols.missing_resolver].append(resolver)
assert sys is provider['sys']
```

There are other builtin resolvers:

- `ImportServiceInfoResolver` - import module by name from a `str` key
- `TypesServiceInfoResolver` - create instance by type from a `type` key
- `TypeNameServiceInfoResolver` - create instance by type name from a `str` key
- `TypingServiceInfoResolver` - get services tuple by keys from a `typing.Tuple` key.

**`IServiceInfoResolver` only work when service was missing.**

Read full [documentation](../../wiki).
