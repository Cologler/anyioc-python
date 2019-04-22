# anyioc

[![Build Status](https://travis-ci.com/Cologler/anyioc-python.svg?branch=master)](https://travis-ci.com/Cologler/anyioc-python)

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

### Predefined keys

There are some predefined keys you can use direct, but you still can overwrite it:

* `ioc` - get current scoped ServiceProvider instance.
* `provider` - alias of `ioc`
* `service_provider` - alias of `ioc`

### `provider.get()` vs `provider[]`

`provider[]` will raise `ServiceNotFoundError` when service was not found;

`provider.get()` only return `None` without error.
