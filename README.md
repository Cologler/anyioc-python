# anyioc

![GitHub](https://img.shields.io/github/license/Cologler/anyioc-python.svg)
[![Build Status](https://travis-ci.com/Cologler/anyioc-python.svg?branch=master)](https://travis-ci.com/Cologler/anyioc-python)
[![PyPI](https://img.shields.io/pypi/v/anyioc.svg)](https://pypi.org/project/anyioc/)

Another simple ioc framework for python.

## Usage

``` py
from anyioc import ServiceProvider
provider = ServiceProvider()
provider.register_singleton('the key', lambda x: 102) # x will be scoped ServiceProvider
value = provider.get('the key')
assert value == 102
```

Need global ServiceProvider ? try `from anyioc.g import ioc`.

## Details

### Features

By default, you can use methods to register with lifetime:

* `register_singleton(key, factory)`
* `register_scoped(key, factory)`
* `register_transient(key, factory)`
* `register(key, factory, lifetime)`
* `register_value(key, value)`
* `register_group(key, keys)`
* `register_bind(new_key, target_key)`

### Predefined keys

There are some predefined keys you can use direct, but you still can overwrite it:

* `ioc` - get current scoped ServiceProvider instance.
* `provider` - alias of `ioc`
* `service_provider` - alias of `ioc`

### `provider.get()` vs `provider[]`

`provider[]` will raise `ServiceNotFoundError` when service was not found;

`provider.get()` only return `None` without error.

### IServiceInfoResolver

By default, you need to register a service before you get it.

So if you want to dynamic get it without register:

``` py
from anyioc import ServiceProvider
from anyioc.symbols import Symbols
from anyioc.ioc_resolver import ImportServiceInfoResolver

import sys
provider = ServiceProvider()
provider[Symbols.missing_resolver].append(ImportServiceInfoResolver())
assert sys is provider['sys']
```

There are other builtin resolvers:

* ImportServiceInfoResolver - import a module from a `str` key
* TypesServiceInfoResolver - create instance from a `type` key
* TypeNameServiceInfoResolver - from `str` key find a `type`, then create instance
