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

def _casRun(_frame,_mediaROI=None, _left=None, _right=None, _top=None, _bottom=None):
    #リサイズ
    if _frame.shape[1] != _width or _frame.shape[0] != _height:
        _frame = cv2.resize(_frame, (_width, _height))
    #カット
    if _mediaROI is not None : #MediaPipeからROIが受け取れなかったら計算をする。
        if _left is not None : #ROI計算に使う値がなかったらカットを行わない
            _frame = _frame[_top:_bottom, _left:_right]
    # ノイズ処理
    _frame = cv2.GaussianBlur(_frame, (3, 3), 0)
    # RGB変換
    _frame = cv2.cvtColor(_frame, cv2.COLOR_BGR2RGB)
    #カスケード判別用 青
    _frame = cv2.rectangle(_frame,(0, 0),(100, 100),(255, 0, 0),-1) 
    debugCam.debug(_frame)

    return _frame