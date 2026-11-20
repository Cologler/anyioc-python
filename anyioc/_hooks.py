from collections.abc import Callable
from threading import Condition, Lock, Thread, current_thread


class Hooks[**P]:
    """Run synchronous callbacks in registration order, at most once.

    Calling `run` freezes registration and executes the callbacks. Reentry by
    the executing thread returns immediately. Other threads wait for the
    outcome. A failure stops the remaining callbacks and is raised on replay.
    """

    def __init__(self) -> None:
        self._condition = Condition(Lock())
        self._pending: list[Callable[P, object]] | None = []
        self._frozen = False
        self._runner: Thread | None = None
        self.run: Callable[P, None] = self._start

    def add(self, hook: Callable[P, object], /) -> None:
        """Register a callback before registration is frozen."""
        with self._condition:
            if self._frozen:
                raise RuntimeError('Cannot add a hook after registration is frozen.')
            assert self._pending is not None
            self._pending.append(hook)

    def freeze(self) -> None:
        """Close registration while keeping the pending callbacks runnable."""
        with self._condition:
            self._frozen = True

    @property
    def running(self) -> bool:
        """Return whether a thread is executing the callbacks."""
        with self._condition:
            return self._runner is not None

    def _start(self, *args: P.args, **kwargs: P.kwargs) -> None:
        with self._condition:
            callbacks = self._pending
            if callbacks is not None:
                self._runner = current_thread()
                self._frozen = True
                self._pending = None
                self.run = self._wait_for_run
            run = self.run

        # Another caller may have advanced the state after this entry point was read.
        if callbacks is None:
            run(*args, **kwargs)
            return

        terminal: Callable[P, None] = self._noop
        try:
            for callback in callbacks:
                callback(*args, **kwargs)
        except BaseException as exc:
            error = exc

            def raise_failure(*args: P.args, **kwargs: P.kwargs) -> None:
                raise error

            terminal = raise_failure
            raise
        finally:
            with self._condition:
                self._runner = None
                # Publish the outcome before waking callers holding an older entry point.
                self.run = terminal
                self._condition.notify_all()

    def _wait_for_run(self, *args: P.args, **kwargs: P.kwargs) -> None:
        with self._condition:
            runner = self._runner
            if runner is not None and runner is current_thread():
                return
            while self._runner is not None:
                self._condition.wait()
            terminal = self.run

        terminal(*args, **kwargs)

    @staticmethod
    def _noop(*args: P.args, **kwargs: P.kwargs) -> None:
        pass
