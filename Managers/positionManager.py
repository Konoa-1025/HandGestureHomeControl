"""人物位置の窓口。mainはupdate(frame)から畳IDまたはNoneを受け取る。"""
import numpy as np
import Utils.logger as p
from Position.tatamiMap import TatamiMap

estimator = None


class HumanPosition:
    def __init__(self, tatami_map, detector, bottom_ratio=0.3, debug=False):
        if not 0 < bottom_ratio <= 1:
            raise ValueError("bottom_ratioは0より大きく1以下にしてください")
        self.tatami_map = tatami_map
        self.detector = detector
        self.bottom_ratio = bottom_ratio
        self.debug = debug
        self.current_position = None
        self.bounding_box = None
        self.position_box = None

    def update(self, frame):
        self.current_position = self.bounding_box = self.position_box = None
        if frame is None:
            return None
        box = self.detector.detect(frame)
        if box is None or len(box) != 4 or not np.all(np.isfinite(box)):
            return None
        height, width = frame.shape[:2]
        x1, y1, x2, y2 = box
        x1, x2 = np.clip([x1, x2], 0, width)
        y1, y2 = np.clip([y1, y2], 0, height)
        if x2 <= x1 or y2 <= y1:
            return None
        self.bounding_box = (x1, y1, x2, y2)
        self.position_box = (x1, y2 - (y2 - y1) * self.bottom_ratio, x2, y2)
        self.current_position = self.tatami_map.locate(self.position_box, frame.shape)
        return self.current_position


def Initialization(config):
    global estimator
    close()
    settings = config.get("position", {})
    if not settings.get("enabled", False):
        return True
    detector = None
    try:
        tatami_map = TatamiMap(settings["csv_path"], settings["image_size"], settings.get("image_rect"))
        from Recognizers.personDetector import PersonDetector
        detector = PersonDetector()
        estimator = HumanPosition(tatami_map, detector, settings.get("bottom_ratio", 0.3), settings.get("debug", False))
        p.success("人物位置推定の初期化完了")
    except Exception as error:
        if detector is not None:
            detector.close()
        p.warning(f"人物位置推定を無効化しました: {error}")
    # 位置推定が利用できない場合も既存の手認識は続行する。
    return True


def update(frame):
    global estimator
    if estimator is None:
        return None
    try:
        return estimator.update(frame)
    except Exception as error:
        p.warning(f"人物位置推定を停止しました: {error}")
        close()
        return None


def get_debug_state():
    return estimator if estimator is not None and estimator.debug else None


def close():
    global estimator
    previous, estimator = estimator, None
    if previous is not None:
        previous.detector.close()
