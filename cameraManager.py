# cameraManager.py
# Norifumi Kondo
import os
import cv2
import json
from pathlib import Path
import logPrint as p
import threading

p.info("起動")

_CONFIG_PATH = Path(__file__).parent / "config.json"

with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    _config = json.load(f)

_captures = []


def _make_url(_camera) -> str | None:
    if _camera["type"] == "axis":
        return (
            f"http://{_camera['user']}:"
            f"{_camera['password']}@"
            f"{_camera['host']}"
            "/axis-cgi/mjpg/video.cgi"
        )

    if _camera["type"] == "url":
        return _camera["url"]

    return None

def _try_open(_url, _timeout=3):
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

    for _camera in _config["cameras"]:
        if len(_captures) >= 2:
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
        p.error("使用できるカメラがありません")
        return False

    p.success(f"{len(_captures)}台のカメラを使用します")
    return True


def read_frames():
    _frames = []

    for _cap in _captures:
        _ret, _frame = _cap.read()

        if _ret:
            _frames.append(_frame)
        else:
            _frames.append(None)

    return _frames


def release_all():
    for _cap in _captures:
        _cap.release()

    _captures.clear()