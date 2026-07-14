# pointingEstimator.py
# Norifumi Kondo
# 指差し方向を推定する

_min_vector_length = 30


def Initialization(_settings):
    global _min_vector_length

    _min_vector_length = _settings.get("min_vector_length", 30)

    return True


import math


def _estimate_direction(_landmarks):
    _mcp = _landmarks[5]
    _tip = _landmarks[8]

    _dx = _tip["x"] - _mcp["x"]
    _dy = _tip["y"] - _mcp["y"]

    _length = math.hypot(_dx, _dy)

    if _length < _min_vector_length:
        return "UNKNOWN"

    # 画像ではyが下向きに増えるので、符号を反転
    _angle = math.degrees(math.atan2(-_dy, _dx))

    #画像内での角度から色々やる

    if -22.5 <= _angle < 22.5:
        return "RIGHT"
    elif 22.5 <= _angle < 67.5:
        return "UP_RIGHT"
    elif 67.5 <= _angle < 112.5:
        return "UP"
    elif 112.5 <= _angle < 157.5:
        return "UP_LEFT"
    elif _angle >= 157.5 or _angle < -157.5:
        return "LEFT"
    elif -157.5 <= _angle < -112.5:
        return "DOWN_LEFT"
    elif -112.5 <= _angle < -67.5:
        return "DOWN"
    else:
        return "DOWN_RIGHT"


def run(_gestures):
    _results = []

    for _gesture in _gestures:
        _result = {
            **_gesture,
            "direction": None
        }

        if _gesture.get("stabilized_gesture") == "POINT":
            _result["direction"] = _estimate_direction(
                _gesture["landmarks"]
            )

        _results.append(_result)

    return _results