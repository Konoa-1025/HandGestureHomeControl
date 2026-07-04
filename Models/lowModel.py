# lowModel.py
# Norifumi Kondo

import cv2
import mediapipe as mp
import utils.logPrint as p

_initialized = False
_hands: mp.solutions.hands.Hands | None = None # type: ignore

# lowモデル用設定
_processWidth = 640
_processHigth = 360
_maxHands = 1
_MIN_DETECTION_CONFIDENCE = 0.4
_MIN_TRACKING_CONFIDENCE = 0.4

def Initialization(_settings):
    global _processWidth
    global _processHigth
    global _maxHands
    global _MIN_DETECTION_CONFIDENCE
    global _MIN_TRACKING_CONFIDENCE

    _processWidth = _settings["process_width"]
    _processHigth = _settings["process_height"]
    _maxHands = _settings["max_hands"]
    _MIN_DETECTION_CONFIDENCE = _settings["detection_confidence"]
    _MIN_TRACKING_CONFIDENCE = _settings["tracking_confidence"]

    return True


def _startModel():
    global _initialized, _hands

    if _initialized:
        return

    p.info("Lowモデル初期化")

    _mp_hands = mp.solutions.hands # type: ignore
    _hands = _mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=_maxHands,
        min_detection_confidence=_MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=_MIN_TRACKING_CONFIDENCE
    )

    _initialized = True


def _create_landmark_list(_landmarks, _scale_x, _scale_y):
    _landmark_list = []

    for _lm in _landmarks.landmark:
        _x = int(_lm.x * _processWidth * _scale_x)
        _y = int(_lm.y * _processHigth * _scale_y)

        _landmark_list.append({
            "x": _x,
            "y": _y,
            "z": _lm.z
        })

    return _landmark_list

def _create_hand_center(_landmarks, _scale_x, _scale_y):
    _xs = [int(_lm.x * _processWidth * _scale_x) for _lm in _landmarks.landmark]
    _ys = [int(_lm.y * _processHigth * _scale_y) for _lm in _landmarks.landmark]

    return {
        "center_x": (min(_xs) + max(_xs)) // 2,
        "center_y": (min(_ys) + max(_ys)) // 2
    }


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

    for _frame_index, _frame in enumerate(_frames):
        if _frame is None:
            continue

        _frame_height, _frame_width = _frame.shape[:2]
        _scale_x = _frame_width / _processWidth
        _scale_y = _frame_height / _processHigth

        _resized_frame = cv2.resize(_frame, (_processWidth, _processHigth))
        _rgb_frame = cv2.cvtColor(_resized_frame, cv2.COLOR_BGR2RGB)
        _result = _hands.process(_rgb_frame)

        if not _result.multi_hand_landmarks:
            continue

        for _hand_landmarks in _result.multi_hand_landmarks:
            _center = _create_hand_center(_hand_landmarks, _scale_x, _scale_y)
            _landmarks = _create_landmark_list(_hand_landmarks, _scale_x, _scale_y)

            _hands_data.append({
                "frame_index": _frame_index,
                "center_x": _center["center_x"],
                "center_y": _center["center_y"],
                "landmarks": _landmarks,
                "model": "low"
            })

    return {
        "is_person": len(_hands_data) > 0,
        "hands": _hands_data
    }