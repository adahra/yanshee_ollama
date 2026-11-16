#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
YanAPI Button-Triggered Dance Sequence

Waits for a gamepad POWER button press, then performs:
1. Crouch motion
2. Bow motion
3. Dance sequence (music + movements)

Note:
    YanAPI exposes no API for the physical chest switch. The trigger below
    reads the joystick/gamepad button map, where ``POWER`` is the gamepad
    POWER key (see YanAPI.get_joystick_buttons_list_value). On firmware
    builds that map the chest button onto that key, pressing the chest
    button also works.

Usage:
    python3 dance_sequence.py                  # run against 127.0.0.1
    python3 dance_sequence.py --ip 192.168.1.100
    python3 dance_sequence.py --test           # dry run, no network
"""

import argparse
import sys
import time

import YanAPI as yan_api
import request_timeout

POLL_INTERVAL = 0.5
MAX_CONSECUTIVE_FAILURES = 10


class DryRunAPI:
    """Stand-in for YanAPI in ``--test`` mode. Never touches the network."""

    def get_joystick_buttons_list_value(self):
        return {"POWER": 1}

    def get_robot_battery_value(self):
        return 100

    def sync_play_motion(self, name="reset", direction="", speed="normal",
                         repeat=1, version="v1"):
        print("  [DRY RUN] motion: " + name +
              ((" (" + direction + ")") if direction else ""))
        return True

    def start_play_music(self, name=""):
        print("  [DRY RUN] music: start " + (name or "(default)"))
        return {"code": 0, "msg": "success"}

    def stop_play_music(self):
        print("  [DRY RUN] music: stop")
        return {"code": 0, "msg": "success"}


def is_power_button_pressed(api=yan_api):
    """Return True when the POWER button reports as pressed.

    Raises:
        Any exception raised by the API call (the caller decides whether to
        retry or give up).
    """
    buttons = api.get_joystick_buttons_list_value()
    if not isinstance(buttons, dict):
        return False
    return buttons.get("POWER", 0) == 1


def wait_for_power_button(api=yan_api, poll_interval=POLL_INTERVAL,
                          max_failures=MAX_CONSECUTIVE_FAILURES):
    """Block until POWER is pressed, or give up after repeated errors.

    Returns:
        bool: True when pressed, False when interrupted or the robot could
        not be reached ``max_failures`` times in a row.
    """
    print("Waiting for POWER button press...")
    print("Press the POWER button on the gamepad (or the chest button if your")
    print("firmware maps it there). Press Ctrl+C to cancel.")

    failures = 0
    try:
        while True:
            try:
                pressed = is_power_button_pressed(api)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                failures += 1
                print("Error checking button status (" + str(failures) + "/" +
                      str(max_failures) + "): " + str(e))
                if failures >= max_failures:
                    print("Could not read button state; giving up.")
                    return False
                time.sleep(poll_interval)
                continue

            failures = 0
            if pressed:
                print("POWER button pressed!")
                return True
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return False


def safe_call(func, *args, **kwargs):
    """Call an SDK function and normalise its result to a bool.

    YanAPI is inconsistent: motion helpers return ``bool`` while most other
    calls return a ``{"code": ..., "msg": ...}`` dict. Both are accepted.
    """
    try:
        result = func(*args, **kwargs)
    except Exception as e:
        print("Error calling " + func.__name__ + ": " + str(e))
        return False

    if isinstance(result, bool):
        if not result:
            print("Call to '" + func.__name__ + "' returned False")
        return result

    if isinstance(result, dict):
        if result.get("code", 1) == 0:
            return True
        print("Call to '" + func.__name__ + "' failed: " +
              str(result.get("msg", "Unknown error")))
        return False

    print("Call to '" + func.__name__ + "' returned unexpected " +
          type(result).__name__ + ": " + repr(result))
    return False


def execute_dance_sequence(api=yan_api):
    """Execute the full dance sequence after the button press.

    Sequence:
    1. Crouch down
    2. Bow respectfully
    3. Start dancing (music + movements)

    Returns:
        bool: True only if every step succeeded.
    """
    print("\nExecuting dance sequence...")
    results = []

    # Step 1: Crouch
    print("Step 1: Performing crouch...")
    if safe_call(api.sync_play_motion, "crouch"):
        results.append(True)
        print("  Crouch complete")
    else:
        results.append(False)
    time.sleep(0.5)

    # Step 2: Bow
    print("Step 2: Performing bow...")
    if safe_call(api.sync_play_motion, "bow"):
        results.append(True)
        print("  Bow complete")
    else:
        results.append(False)
    time.sleep(0.5)

    # Step 3: Dance sequence
    print("Step 3: Starting dance sequence...")

    print("  Playing music...")
    results.append(safe_call(api.start_play_music))

    try:
        time.sleep(1)

        print("  Walking forward...")
        results.append(safe_call(api.sync_play_motion, "walk", "forward", "normal"))

        print("  Turning around...")
        results.append(safe_call(api.sync_play_motion, "turn around", "right", "normal"))

        print("  Waving...")
        results.append(safe_call(api.sync_play_motion, "wave", "both", "normal"))
    finally:
        # Always stop the music, even if a motion call blows up.
        results.append(safe_call(api.stop_play_music))

    print("  Dance sequence complete")
    return all(results)


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Wait for the POWER button, then run a dance sequence.")
    parser.add_argument("--ip", default="127.0.0.1",
                        help="Yanshee IP address (default: 127.0.0.1)")
    parser.add_argument("--test", action="store_true",
                        help="dry run: simulate the button and every call locally")
    parser.add_argument("--timeout", type=float, default=None,
                        help="override network timeout in seconds for both connect and read "
                             "(default: 3.05 / 10)")
    # Backwards compatibility: `python3 dance_sequence.py test`
    parser.add_argument("mode", nargs="?", choices=["test"],
                        help=argparse.SUPPRESS)
    return parser


def main(argv=None, api=None):
    """Run the button-triggered dance sequence. Returns a process exit code."""
    args = build_arg_parser().parse_args(argv)
    timeout = ((args.timeout, args.timeout)
               if args.timeout is not None
               else request_timeout.DEFAULT_TIMEOUT)
    request_timeout.install(timeout=timeout)
    test_mode = args.test or args.mode == "test"

    print("=" * 60)
    print("YanAPI Button-Triggered Dance Sequence")
    print("=" * 60)

    if test_mode:
        print("Running in TEST MODE (dry run, no robot calls)")
        api = DryRunAPI()
        print("Simulating POWER button press in 3 seconds...")
        time.sleep(3)
        print("Simulated POWER button pressed!")
    else:
        if api is None:
            api = yan_api
            print("Initializing YanAPI for " + args.ip + "...")
            yan_api.yan_api_init(args.ip)

        try:
            battery = api.get_robot_battery_value()
        except Exception as e:
            print("Warning: could not read battery: " + str(e))
            battery = -1

        if battery is None or battery < 0:
            print("Error: robot is not responding. Check the IP and that the")
            print("robot is powered on. Use --test for a dry run.")
            return 1

        print("Robot responsive (Battery: " + str(battery) + "%)")
        print("\nReady to trigger dance sequence.")

        if not wait_for_power_button(api):
            print("\nButton press waiting was cancelled.")
            return 1

    success = execute_dance_sequence(api)

    if success:
        print("\n" + "=" * 60)
        print("DANCE SEQUENCE COMPLETED!")
        print("=" * 60)
        print("\nSummary:")
        print("  - Waited for POWER button press")
        print("  - Performed crouch motion")
        print("  - Performed bow motion")
        print("  - Executed dance sequence")
        return 0

    print("\nDance sequence finished with errors (see messages above).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
