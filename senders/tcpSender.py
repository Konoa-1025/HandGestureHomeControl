# tcpSender.py
# Norifumi Kondo

import socket
import json
import threading
import time
import struct
from pathlib import Path

import cv2
import utils.logPrint as p


_CONFIG_PATH = Path(__file__).parent / "../config.json"

with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    _config = json.load(f)


_TCP_HOST = _config["tcp_host"]
_LOG_PORT = _config["log_port"]
_RESEARCH_LOG_PORT = _config["research_log_port"]
_FRONT_VIDEO_PORT = _config["front_video_port"]
_SIDE_VIDEO_PORT = _config["side_video_port"]


_log_client = None
_research_log_client = None
_front_video_client = None
_side_video_client = None

_restart_counter_log = 0
_restart_counter_research = 0
_restart_counter_front_video = 0
_restart_counter_side_video = 0


def _connect(port):
    _client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _client.settimeout(3)
    _client.connect((_TCP_HOST, port))
    _client.settimeout(None)
    return _client


def _client_worker(_port, _client_name):
    global _log_client
    global _research_log_client
    global _front_video_client
    global _side_video_client

    _restart_counter = 0

    while True:
        if _client_name == "log":
            _client = _log_client
        elif _client_name == "research":
            _client = _research_log_client
        elif _client_name == "front_video":
            _client = _front_video_client
        elif _client_name == "side_video":
            _client = _side_video_client
        else:
            return

        if _client is None:
            try:
                _new_client = _connect(_port)

                if _client_name == "log":
                    _log_client = _new_client
                elif _client_name == "research":
                    _research_log_client = _new_client
                elif _client_name == "front_video":
                    _front_video_client = _new_client
                elif _client_name == "side_video":
                    _side_video_client = _new_client

                p.success(
                    f"{_TCP_HOST}:{_port} 接続成功",
                    "tcpSender"
                )
                _restart_counter = 0

            except Exception as e:
                _restart_counter += 1

                if _restart_counter >= 5:
                    p.error(
                        f"{_TCP_HOST}:{_port} に接続失敗 ({e})",
                        "tcpSender"
                    )
                    break

                p.warning(
                    f"{_TCP_HOST}:{_port} 接続失敗 ({e}) 5秒後に再試行({_restart_counter}回)",
                    "tcpSender"
                )
                time.sleep(5)

        else:
            time.sleep(0.2)


def connect_all():
    threading.Thread(
        target=_client_worker,
        args=(_LOG_PORT, "log"),
        daemon=True
    ).start()

    threading.Thread(
        target=_client_worker,
        args=(_RESEARCH_LOG_PORT, "research"),
        daemon=True
    ).start()

    threading.Thread(
        target=_client_worker,
        args=(_FRONT_VIDEO_PORT, "front_video"),
        daemon=True
    ).start()

    threading.Thread(
        target=_client_worker,
        args=(_SIDE_VIDEO_PORT, "side_video"),
        daemon=True
    ).start()


def _send_text(_client_name, _text):
    global _log_client
    global _research_log_client

    if _client_name == "log":
        _client = _log_client
    elif _client_name == "research":
        _client = _research_log_client
    else:
        return

    if _client is None:
        return

    try:
        _client.sendall(
            (_text + "\n").encode("utf-8")
        )

    except Exception as e:
        p.error(
            f"{_client_name} 送信失敗 : {e}",
            "tcpSender"
        )

        try:
            _client.close()
        except:
            pass

        if _client_name == "log":
            _log_client = None
        elif _client_name == "research":
            _research_log_client = None


def send_log(text):
    _send_text("log", text)


def send_research_log(text):
    _send_text("research", text)


def _send_frame(_client_name, _frame, _quality=70):
    global _front_video_client
    global _side_video_client

    if _frame is None:
        return

    if _client_name == "front_video":
        _client = _front_video_client
    elif _client_name == "side_video":
        _client = _side_video_client
    else:
        return

    if _client is None:
        return

    try:
        _encode_param = [
            int(cv2.IMWRITE_JPEG_QUALITY),
            _quality
        ]

        _success, _buffer = cv2.imencode(
            ".jpg",
            _frame,
            _encode_param
        )

        if not _success:
            return

        _data = _buffer.tobytes()
        _size = struct.pack(">I", len(_data))

        _client.sendall(_size + _data)

    except Exception as e:
        p.error(
            f"{_client_name} 映像送信失敗 : {e}",
            "tcpSender"
        )

        try:
            _client.close()
        except:
            pass

        if _client_name == "front_video":
            _front_video_client = None
        elif _client_name == "side_video":
            _side_video_client = None


def send_front_frame(_frame):
    _send_frame("front_video", _frame)


def send_side_frame(_frame):
    _send_frame("side_video", _frame)


def close_all():
    global _log_client
    global _research_log_client
    global _front_video_client
    global _side_video_client

    for _client in [
        _log_client,
        _research_log_client,
        _front_video_client,
        _side_video_client
    ]:
        if _client:
            try:
                _client.close()
            except:
                pass

    _log_client = None
    _research_log_client = None
    _front_video_client = None
    _side_video_client = None