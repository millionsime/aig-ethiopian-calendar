# Tiny test helpers - zero dependencies (pytest-compatible: plain test_*
# functions with asserts are collected by pytest too).
import contextlib


@contextlib.contextmanager
def raises(exc):
    """Minimal stand-in for pytest.raises."""
    try:
        yield
    except exc:
        return
    raise AssertionError(f"expected {getattr(exc, '__name__', exc)} to be raised")
