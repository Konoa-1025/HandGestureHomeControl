#managers/cascadeManager.py
#Norifumi Konndo
import utils.logPrint as p
import cascades.highCascade as highCas
import cascades.lowCascade as lowCas

_crop_size = 200
_hand_positions = {}
_last_frame_transforms = {}
_lost_count = 0
_LOST_LIMIT = 10


def Initialization(_low,_high,_lowWidth,_lowHeight,_highWidth,_highHeight,_lostlim,_lostCo,_cropSize):
    _intflg = True
    global _current 
    global _memory_high
    global _memory_low
    global _last_frame_transforms
    global _lost_count
    global _LOST_LIMIT
    global _crop_size
    _current = "low"
    _memory_low = _low
    _memory_high = _high
    _last_frame_transforms = {}
    _lost_count = _lostCo
    _LOST_LIMIT = _lostlim
    _crop_size = _cropSize
    _intflg = lowCas.Initialization(_lowWidth,_lowHeight)
    _intflg = highCas.Initialization(_highWidth,_highHeight)
    p.success("初期化終了")
    return _intflg

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

    left = max(0, _center_x - _crop_size)
    right = min(_frame_width, _center_x + _crop_size)
    top = max(0, _center_y - _crop_size)
    bottom = min(_frame_height, _center_y + _crop_size)

    return {
        "left": left,
        "right": right,
        "top": top,
        "bottom": bottom,
        "center_x": _center_x,
        "center_y": _center_y
    }


def _to_global_position(_index, _center_x, _center_y):
    _transform = _last_frame_transforms.get(_index)

    if _transform is None or not _transform["is_cropped"]:
        return _center_x, _center_y

    _out_width = _transform["out_width"]
    _out_height = _transform["out_height"]
    _crop_width = _transform["right"] - _transform["left"]
    _crop_height = _transform["bottom"] - _transform["top"]

    if _out_width <= 0 or _out_height <= 0 or _crop_width <= 0 or _crop_height <= 0:
        return _center_x, _center_y

    _global_x = _transform["left"] + int(_center_x * _crop_width / _out_width)
    _global_y = _transform["top"] + int(_center_y * _crop_height / _out_height)

    _global_x = max(0, min(_transform["frame_width"] - 1, _global_x))
    _global_y = max(0, min(_transform["frame_height"] - 1, _global_y))

    return _global_x, _global_y


def updateHandPositions(_result, _frames):
    global _hand_positions, _lost_count

    if not _result["is_person"]:
        _lost_count += 1

        if _lost_count >= _LOST_LIMIT:
            _hand_positions.clear()
            _lost_count = 0
            #p.info("手位置リセット")

        return

    _lost_count = 0
    _hand_positions.clear()

    for _hand in _result["hands"]:
        _index = _hand["frame_index"]

        if _index < 0 or _index >= len(_frames):
            continue

        if _frames[_index] is None:
            continue

        _center_x, _center_y = _to_global_position(
            _index,
            _hand["center_x"],
            _hand["center_y"]
        )

        _height, _width = _frames[_index].shape[:2]

        _hand_positions[_index] = _handPosition(
            _center_x,
            _center_y,
            _width,
            _height
        )

    #p.info(f"保存後: {_hand_positions}")

def run(_frames):
    global _last_frame_transforms

    _last_frame_transforms = {}

    for i in range(len(_frames)):
        if _frames[i] is None:
            continue

        _frame_height, _frame_width = _frames[i].shape[:2]
        _camera_name = f"Camera {i + 1}"

        _crop = _hand_positions.get(i)

        _left = 0
        _right = _frame_width
        _top = 0
        _bottom = _frame_height
        _is_cropped = False

        if _crop is not None:
            _left = max(0, min(_frame_width, int(_crop["left"])))
            _right = max(0, min(_frame_width, int(_crop["right"])))
            _top = max(0, min(_frame_height, int(_crop["top"])))
            _bottom = max(0, min(_frame_height, int(_crop["bottom"])))
            _is_cropped = _right > _left and _bottom > _top

        if _current == "low":
            _frames[i] = lowCas._casRun(
                _frames[i],
                _camera_name,
                _crop
            )
        else:
            _frames[i] = highCas._casRun(
                _frames[i],
                _camera_name,
                _crop
            )

        _out_height, _out_width = _frames[i].shape[:2]
        _last_frame_transforms[i] = {
            "is_cropped": _is_cropped,
            "left": _left,
            "right": _right,
            "top": _top,
            "bottom": _bottom,
            "out_width": _out_width,
            "out_height": _out_height,
            "frame_width": _frame_width,
            "frame_height": _frame_height
        }

    return _frames