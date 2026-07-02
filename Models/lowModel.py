# lowModel.py
# Norifumi Kondo

import cv2
import mediapipe as mp
import utils.logPrint as p

_initialized = False
_hands: mp.solutions.hands.Hands # type: ignore

# lowモデル用設定
_PROCESS_WIDTH = 640
_PROCESS_HEIGHT = 360
_MAX_HANDS = 1
_MIN_DETECTION_CONFIDENCE = 0.4
_MIN_TRACKING_CONFIDENCE = 0.4


def _startModel():
    global _initialized, _hands

    if _initialized:
        return

    p.info("Lowモデル初期化")

    _mp_hands = mp.solutions.hands # type: ignore
    _hands = _mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=_MAX_HANDS,
        min_detection_confidence=_MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=_MIN_TRACKING_CONFIDENCE
    )

    _initialized = True


def _create_hand_box(_landmarks, _width, _height):
    _xs = [int(_lm.x * _width) for _lm in _landmarks.landmark]
    _ys = [int(_lm.y * _height) for _lm in _landmarks.landmark]

    _x1 = max(min(_xs), 0)
    _y1 = max(min(_ys), 0)
    _x2 = min(max(_xs), _width)
    _y2 = min(max(_ys), _height)

    return {
        "x": _x1,
        "y": _y1,
        "width": _x2 - _x1,
        "height": _y2 - _y1,
        "center_x": (_x1 + _x2) // 2,
        "center_y": (_y1 + _y2) // 2
    }


def _create_landmark_list(_landmarks, _width, _height):
    _landmark_list = []

    for _lm in _landmarks.landmark:
        _landmark_list.append({
            "x": int(_lm.x * _width),
            "y": int(_lm.y * _height),
            "z": _lm.z
        })

    return _landmark_list


def run(_frames):
    global _hands

    _startModel()

    if _hands is None:
        p.error("Lowモデルが初期化されていません")
        return {
            "is_person": False,
            "hands": []
        }

    _hands_data = []

    for _frame in _frames:
        if _frame is None:
            continue

        _resized_frame = cv2.resize(_frame, (_PROCESS_WIDTH, _PROCESS_HEIGHT))
        _rgb_frame = cv2.cvtColor(_resized_frame, cv2.COLOR_BGR2RGB)
        _result = _hands.process(_rgb_frame)

        if not _result.multi_hand_landmarks:
            continue

        for _hand_landmarks in _result.multi_hand_landmarks:
            _box = _create_hand_box(_hand_landmarks, _PROCESS_WIDTH, _PROCESS_HEIGHT)
            _landmarks = _create_landmark_list(_hand_landmarks, _PROCESS_WIDTH, _PROCESS_HEIGHT)

            _hands_data.append({
                "box": _box,
                "landmarks": _landmarks
            })

    return {
        "is_person": len(_hands_data) > 0,
        "hands": _hands_data
    }