# gestureStabilizer.py
# Norifumi Kondo
# 手の形を複数フレームから確定する
import utils.logPrint as p

# gestureStabilizer.py

_required_frames = 5
_camera_states = {}


def Initialization(_settings):
    global _required_frames
    global _camera_states

    _required_frames = _settings.get("required_frames", 5)
    _camera_states = {}

    return True


def _create_state():
    return {
        "current_gesture": None,
        "gesture_count": 0,
        "confirmed_gesture": None
    }


def run(_hands):
    _results = []

    for _hand in _hands:
        _camera_index = _hand["camera_index"]
        _gesture_name = _hand["gesture"]["name"]

        if _camera_index not in _camera_states:
            _camera_states[_camera_index] = _create_state()

        _state = _camera_states[_camera_index]

        if _gesture_name == "UNKNOWN":
            _state["current_gesture"] = None
            _state["gesture_count"] = 0
            _state["confirmed_gesture"] = None

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
            "gesture_count": _state["gesture_count"]
        })
    
    return _results