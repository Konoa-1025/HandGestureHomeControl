# gestureStabilizer.py
# Norifumi Kondo
# 手の形を複数フレームから確定する

import time

import utils.logPrint as p


_required_frames = 5
_lost_timeout = 1.0
_camera_states = {}


def Initialization(_settings):
    global _required_frames
    global _lost_timeout
    global _camera_states

    p.info("初期化中")

    _required_frames = _settings.get("required_frames", 5)
    _lost_timeout = float(_settings.get("lost_timeout", 0.5))
    _camera_states = {}

    p.success("初期化成功")
    return True


def _create_state():
    return {
        "current_gesture": None,
        "gesture_count": 0,
        "confirmed_gesture": None,
        "lost_since": None
    }


def _reset_state(_state):
    _state["current_gesture"] = None
    _state["gesture_count"] = 0
    _state["confirmed_gesture"] = None
    _state["lost_since"] = None


def run(_hands):
    _results = []
    _detected_cameras = set()
    _now = time.monotonic()

    for _hand in _hands:
        _camera_index = _hand["camera_index"]
        _gesture_name = _hand["gesture"]["name"]

        _detected_cameras.add(_camera_index)

        if _camera_index not in _camera_states:
            _camera_states[_camera_index] = _create_state()

        _state = _camera_states[_camera_index]

        _state["lost_since"] = None
        _state["last_hand"] = _hand

        if _gesture_name == "UNKNOWN":
            _reset_state(_state)

        elif _gesture_name == _state["current_gesture"]:
            _state["gesture_count"] += 1

        else:
            _state["current_gesture"] = _gesture_name
            _state["gesture_count"] = 1
            _state["confirmed_gesture"] = None

        if _state["gesture_count"] >= _required_frames:
            _state["confirmed_gesture"] = _gesture_name

        _results.append({
            **_hand,
            "stabilized_gesture": _state["confirmed_gesture"],
            "gesture_count": _state["gesture_count"],
            "is_cached": False
        })

    for _camera_index, _state in _camera_states.items():
        if _camera_index in _detected_cameras:
            continue

        if _state["lost_since"] is None:
            _state["lost_since"] = _now

        if _now - _state["lost_since"] >= _lost_timeout:
            _reset_state(_state)
            continue

        if (
            _state["confirmed_gesture"] is not None
            and _state["last_hand"] is not None
        ):
            _results.append({
                **_state["last_hand"],
                "stabilized_gesture": _state["confirmed_gesture"],
                "gesture_count": _state["gesture_count"],
                "is_cached": True
            })

    return _results