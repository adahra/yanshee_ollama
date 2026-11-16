# AGENTS.md

## Project
Yanshee robot SDK (`YanAPI.py`, 5997-line module of REST wrappers) plus a button-triggered dance demo (`dance_sequence.py`) and a timeout guard (`request_timeout.py`). No manifest, CI, or lockfile — dependencies are `requests`, `nest_asyncio`, `opencv-python` (imported as `cv2`).

## Commands
- Tests: `python3 -m pytest -q` (23 tests, no robot/network needed)
- Single file: `python3 -m pytest test_mock_dance.py -q`
- Single test: `python3 -m pytest test_mock_dance.py::test_safe_call_accepts_bool_true -q`
- Dry run (no robot): `python3 dance_sequence.py --test`
- Real run: `python3 dance_sequence.py --ip 192.168.1.100`
- Override timeout: `python3 dance_sequence.py --ip 192.168.1.100 --timeout 5`
- Compile check: `python3 -m compileall -q .`

## Architecture
- `YanAPI.py` is a module of plain functions, not classes. Call `yan_api.yan_api_init(ip)` first; it mutates the module-global `basic_url`.
- `sync_play_motion(...)` returns `bool`; most other calls return `{"code", "msg", ...}` dicts. `safe_call()` in `dance_sequence.py` normalises both.
- `get_robot_battery_value()` returns `-1` on failure.
- `get_joystick_buttons_list_value()` reads the *gamepad* button map (`POWER` key). There is no SDK call for the physical chest button; the demo's trigger is the gamepad POWER key (firmware may map the chest button onto it).
- `request_timeout.py` wraps `requests.get/put/post/...` in place because YanAPI looks them up on the module at call time. Call `request_timeout.install(timeout=(connect, read))` (idempotent) before init; `restore()` in tests. Do not edit `YanAPI.py`.
- `lib_ukit/` holds protobuf stubs + CRC8 helpers for uKit 2.0.

## Testing quirks
- Tests are pytest despite filenames; no `conftest.py`. Autouse fixtures patch `time.sleep` to keep the suite fast.
- Mock the SDK by replacing `dance_sequence.yan_api` with a fake object (`FakeYanApi`); monkeypatch `dance_sequence.request_timeout.install` to capture calls.
- `test` mode uses `DryRunAPI` and never touches the network.

## Gotchas
- `YanAPI.py` imports `cv2` and calls `nest_asyncio.apply()` at import; keep both installed.
- `sync_play_motion` uses `asyncio.get_event_loop().run_until_complete`, which breaks inside a running event loop.
- `is_power_button_pressed` propagates exceptions; `wait_for_power_button` retries up to `MAX_CONSECUTIVE_FAILURES` (10) then gives up.
- `execute_dance_sequence` always stops music in `finally`.
- `QWEN.md` was removed; do not recreate it empty.