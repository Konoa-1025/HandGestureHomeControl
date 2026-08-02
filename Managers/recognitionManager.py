
#? Managers/recognitionManager.py
#? Norifumi Konndo

import Utils.logger as p
import Recognizers.gestureRecognizer as recognizer
import Recognizers.gestureStabilizer as stabilizer
import Recognizers.pointingEstimator as pointing


def Initialization(settings):

    p.info("recognitionManagerを初期化中")

    p.success("recognitionManagerの初期化完了")

    p.info("recognizerの初期化中")
    if not recognizer.Initialization(settings):
        p.error("recognizerの初期化に失敗しました")
        return False
    if not stabilizer.Initialization(settings):
        p.error("stabilizerの初期化に失敗しました")
        return False
    if not pointing.Initialization(settings):
        p.error("pointingの初期化に失敗しました")
        return False

    return True

def get_gesture_data(hand_landmarks):
    recognized_gesture = recognizer.run(hand_landmarks["hands"])
    return recognized_gesture

def gesture_process(hand_landmarks):
    raw_gesture = get_gesture_data(hand_landmarks) #?返り値：現在の認識ジェスチャ,指毎の判定
    if raw_gesture["name"] == "POINT":
        point_data = pointing.get_direction(hand_landmarks)#?返り値：角度,方向
    #recognized_gesture = stabilizer.stabilizer_precess(hand_landmarks,point_data)
    return{}