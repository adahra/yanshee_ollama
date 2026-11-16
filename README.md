# Yanshee Robot SDK

## Overview

Yanshee is a versatile robotic platform designed for education, research, and hobbyist applications. It combines advanced hardware capabilities with an easy-to-use Python SDK for comprehensive robot control.

## Key Features

### 🤖 Hardware Capabilities
- **Motion Control**: Advanced gait systems, built-in movements (walk, wave, bend, etc.)
- **Vision Systems**: AprilTag recognition, QR code scanning, face recognition, object tracking
- **Sensor Suite**: Battery monitoring, joystick controls, environmental sensors
- **Actuation**: 17 servo motors for precise movement control
- **Audio**: Speech synthesis and music playback

### 🔧 Control Interface
- RESTful API with Python SDK
- Bluetooth gamepad support
- Comprehensive motion planning and execution
- Real-time status monitoring

## Installation

```bash
pip install yan-api-sdk
```

## Getting Started

### 1. Initialize the SDK

```python
from yan_api import YanAPI

# Initialize with robot IP (replace with actual robot IP)
YanAPI.yan_api_init("192.168.1.100")
```

### 2. Basic Robot Control

```python
# Get battery status
battery_info = YanAPI.get_robot_battery_info()
print("Battery: " + str(battery_info["data"]["percent"]) + "%")

# Play a movement
YanAPI.sync_play_motion("wave")

# Check vision status
aprilTag_status = YanAPI.get_aprilTag_recognition_status()
```

### 3. Advanced Motion Control

```python
# Set custom servo angles
servo_angles = {
    "RightShoulderFlex": 90,
    "RightElbowFlex": 45,
    "LeftShoulderFlex": 90
}
YanAPI.set_servos_angles(servo_angles)

# Execute gait movement
YanAPI.sync_do_motion_gait(speed_v=2, speed_h=1, steps=10, period=2)
```

## API Reference

### Hardware Control
- **Battery**: `get_robot_battery_info()`, `get_robot_battery_value()`
- **LED Control**: `get_robot_led()`, `set_robot_led()`, `sync_set_led()`
- **Volume**: `get_robot_volume()`, `set_robot_volume()`

### Motion Systems
- **Built-in Motions**: `sync_play_motion()`, `upload_motion()`
- **Gait Control**: `control_motion_gait()`, `sync_do_motion_gait()`
- **Servo Control**: `get_servos_angles()`, `set_servos_angles()`

### Vision & Perception
- **AprilTag**: `start_aprilTag_recognition()`, `stop_aprilTag_recognition()`
- **QR Code**: `start_QR_code_recognition()`, `sync_do_QR_code_recognition()`
- **Object Tracking**: `start_object_tracking()`, `stop_object_tracking()`

### Media & Audio
- **Music**: `sync_play_music()`, `upload_media_music()`
- **Voice**: Through Voice class for speech recognition and synthesis

## Class Structure

### Core Data Classes
- `RobotBatteryInfo`: Battery voltage, charging state, percentage
- `RobotVersionInfo`: Hardware/software versions
- `RobotLedInfo`: LED colors and modes
- `RobotMotionDirection`: Movement directions
- `RobotMotionSpeed`: Speed settings

### Controller Classes
- **Voice**: Speech recognition and natural language processing
- **UkitController**: uKit2.0 integration

## Development Examples

### Example 0: Button-Triggered Dance Demo

This repository ships a small demo on top of the SDK.

```bash
python3 dance_sequence.py --test                 # dry run: no robot, no network
python3 dance_sequence.py --ip 192.168.1.100     # run against a real robot
```

The demo waits for the gamepad POWER button (the SDK exposes no API for the
physical chest switch), then runs crouch → bow → music → walk → turn → wave.
It exits non-zero if the robot cannot be reached or any step fails.

Run the test suite with:

```bash
python3 -m pytest -q
```

### Example 1: Wave Movement
```python
YanAPI.yan_api_init("192.168.1.100")
YanAPI.sync_play_motion("wave")
```

### Example 2: Object Tracking
```python
# Start tracking
YanAPI.start_object_tracking(name="yanshee", width=0.1, height=0.365)

# Monitor status
while True:
    status = YanAPI.get_object_tracking_status()
    if status["status"] == "idle":
        break
```

### Example 3: Custom Servo Sequence
```python
def wave_sequence():
    # Raise right arm
    YanAPI.set_servos_angles({"RightShoulderFlex": 45}, runtime=500)
    # Bend right elbow
    YanAPI.set_servos_angles({"RightElbowFlex": 30}, runtime=500)
    # Return to start
    YanAPI.set_servos_angles({"RightShoulderFlex": 0, "RightElbowFlex": 0}, runtime=500)

wave_sequence()
```

## Configuration

### Robot Modes
- **Energy Saving Mode**: `get_robot_mode()` checks `energy_saving_mode`
- **Calibration Mode**: `get_robot_mode()` checks `calibration_mode`

### Supported Languages
- `zh`: Chinese
- `en`: English

## Error Handling

All API functions return a dictionary with:
- `code`: 0 for success, non-zero for errors
- `data`: Response data (may be empty)
- `msg`: Human-readable message

```python
res = YanAPI.get_robot_battery_info()
if res["code"] != 0:
    print("Error: " + str(res["msg"]))
```

## Advanced Features

### Motion Layers (v2)
The robot supports layered motion systems:
- **System Layers**: Pre-built complex movements
- **User Layers**: Custom uploaded motions
- **Layer Management**: Pause/resume/stop individual layers

### Vision Integration
- Real-time AprilTag detection with pose estimation
- QR code content recognition
- Object tracking with configurable timeout parameters

## License

This project is open source. Please use responsibly and have fun!

## Contact

For questions or support, refer to the "http://[robotIP]:9090/v1/ui" interface for detailed API documentation and real-time monitoring.