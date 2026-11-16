#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Tests for dance_sequence.py using a fake YanAPI (no robot, no network).

Run with: pytest -q
"""

import pytest

import dance_sequence


class FakeYanApi:
    """In-memory stand-in for the YanAPI module."""

    def __init__(self, motion_result=True, raise_on_motion=None, power=0):
        self.motion_result = motion_result
        self.raise_on_motion = raise_on_motion
        self.power = power
        self.motions = []
        self.events = []

    def get_joystick_buttons_list_value(self):
        return {"POWER": self.power, "A": 0}

    def get_robot_battery_value(self):
        return 87

    def sync_play_motion(self, name="reset", direction="", speed="normal",
                         repeat=1, version="v1"):
        self.motions.append((name, direction))
        self.events.append("motion:" + name)
        if name == self.raise_on_motion:
            raise RuntimeError("motion exploded")
        return self.motion_result

    def start_play_music(self, name=""):
        self.events.append("music:start")
        return {"code": 0, "msg": "success"}

    def stop_play_music(self):
        self.events.append("music:stop")
        return {"code": 0, "msg": "success"}


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Keep the suite fast: the sequence's cosmetic sleeps are irrelevant here."""
    monkeypatch.setattr(dance_sequence.time, "sleep", lambda seconds: None)


# --------------------------------------------------------------------------
# safe_call: must accept both SDK return styles (bool and dict)
# --------------------------------------------------------------------------

def test_safe_call_accepts_bool_true():
    assert dance_sequence.safe_call(lambda: True) is True


def test_safe_call_accepts_bool_false():
    assert dance_sequence.safe_call(lambda: False) is False


def test_safe_call_accepts_dict_success():
    assert dance_sequence.safe_call(lambda: {"code": 0, "msg": "success"}) is True


def test_safe_call_accepts_dict_failure():
    assert dance_sequence.safe_call(lambda: {"code": 1, "msg": "boom"}) is False


def test_safe_call_returns_false_when_call_raises():
    def boom():
        raise RuntimeError("network down")

    assert dance_sequence.safe_call(boom) is False


# --------------------------------------------------------------------------
# Button polling
# --------------------------------------------------------------------------

def test_is_power_button_pressed_reads_power_state():
    assert dance_sequence.is_power_button_pressed(FakeYanApi(power=1)) is True
    assert dance_sequence.is_power_button_pressed(FakeYanApi(power=0)) is False


def test_wait_for_power_button_returns_true_when_pressed():
    api = FakeYanApi(power=1)
    assert dance_sequence.wait_for_power_button(api, poll_interval=0.01) is True


def test_wait_for_power_button_gives_up_after_consecutive_errors():
    class BrokenApi:
        def get_joystick_buttons_list_value(self):
            raise ConnectionError("robot unreachable")

    assert dance_sequence.wait_for_power_button(
        BrokenApi(), poll_interval=0.01, max_failures=3
    ) is False


# --------------------------------------------------------------------------
# Dance sequence
# --------------------------------------------------------------------------

def test_execute_dance_sequence_plays_expected_motions():
    api = FakeYanApi()
    assert dance_sequence.execute_dance_sequence(api) is True
    assert api.motions == [
        ("crouch", ""),
        ("bow", ""),
        ("walk", "forward"),
        ("turn around", "right"),
        ("wave", "both"),
    ]


def test_execute_dance_sequence_stops_music_after_dancing():
    api = FakeYanApi()
    dance_sequence.execute_dance_sequence(api)
    assert "music:start" in api.events
    assert api.events.index("music:start") < api.events.index("motion:walk")
    assert api.events[-1] == "music:stop"


def test_execute_dance_sequence_stops_music_when_motion_raises():
    api = FakeYanApi(raise_on_motion="wave")
    dance_sequence.execute_dance_sequence(api)
    assert api.events[-1] == "music:stop"


def test_execute_dance_sequence_returns_false_when_motion_fails():
    assert dance_sequence.execute_dance_sequence(FakeYanApi(motion_result=False)) is False


def test_execute_dance_sequence_returns_false_when_music_fails():
    class MusicFails(FakeYanApi):
        def start_play_music(self, name=""):
            return {"code": 7, "msg": "no such file"}

    assert dance_sequence.execute_dance_sequence(MusicFails()) is False


# --------------------------------------------------------------------------
# main(): test mode must never touch the real SDK / network
# --------------------------------------------------------------------------

def test_main_test_mode_uses_dry_run_api(monkeypatch):
    class NetworkGuard:
        def __getattr__(self, name):
            raise AssertionError("test mode must not touch YanAPI." + name)

    monkeypatch.setattr(dance_sequence, "yan_api", NetworkGuard())
    assert dance_sequence.main(["--test"]) == 0


def test_main_returns_one_when_button_wait_fails(monkeypatch):
    monkeypatch.setattr(dance_sequence.yan_api, "get_robot_battery_value",
                        lambda: 87)
    monkeypatch.setattr(dance_sequence, "wait_for_power_button", lambda *a, **k: False)

    assert dance_sequence.main(["--ip", "127.0.0.1"]) == 1


def test_main_installs_request_timeout_by_default(monkeypatch):
    installed = []
    monkeypatch.setattr(dance_sequence.request_timeout, "install",
                        lambda timeout=dance_sequence.request_timeout.DEFAULT_TIMEOUT:
                        installed.append(timeout))

    assert dance_sequence.main(["--test"]) == 0
    assert installed == [dance_sequence.request_timeout.DEFAULT_TIMEOUT]


def test_main_timeout_option_installs_custom_timeout(monkeypatch):
    captured = {}

    def fake_install(timeout=dance_sequence.request_timeout.DEFAULT_TIMEOUT):
        captured["timeout"] = timeout

    monkeypatch.setattr(dance_sequence.request_timeout, "install", fake_install)

    assert dance_sequence.main(["--test", "--timeout", "2.5"]) == 0
    assert captured["timeout"] == (2.5, 2.5)
