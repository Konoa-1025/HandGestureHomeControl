#managers/cascadeManager.py
#Norifumi Konndo
import utils.logPrint as p
import cascades.highCascade as highCas
import cascades.lowCascade as lowCas

_crop_size = 500

def Initialization(_low,_high,_lowWidth,_lowHeight,_highWidth,_highHeight):
    global _current 
    global _memory_high
    global _memory_low
    lowCas.Initialization(_lowWidth,_lowHeight)
    highCas.Initialization(_highWidth,_highHeight)

    _current = "low"
    _memory_low = _low
    _memory_high = _high

def update(_system):
    global _current

    _memory = _system["memory"]
    _cpu = _system["cpu"]

    if _cpu >= 90:
        if _current != "low":
            _current = "low"
            p.info("CPU高負荷：カスケード low")
            lowCas._startCas()
        return _current

    if _current == "high":
        if _memory >= _memory_high:
            _current = "low"
            p.info(f"カスケード：low {_memory}")
            lowCas._startCas()

    elif _current == "low":
        if _memory <= _memory_low:
            _current = "high"
            p.info(f"カスケード：high {_memory}")
            highCas._startCas()

    return _current

def _handPosition(_center_x, _center_y, _frame_width, _frame_height):

    left = _center_x - _crop_size
    right = _center_x + _crop_size
    top = _center_y - _crop_size
    bottom = _center_y + _crop_size

    # 画像外に出ないように補正
    left = max(0, left)
    top = max(0, top)
    right = min(_frame_width, right)
    bottom = min(_frame_height, bottom)
    return left, right, top, bottom

def run(_frames):
    for i in range(len(_frames)):
        if _frames[i] is None:
            continue

        _camera_name = f"Camera {i + 1}"

        if _current == "low":
            _frames[i] = lowCas._casRun(_frames[i], _camera_name)
        else:
            _frames[i] = highCas._casRun(_frames[i], _camera_name)