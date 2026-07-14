# highModel.py
#Norifumi Kondo
import cv2
import mediapipe as mp
import utils.logPrint as p
import debug.preview as preview

_initialized = False
_hands: mp.solutions.hands.Hands | None = None # type: ignore

# highモデル用初期設定
_processWidth = 1280
_processHeight = 720
_maxHands = 2
_min_detection_confidence = 0.7
_min_tracking_confidence = 0.7

def Initialization(_settings):
    global _processWidth
    global _processHeight
    global _maxHands
    global _min_detection_confidence
    global _min_tracking_confidence

    _processWidth = _settings["process_width"]
    _processHeight = _settings["process_height"]
    _maxHands = _settings["max_hands"]
    _min_detection_confidence = _settings["detection_confidence"]
    _min_tracking_confidence = _settings["tracking_confidence"]

    return True



def _startModel():
    global _initialized, _hands

    if _initialized:
        return

    p.info("highモデル初期化")

    _mp_hands = mp.solutions.hands # type: ignore
    _hands = _mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=_maxHands,
        model_complexity=1,
        min_detection_confidence=_min_detection_confidence,
        min_tracking_confidence=_min_tracking_confidence
    )

    _initialized = True


def _create_landmark_list(_landmarks, _scale_x, _scale_y):
    _landmark_list = []

    for _lm in _landmarks.landmark:
        _x = int(_lm.x * _processWidth * _scale_x)
        _y = int(_lm.y * _processHeight * _scale_y)

        _landmark_list.append({
            "x": _x,
            "y": _y,
            "z": _lm.z,
            "visibility": _lm.visibility if hasattr(_lm, "visibility") else 0,
            "presence": _lm.presence if hasattr(_lm, "presence") else 0
        })

    return _landmark_list


def run(_frames):
    global _hands

    _startModel()

    if _hands is None:
        p.error("highモデルが初期化されていません")
        return {
            "is_person": False,
            "hands": []
        }

    _hands_data = []

    for _frame_index, _frame in enumerate(_frames):
        _camera_name = f"highModel Camera {_frame_index + 1}"
        if _frame is None:
            continue

        _frame_height, _frame_width = _frame.shape[:2]
        _scale_x = _frame_width / _processWidth
        _scale_y = _frame_height / _processHeight

        _resized_frame = cv2.resize(_frame, (_processWidth, _processHeight))
        _rgb_frame = cv2.cvtColor(_resized_frame, cv2.COLOR_BGR2RGB)
        _result = _hands.process(_rgb_frame)

        if not _result.multi_hand_landmarks:
            preview.show(_frame, _camera_name) # ?プレビュー用
            continue

        for _hand_landmarks in _result.multi_hand_landmarks:
            _landmarks = _create_landmark_list(_hand_landmarks, _scale_x, _scale_y)

            _hand_data = {
                "frame_index": _frame_index,
                "landmarks": _landmarks,
                "model": "high"
            }

            _hands_data.append(_hand_data)

            # ?プレビュー用
            preview.modelPreview(
                _frame,
                _camera_name,
                _landmarks
            )   

    return {
        "is_person": len(_hands_data) > 0,
        "hands": _hands_data
    }