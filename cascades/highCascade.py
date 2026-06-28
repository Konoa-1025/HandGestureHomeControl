#cascades/highCascade.py
#Norifumi Kondo
import debug.watching as debugCam

import cv2
import utils.logPrint as p
import managers.cameraManager as camera

_width = 2560
_height = 1440
_resolution = "2560x1440"

def _startCas():
    
    camera.change_resolution(_resolution)
    p.info("起動")

def _casRun(_frame, _left=None, _right=None, _top=None, _bottom=None):
    #リサイズ
    if _resolution == "3840x2160": #すでに解像度が低いならスキップ
        _frame = cv2.resize(_frame, (_width, _height))
    #カット
    if _left is not None :
        _frame = _frame[_top:_bottom, _left:_right]
    # ノイズ処理
    _frame = cv2.GaussianBlur(_frame, (3, 3), 0)
    # RGB変換
    _frame = cv2.cvtColor(_frame, cv2.COLOR_BGR2RGB)
    #カスケード判別用 赤
    _frame = cv2.rectangle(_frame,(0, 0),(100, 100),(0, 0, 255),-1)  

    debugCam.debug(_frame)

    return _frame