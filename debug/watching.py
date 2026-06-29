import cv2

_windows = set()

def debug(_frame, _name="Debug", _width=1280, _height=720):
    if _name not in _windows:
        cv2.namedWindow(_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(_name, _width, _height)
        _windows.add(_name)

    cv2.imshow(_name, _frame)
    cv2.waitKey(1)

def destroy():
    cv2.destroyAllWindows()
    _windows.clear()