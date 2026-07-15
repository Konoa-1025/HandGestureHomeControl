#gestureRecognizer.py
#Norifumi Konndo
#ランドマークから手の形を推測する
import math
import utils.logPrint as p


_settings = {}

def Initialization(settings):

    global _settings

    p.info("初期化中")
    _settings = settings

    p.success("初期化成功")
    return True

def run(_handpoints):
    _hands = []

    for _handpoint in _handpoints:
        _landmarks = _handpoint["landmarks"]
        _gesture = recognize(_landmarks)

        _hands.append({
            **_handpoint,
            "gesture": _gesture
        })
    
    return _hands


def _calculate_angle(point_a, point_b, point_c):
    """
    point_bを中心とした角度を求める
    """
    vector_ba = (
        point_a["x"] - point_b["x"],
        point_a["y"] - point_b["y"]
    )

    vector_bc = (
        point_c["x"] - point_b["x"],
        point_c["y"] - point_b["y"]
    )

    dot = (
        vector_ba[0] * vector_bc[0]
        + vector_ba[1] * vector_bc[1]
    )

    length_ba = math.hypot(vector_ba[0], vector_ba[1])
    length_bc = math.hypot(vector_bc[0], vector_bc[1])

    if length_ba == 0 or length_bc == 0:
        return 0.0

    cos_value = dot / (length_ba * length_bc)
    cos_value = max(-1.0, min(1.0, cos_value))

    return math.degrees(math.acos(cos_value))


def _is_finger_extended(landmarks, mcp_index, pip_index, dip_index, tip_index):
    pip_angle = _calculate_angle(
        landmarks[mcp_index],
        landmarks[pip_index],
        landmarks[dip_index]
    )

    dip_angle = _calculate_angle(
        landmarks[pip_index],
        landmarks[dip_index],
        landmarks[tip_index]
    )

    return pip_angle >= 150 and dip_angle >= 150


def recognize(landmarks):
    if not landmarks or len(landmarks) < 21:
        return {
            "name": "UNKNOWN",
            "fingers": {}
        }

    fingers = {
        "index": _is_finger_extended(landmarks, 5, 6, 7, 8),
        "middle": _is_finger_extended(landmarks, 9, 10, 11, 12),
        "ring": _is_finger_extended(landmarks, 13, 14, 15, 16),
        "pinky": _is_finger_extended(landmarks, 17, 18, 19, 20)
    }

    #! ランドマークから手の形にする

    gesture_name = "UNKNOWN"

    if all(fingers.values()):
        gesture_name = "OPEN_HAND" #パー

    elif not any(fingers.values()):
        gesture_name = "FIST"   #グー

    elif (
        fingers["index"]
        and not fingers["middle"]
        and not fingers["ring"]
        and not fingers["pinky"]
    ):
        gesture_name = "POINT"  #指差し
    
    elif (
        fingers["index"]
        and fingers["middle"]
        and not fingers["ring"]
        and not fingers["pinky"]
    ):
        gesture_name = "PEACE"  #チョキ

    return {
        "name": gesture_name,
        "fingers": fingers
    }