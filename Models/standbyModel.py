# standbyModel.py
# Norifumi Kondo
import utils.logPrint as p
import cv2

_prev_frame = None
_THRESHOLD = 25      # 差分の感度（大きいほど鈍感）
_MIN_PIXELS = 1000   # 動きと判断するピクセル数

def Initialization(_settings):
    global _THRESHOLD
    global _MIN_PIXELS

    _THRESHOLD = _settings["threshold"]
    _MIN_PIXELS = _settings["min_pixels"]

    return True


p.info("起動")

def run(_frames):
    global _prev_frame

    if _frames is None:
        p.error("standbyModel: フレームがNoneです")
        return False

    if not isinstance(_frames, list):
        _frames = [_frames]

    for _frame in _frames:
        if _frame is None:
            continue

        #グレースケールにする
        gray = cv2.cvtColor(_frame, cv2.COLOR_BGR2GRAY)

        if _prev_frame is None:
            _prev_frame = gray
            continue

        if _prev_frame.shape != gray.shape:
            _prev_frame = gray
            return True

        diff = cv2.absdiff(_prev_frame, gray)
        _prev_frame = gray

        #動きを確認
        moved = cv2.countNonZero(
            cv2.threshold(diff, _THRESHOLD, 255, cv2.THRESH_BINARY)[1]
        ) > _MIN_PIXELS

        if moved:
            #p.success("動きを検出しました")
            return True

    return False