from typing import TYPE_CHECKING

from pytest import fixture

if TYPE_CHECKING:
    from h3a.context import Context


@fixture
def test_context() -> "Context":
    from threading import RLock

    from h3a.context import Context

    return Context(
        log_lock=RLock(),
        verbose=True,
        threads=1,
    )
