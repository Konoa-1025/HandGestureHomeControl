
#? Managers/recognitionManager.py
#? Norifumi Konndo

import Utils.logger as p
import Recognizers.gestureRecognizer as recognizer
import Recognizers.gestureStabilizer as stabilizer


def Initialization(settings):

    p.info("recognitionManagerを初期化中")

    p.success("recognitionManagerの初期化完了")

    return True

def gesture_process(hand_landmarks):
    recognized_gesture = recognizer.run(hand_landmarks["hands"])
    return recognized_gesture