# anyioc

Another simple ioc framework for python.

## Usage

``` py
from anyioc import ServiceProvider
provider = ServiceProvider()
provider.register_singleton('the key', lambda x: 102) # x will be scoped ServiceProvider
value = provider.get('the key')
assert value == 102
```
