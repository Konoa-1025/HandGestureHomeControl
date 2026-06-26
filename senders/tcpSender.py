# tcpSender.py
# Norifumi Kondo

import socket
import threading
import time
import struct

import cv2
import utils.logPrint as p


_tcp_hosts = []
_ports = {}
_selected_host = None

_log_client = None
_research_log_client = None
_front_video_client = None
_side_video_client = None


def _connect(_port):
    global _selected_host

    _hosts = [_selected_host] if _selected_host else _tcp_hosts

    for _host in _hosts:
        _client = None

        try:
            _client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _client.settimeout(3)
            _client.connect((_host, _port))
            _client.settimeout(None)

            if _selected_host is None:
                _selected_host = _host
                p.success(f"TCP接続先を採用: {_selected_host}", "tcpSender")

            return _client

        except Exception:
            if _client:
                try:
                    _client.close()
                except Exception:
                    pass

    raise ConnectionError("接続できるTCPホストがありません")


def _set_client(_client_name, _client):
    global _log_client
    global _research_log_client
    global _front_video_client
    global _side_video_client

    if _client_name == "log":
        _log_client = _client
    elif _client_name == "research":
        _research_log_client = _client
    elif _client_name == "front_video":
        _front_video_client = _client
    elif _client_name == "side_video":
        _side_video_client = _client


def _get_client(_client_name):
    if _client_name == "log":
        return _log_client
    if _client_name == "research":
        return _research_log_client
    if _client_name == "front_video":
        return _front_video_client
    if _client_name == "side_video":
        return _side_video_client

    return None


def _client_worker(_port, _client_name):
    _restart_counter = 0

    while True:
        _client = _get_client(_client_name)

        if _client is None:
            try:
                _new_client = _connect(_port)
                _set_client(_client_name, _new_client)

                p.success(
                    f"{_selected_host}:{_port} 接続成功",
                    "tcpSender"
                )

                _restart_counter = 0

            except Exception as e:
                _restart_counter += 1

                if _restart_counter >= 5:
                    p.error(
                        f"{_client_name} 接続失敗: {e}",
                        "tcpSender"
                    )
                    break

                p.warning(
                    f"{_client_name} 接続失敗: {e} 5秒後に再試行({_restart_counter}回)",
                    "tcpSender"
                )
                time.sleep(5)

        else:
            time.sleep(0.2)


def connect_all(_config):
    global _tcp_hosts
    global _ports

    _tcp_hosts = _config["tcp"]["hosts"]
    _ports = _config["tcp"]["ports"]

    threading.Thread(
        target=_client_worker,
        args=(_ports["log"], "log"),
        daemon=True
    ).start()

    threading.Thread(
        target=_client_worker,
        args=(_ports["research_log"], "research"),
        daemon=True
    ).start()

    threading.Thread(
        target=_client_worker,
        args=(_ports["front_video"], "front_video"),
        daemon=True
    ).start()

    threading.Thread(
        target=_client_worker,
        args=(_ports["side_video"], "side_video"),
        daemon=True
    ).start()


def _disconnect_client(_client_name):
    _client = _get_client(_client_name)

    if _client:
        try:
            _client.close()
        except Exception:
            pass

    _set_client(_client_name, None)


def _send_text(_client_name, _text):
    _client = _get_client(_client_name)

    if _client is None:
        return

    try:
        _client.sendall((_text + "\n").encode("utf-8"))

    except Exception as e:
        p.error(
            f"{_client_name} 送信失敗: {e}",
            "tcpSender"
        )
        _disconnect_client(_client_name)


def send_log(_text):
    _send_text("log", _text)


def send_research_log(_text):
    _send_text("research", _text)


def _send_frame(_client_name, _frame, _quality=70):
    if _frame is None:
        return

    _client = _get_client(_client_name)

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
            f"{_client_name} 映像送信失敗: {e}",
            "tcpSender"
        )
        _disconnect_client(_client_name)


def send_front_frame(_frame):
    _send_frame("front_video", _frame)


def send_side_frame(_frame):
    _send_frame("side_video", _frame)


def close_all():
    global _selected_host

    _disconnect_client("log")
    _disconnect_client("research")
    _disconnect_client("front_video")
    _disconnect_client("side_video")

    _selected_host = None

    p.info("TCP接続を終了しました", "tcpSender")