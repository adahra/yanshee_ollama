#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Inject a default network timeout into YanAPI's HTTP calls.

YanAPI.py calls ``requests.get`` / ``requests.put`` without a ``timeout=``
argument, so an unresponsive robot can block the caller forever. The SDK is
left untouched: this module wraps the ``requests`` helpers in place, and
because YanAPI looks the functions up on the module at call time, the wrapper
reaches it.

Usage:
    import request_timeout
    request_timeout.install()      # once, before initialising YanAPI

``DEFAULT_TIMEOUT`` is a ``(connect, read)`` tuple in seconds. To bypass the
wrapper (for example in tests), call ``restore()``.
"""

import requests

DEFAULT_TIMEOUT = (3.05, 10)

_METHODS = ("get", "put", "post", "delete", "patch", "head")
_originals = {}


def _with_timeout(func, timeout):
    def wrapper(*args, **kwargs):
        kwargs.setdefault("timeout", timeout)
        return func(*args, **kwargs)

    wrapper.__name__ = getattr(func, "__name__", "wrapper")
    wrapper.__doc__ = "Wraps requests.%s, defaulting timeout=%r." % (
        wrapper.__name__, timeout)
    return wrapper


def install(timeout=DEFAULT_TIMEOUT):
    """Wrap the requests helpers so calls without a timeout get one.

    Idempotent: calling it again does nothing.
    """
    if _originals:
        return
    for name in _METHODS:
        original = getattr(requests, name, None)
        if original is None:
            continue
        _originals[name] = original
        setattr(requests, name, _with_timeout(original, timeout))


def restore():
    """Undo install(), putting the original requests helpers back."""
    for name, original in _originals.items():
        setattr(requests, name, original)
    _originals.clear()


def is_installed():
    return bool(_originals)
