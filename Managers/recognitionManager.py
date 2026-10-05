
#? Managers/recognitionManager.py
#? Norifumi Kondo

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
    if not hand_landmarks.get("hands"):
        return {"name": "UNKNOWN", "fingers": {}}
    recognized_gesture = recognizer.run(hand_landmarks["hands"])
    return recognized_gesture


def gesture_process(hand_landmarks, current_position=None, timestamp=None):
    raw_gesture = get_gesture_data(hand_landmarks)

    point_data = None

    if raw_gesture["name"] == "POINT":
        point_data = pointing.get_direction(hand_landmarks, current_position)#?返り値 角度,方向

    recognized_gesture = stabilizer.stabilizer_process(raw_gesture,point_data,timestamp)#?返り値 確定したジェスチャ,確定した方向

    return recognized_gesture