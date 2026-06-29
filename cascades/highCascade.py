#cascades/highCascade.py
#Norifumi Kondo
import debug.watching as debugCam

import cv2
import utils.logPrint as p
import managers.cameraManager as camera

_width = 3840
_height = 2160

def Initialization(_highWidth,_highHeight):
    global _width
    global _height

    _width = _highWidth
    _height = _highHeight

def _startCas():
    
    camera.change_resolution(f"{_width}x{_height}")
    p.info("起動")

def _casRun(_frame,_camera_name="Camera",_mediaROI=None, _left=None, _right=None, _top=None, _bottom=None):
    #リサイズ ネットワークカメラでリサイズできるならスキップ
    if _frame.shape[1] != _width or _frame.shape[0] != _height:
        _frame = cv2.resize(_frame, (_width, _height))
    #カット
    if _left is not None :
        _frame = _frame[_top:_bottom, _left:_right]
    # ノイズ処理
    _frame = cv2.GaussianBlur(_frame, (3, 3), 0)
    # RGB変換
    _frame = cv2.cvtColor(_frame, cv2.COLOR_BGR2RGB)
    #カスケード判別用 赤
    _frame = cv2.rectangle(_frame,(0, 0),(100, 100),(255, 0, 0),-1)  

    # 表示用だけRGB → BGRに戻す
    _debug_frame = cv2.cvtColor(_frame, cv2.COLOR_RGB2BGR)

    debugCam.debug(_debug_frame, _camera_name, 960, 540)

    return _frame