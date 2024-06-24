import gc
from contextlib import contextmanager


@contextmanager
def no_gc():
    _gc_is_enabled = gc.isenabled()
    gc.disable()

    try:
        yield

    finally:
        if _gc_is_enabled:
            gc.enable()
