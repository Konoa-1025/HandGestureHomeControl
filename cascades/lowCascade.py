#cascades/lowCascade.py
#Norifumi Kondo
import cv2
import utils.logPrint as p
import managers.cameraManager as camera

#low
_width = 1920
_height = 1080

def Initialization(_settings):
    global _width
    global _height

    p.info("初期化中")

    _width = _settings["width"]
    _height = _settings["height"]

    p.success("初期化成功")
    return True

def _startCas(): #ネットワークカメラ用
    
    camera.change_resolution(f"{_width}x{_height}")
    p.info("起動")

def _casRun(_frame):
    # リサイズ
    if _frame.shape[1] != _width or _frame.shape[0] != _height:
        _frame = cv2.resize(_frame, (_width, _height))

    # ノイズ処理
    _frame = cv2.GaussianBlur(_frame, (3, 3), 0)

    # カスケード判別用 青（BGR）
    #_frame = cv2.rectangle(_frame, (0, 0), (100, 100), (255, 0, 0), -1)

    # *? デバッグ用確認カメラ
    #debugCam.show(_frame, _camera_name, 960, 540)

    return _frame