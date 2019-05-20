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

### Features

By default, you can use methods of `ServiceProvider` to register services with lifetime:

* `register_singleton(key, factory)`
* `register_scoped(key, factory)`
* `register_transient(key, factory)`
* `register(key, factory, lifetime)`
* `register_value(key, value)`
* `register_group(key, keys)`
* `register_bind(new_key, target_key)`

### Global `ServiceProvider`

#### Process scoped

By default, you should create your `ServiceProvider`.

However, we can use a global `ServiceProvider` to share services in python process.

``` py
from anyioc.g import ioc

# ioc is a global `ServiceProvider` instance
```

#### Module scoped and namespace scoped

Also we have module scoped `ServiceProvider` and namespace scoped `ServiceProvider`.

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

* `ioc` - get current scoped `ServiceProvider` instance.
* `provider` - alias of `ioc`
* `service_provider` - alias of `ioc`

### `provider.get()` vs `provider[]`

There are two ways to get services from `ServiceProvider`:

* `provider[]` will raise `ServiceNotFoundError` if the service was not found;
* `provider.get()` only return `None` if the service was not found.

### IServiceInfoResolver

By default, you can get a service after you register it;

If you want to dynamic get it without register, you can do that by use `IServiceInfoResolver`:

``` py
from anyioc import ServiceProvider
from anyioc.symbols import Symbols
from anyioc.ioc_resolver import ImportServiceInfoResolver

import sys
provider = ServiceProvider()
provider[Symbols.missing_resolver].append(ImportServiceInfoResolver().cache())
assert sys is provider['sys']
```

*`.cache()` can cache the results.*

There are other builtin resolvers:

* `ImportServiceInfoResolver` - import module by name from a `str` key
* `TypesServiceInfoResolver` - create instance by type from a `type` key
* `TypeNameServiceInfoResolver` - create instance by type name from a `str` key
* `TypingServiceInfoResolver` - get services tuple by keys from a `typing.Tuple` key.
