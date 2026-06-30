#standbyModel.py
#Norifumi Kondo
import utils.logPrint as p

import cv2
import mediapipe as mp

def _startModel():
    p.info("切り替わりました。")


mp_hands = mp.solutions.hands  # type: ignore[attr-defined]
_hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

p.info("起動")

def run(_frames):
    if _frames is None:
        p.error("standbyModel: フレームがNoneです")
        return False

    if not isinstance(_frames, list):
        _frames = [_frames]

    for _frame in _frames:
        if _frame is None:
            continue

        _rgb = cv2.cvtColor(_frame, cv2.COLOR_BGR2RGB)
        _results = _hands.process(_rgb)

        if _results.multi_hand_landmarks:
            p.success("手を検出しました")
            return True

    return False