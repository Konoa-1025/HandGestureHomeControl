#cascades/lowCascade.py
#Norifumi Kondo
import debug.watching as debugCam

import cv2
import utils.logPrint as p
import managers.cameraManager as camera

#low
_width = 1920
_height = 1080

def Initialization(_lowWidth,_lowHeight):
    global _width
    global _height

    _width = _lowWidth
    _height = _lowHeight

def _startCas(): #ネットワークカメラ用
    
    camera.change_resolution(f"{_width}x{_height}")
    p.info("起動")

def _casRun(_frame, _camera_name="Camera", _mediaROI=None, _left=None, _right=None, _top=None, _bottom=None):
    #print(_mediaROI)
    # リサイズ
    if _frame.shape[1] != _width or _frame.shape[0] != _height:
        _frame = cv2.resize(_frame, (_width, _height))

    # ROI辞書が渡された場合
    if _mediaROI is not None:
        _left = _mediaROI["left"]
        _right = _mediaROI["right"]
        _top = _mediaROI["top"]
        _bottom = _mediaROI["bottom"]

    # カット
    if (
        _left is not None and _right is not None and
        _top is not None and _bottom is not None and
        _right > _left and _bottom > _top
    ):
        _frame = _frame[_top:_bottom, _left:_right]

        # ROIを全体解像度へ拡大し、ズーム状態のまま次段へ渡す
        if _frame.shape[1] != _width or _frame.shape[0] != _height:
            _frame = cv2.resize(_frame, (_width, _height))

    # ノイズ処理
    _frame = cv2.GaussianBlur(_frame, (3, 3), 0)

    # カスケード判別用 青（BGR）
    _frame = cv2.rectangle(_frame, (0, 0), (100, 100), (255, 0, 0), -1)

    # デバッグ用確認カメラ
    debugCam.debug(_frame, _camera_name, 960, 540)

    return _frame