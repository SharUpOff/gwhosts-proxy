import gc
from contextlib import contextmanager
from collections.abc import Iterator


@contextmanager
def no_gc() -> Iterator[None]:
    _gc_is_enabled = gc.isenabled()
    gc.disable()

    try:
        yield

    finally:
        if _gc_is_enabled:
            gc.enable()
