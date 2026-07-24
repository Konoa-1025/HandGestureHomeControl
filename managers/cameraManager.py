# cameraManager.py
# Norifumi Kondo

import cv2
import threading
import platform
import utils.logPrint as p
from typing import Optional

_is_debug = True


_config = {}

_captures = []
_current_resolution = "1920x1080" #画質


def Initialization(_settings):
    global _config

    p.info("初期化中")

    _config = _settings.get("camera", _settings)

    if not start_camera():
        if not _debug_camera():
            p.error("初期化失敗")
            return False

    p.success("初期化成功")
    return True

def _make_url(_camera,_resolution=None) -> Optional[str]:#Type=axis URLの生成
    if _camera["type"] == "axis":

        if _resolution is None:
            _resolution = _current_resolution
        return (
            f"http://{_camera['user']}:"
            f"{_camera['password']}@"
            f"{_camera['host']}"
            f"/axis-cgi/mjpg/video.cgi?resolution={_resolution}"
        )

    if _camera["type"] == "url":
        return _camera["url"]

    return None

def _try_open(_url, _timeout=3): #カメラに一時的に接続
    _result = {}

    def _open():
        _cap = cv2.VideoCapture(_url)

        if _cap.isOpened():
            _result["cap"] = _cap
        else:
            _cap.release()

    _thread = threading.Thread(
        target=_open,
        daemon=True
    )

    _thread.start()
    _thread.join(_timeout)

    return _result.get("cap")

def start_camera():
    global _captures

    _captures = []

    _camera_sources = _config.get("cameras") or _config.get("sources") or []
    _max_cameras = int(_config.get("max_cameras", 2))

    for _camera in _camera_sources:
        if len(_captures) >= _max_cameras:
            break

        _url = _make_url(_camera)
        if _url is None:
            p.warning(f"{_camera['name']} URL生成失敗")
            continue

        p.info(f"{_camera['name']} 接続中")

        _cap = _try_open(_url, 5)

        if _cap is None:
            p.warning(f"{_camera['name']} 接続失敗")
            continue

        if _cap.isOpened():
            p.success(f"{_camera['name']} 接続成功")
            _captures.append(_cap)
        else:
            p.warning(f"{_camera['name']} 接続失敗")
            _cap.release()

    if len(_captures) == 0:
        p.error("使用できるネットワークカメラがありません")
        return False

    p.success(f"{len(_captures)}台のカメラを使用します")
    return True

#画質変更
def change_resolution(_resolution):
    global _current_resolution

    if _resolution == _current_resolution:
        return True

    p.info(f"解像度変更 {_current_resolution} → {_resolution}")

    if _is_debug:
        _width, _height = map(int, _resolution.split("x"))

        # (_is_debug = Trueなら)Webカメラでは1920x1080を超える変更を無視
        if _width > 1920 or _height > 1080:
            p.warning(
                f"Webカメラでは {_resolution} に変更できないため、"
                f"{_current_resolution} のまま使用します"
            )
            return True

        for _cap in _captures:
            _cap.set(cv2.CAP_PROP_FRAME_WIDTH, _width)
            _cap.set(cv2.CAP_PROP_FRAME_HEIGHT, _height)

        _current_resolution = _resolution
        return True

    _camera_sources = (
        _config.get("cameras")
        or _config.get("sources")
        or []
    )

    for i, _camera in enumerate(_camera_sources):
        if i >= len(_captures):
            break
        _new_url = _make_url(_camera, _resolution)
        p.info(f"{_camera['name']} 再接続中")
        _new_cap = _try_open(_new_url, 5)
        if _new_cap is None:
            p.warning(f"{_camera['name']} 再接続失敗")
            continue
        _captures[i].release()
        _captures[i] = _new_cap
        p.success(f"{_camera['name']} 解像度変更完了")
    _current_resolution = _resolution
    return True

def read_frames():
    _frames = []

    for _cap in _captures:
        _ret, _frame = _cap.read()

        if _ret:
            _width, _height = map(int, _current_resolution.split("x"))
            _frame = cv2.resize(_frame, (_width, _height))
            _frames.append(_frame)
        else:
            _frames.append(None)

    return _frames


def release_all(): #カメラの開放
    for _cap in _captures:
        _cap.release()

    _captures.clear()

def _debug_camera():  # Windows / Mac のWebカメラに対応
    global _is_debug
    _width, _height = map(int, _current_resolution.split("x"))

    # OSごとにOpenCVのカメラバックエンドを切り替える
    if platform.system() == "Windows":
        _backend = cv2.CAP_DSHOW
    elif platform.system() == "Darwin":
        _backend = cv2.CAP_AVFOUNDATION
    else:
        _backend = cv2.CAP_ANY

    for i in range(10):
        p.info(f"Webカメラ確認中 index={i}")
        _cap = cv2.VideoCapture(i, _backend)
        if not _cap.isOpened():
            _cap.release()
            continue
        # Webカメラに希望解像度を設定
        _cap.set(cv2.CAP_PROP_FRAME_WIDTH, _width)
        _cap.set(cv2.CAP_PROP_FRAME_HEIGHT, _height)
        # WindowsではMJPEGにすると高解像度で動きやすい
        if platform.system() == "Windows":
            _cap.set(
                cv2.CAP_PROP_FOURCC,
                cv2.VideoWriter_fourcc(*"MJPG") #type: ignore
            )
        _ret, _frame = _cap.read()

        if _ret and _frame is not None:
            p.info(
                f"Camera {i}: "
                f"{_frame.shape[1]}x{_frame.shape[0]}"
            )
            _captures.append(_cap)
            _is_debug = True
            p.success(
                f"Webカメラ接続成功 index={i}"
            )
            return True
        _cap.release()

    p.error("Webカメラ接続失敗")
    return False