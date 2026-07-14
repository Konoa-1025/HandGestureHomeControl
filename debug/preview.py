#preview.py
#Norifumi Konndo
#フレームの映像を確認する
import cv2


_windows = set()

def show(_frame, _name="Preview", _width=1280, _height=720):
    if _name not in _windows:
        cv2.namedWindow(_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(_name, _width, _height)
        _windows.add(_name)

    cv2.imshow(_name, _frame)
    cv2.waitKey(1)


def modelPreview(_frame, _name, _landmarks=None):
    _preview_frame = _frame.copy()
    _connections = [
        (0,1),(1,2),(2,3),(3,4),
        (0,5),(5,6),(6,7),(7,8),
        (5,9),(9,10),(10,11),(11,12),
        (9,13),(13,14),(14,15),(15,16),
        (13,17),(17,18),(18,19),(19,20),
        (0,17)
    ]

    if _landmarks is not None:
        for _start, _end in _connections:
            cv2.line(
                _preview_frame,
                (_landmarks[_start]["x"], _landmarks[_start]["y"]),
                (_landmarks[_end]["x"], _landmarks[_end]["y"]),
                (255, 255, 255),
                2
            )
        for _point in _landmarks:
            cv2.circle(
                _preview_frame,
                (_point["x"], _point["y"]),
                4,
                (0, 255, 0),
                -1
            )

    show(_preview_frame, _name)