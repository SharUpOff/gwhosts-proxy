import gc

from gwhosts.performance import no_gc


def test_no_gc() -> None:
    is_gc_enabled = gc.isenabled()

    with no_gc():
        assert gc.isenabled() is False

    assert gc.isenabled() == is_gc_enabled
