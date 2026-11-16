#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Tests for request_timeout: timeout injection without editing YanAPI.py."""

import json

import pytest
import requests

import request_timeout
import YanAPI


class FakeResponse:
    def __init__(self, payload):
        self.content = json.dumps(payload).encode("utf-8")


@pytest.fixture(autouse=True)
def _clean_patch():
    request_timeout.restore()
    yield
    request_timeout.restore()


def test_install_adds_default_timeout_to_get(monkeypatch):
    calls = []

    def fake_get(*args, **kwargs):
        calls.append(kwargs)
        return FakeResponse({"code": 0, "data": {"percent": 50}})

    monkeypatch.setattr(requests, "get", fake_get)
    request_timeout.install()

    requests.get("http://robot/v1/devices/battery")

    assert calls[0]["timeout"] == request_timeout.DEFAULT_TIMEOUT


def test_install_keeps_explicit_timeout(monkeypatch):
    calls = []

    def fake_get(*args, **kwargs):
        calls.append(kwargs)
        return FakeResponse({"code": 0, "data": {}})

    monkeypatch.setattr(requests, "get", fake_get)
    request_timeout.install()

    requests.get("http://robot/v1/devices/battery", timeout=1)

    assert calls[0]["timeout"] == 1


def test_install_wraps_put_too(monkeypatch):
    calls = []

    def fake_put(*args, **kwargs):
        calls.append(kwargs)
        return FakeResponse({"code": 0})

    monkeypatch.setattr(requests, "put", fake_put)
    request_timeout.install()

    requests.put("http://robot/v1/devices/volume", data="{}")

    assert calls[0]["timeout"] == request_timeout.DEFAULT_TIMEOUT


def test_install_is_idempotent(monkeypatch):
    calls = []

    def fake_get(*args, **kwargs):
        calls.append(kwargs)
        return FakeResponse({"code": 0, "data": {}})

    monkeypatch.setattr(requests, "get", fake_get)
    request_timeout.install()
    request_timeout.install()

    requests.get("http://robot/v1/devices/battery")

    assert len(calls) == 1
    assert calls[0]["timeout"] == request_timeout.DEFAULT_TIMEOUT


def test_yanapi_calls_receive_a_timeout(monkeypatch):
    """The SDK reads requests.get at call time, so the patch reaches it."""

    def fake_get(*args, **kwargs):
        assert kwargs["timeout"] == request_timeout.DEFAULT_TIMEOUT
        return FakeResponse({"code": 0, "data": {"percent": 75}})

    monkeypatch.setattr(requests, "get", fake_get)
    request_timeout.install()

    result = YanAPI.get_robot_battery_info()

    assert result["code"] == 0
    assert result["data"]["percent"] == 75
    assert request_timeout.is_installed()


def test_restore_returns_original_behaviour(monkeypatch):
    calls = []

    def fake_get(*args, **kwargs):
        calls.append(kwargs)
        return FakeResponse({"code": 0, "data": {}})

    monkeypatch.setattr(requests, "get", fake_get)
    request_timeout.install()
    request_timeout.restore()

    requests.get("http://robot/v1/devices/battery")

    assert "timeout" not in calls[0]
    assert not request_timeout.is_installed()
