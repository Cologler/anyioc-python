from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

from pytest import mark, raises

from anyioc._hooks import Hooks


def test_freeze_preserves_hook_order_and_arguments() -> None:
    calls: list[tuple[str, int]] = []
    hooks = Hooks[...]()

    def first(name: str, *, count: int) -> None:
        calls.append((name, count))

    def second(name: str, *, count: int) -> None:
        calls.append((name.upper(), count + 1))

    hooks.add(first)
    hooks.add(second)

    hooks.freeze()
    hooks.freeze()
    with raises(RuntimeError, match='frozen'):
        hooks.add(first)

    assert calls == []
    hooks.run('value', count=2)
    assert calls == [('value', 2), ('VALUE', 3)]


def test_run_ignores_reentry_and_freezes_registration() -> None:
    hooks = Hooks[[]]()
    start = hooks.run
    calls: list[str] = []

    def first() -> None:
        assert hooks.running
        calls.append('first')
        start()
        hooks.run()
        with raises(RuntimeError, match='frozen'):
            hooks.add(first)

    hooks.add(first)
    hooks.add(lambda: calls.append('second'))

    assert not hooks.running
    hooks.run()
    hooks.run()
    assert not hooks.running
    assert calls == ['first', 'second']


def test_successful_run_replaces_itself_with_a_lock_free_noop() -> None:
    hooks = Hooks[[]]()
    calls: list[str] = []
    hooks.add(lambda: calls.append('called'))

    start = hooks.run
    start()
    start()

    with patch.object(hooks, '_condition') as condition:
        hooks.run()
        assert condition.mock_calls == []

    assert calls == ['called']


class HookFailure(BaseException):
    pass


@mark.parametrize('fail', [False, True])
def test_concurrent_run_waits_for_the_same_outcome(fail: bool) -> None:
    hooks = Hooks[[]]()
    entered = Event()
    release = Event()
    waiting = Event()
    calls: list[str] = []

    def first() -> None:
        calls.append('first')
        entered.set()
        assert release.wait(timeout=5)
        if fail:
            raise HookFailure('hook failed')

    def run_again() -> None:
        waiting.set()
        hooks.run()

    hooks.add(first)
    hooks.add(lambda: calls.append('second'))
    start = hooks.run
    with ThreadPoolExecutor(max_workers=2) as pool:
        runner = pool.submit(start)
        try:
            assert entered.wait(timeout=5)
            wait_for_run = hooks.run
            waiter = pool.submit(run_again)
            assert waiting.wait(timeout=5)
            with raises(TimeoutError):
                waiter.result(timeout=0.05)
        finally:
            release.set()

        if fail:
            with raises(HookFailure, match='hook failed'):
                runner.result(timeout=5)
            with raises(HookFailure, match='hook failed'):
                waiter.result(timeout=5)
        else:
            runner.result(timeout=5)
            waiter.result(timeout=5)

    assert not hooks.running
    if fail:
        for run in (start, wait_for_run, hooks.run):
            with raises(HookFailure, match='hook failed'):
                run()
        assert calls == ['first']
    else:
        for run in (start, wait_for_run, hooks.run):
            run()
        assert calls == ['first', 'second']
