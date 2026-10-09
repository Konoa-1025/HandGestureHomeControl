
#? Managers/recognitionManager.py
#? Norifumi Kondo

import time
import Utils.logger as p
import Recognizers.gestureRecognizer as recognizer
import Recognizers.gestureStabilizer as stabilizer
import Recognizers.pointingEstimator as pointing


def Initialization(settings):
    p.info("recognitionManagerを初期化中")

    if not recognizer.Initialization(settings):
        p.error("recognizerの初期化に失敗しました")
        return False

    if not stabilizer.Initialization(settings):
        p.error("stabilizerの初期化に失敗しました")
        return False

    if not pointing.Initialization(settings):
        p.error("pointingの初期化に失敗しました")
        return False

    p.success("recognitionManagerの初期化完了")
    return True


def get_gesture_data(hand_landmarks):
    recognized_gesture = recognizer.run(hand_landmarks["hands"])
    return recognized_gesture


def gesture_process(hand_landmarks, timestamp=None, frame_shape=None, allow_selection=True):
    raw_gesture = get_gesture_data(hand_landmarks)#?返り値 現在のジェスチャ,各指の状態

    point_data = None

    if raw_gesture["name"] == "POINT":
        point_data = pointing.get_direction(hand_landmarks)#?返り値 角度,方向

    recognized_gesture = stabilizer.stabilizer_process(raw_gesture,point_data,timestamp)#?返り値 確定したジェスチャ,確定した方向

    recognized_gesture["raw_gesture"] = raw_gesture["name"]
    recognized_gesture["target"] = None
    recognized_gesture["point_data"] = None
    if pointing.enabled and frame_shape is not None:
        now = time.monotonic() if timestamp is None else timestamp
        result = pointing.get_target(hand_landmarks, frame_shape, raw_gesture)
        recognized_gesture["point_data"] = result
        recognized_gesture["target"] = stabilizer.target_process(
            result, now, pointing.hold_seconds, pointing.gap_tolerance_seconds, allow_selection
        )

    return recognized_gesture
