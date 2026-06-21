# tcpSender.py
# Norifumi Kondo

import socket
import json
import threading
import time
from pathlib import Path
import logPrint as p


_CONFIG_PATH = Path(__file__).parent / "config.json"

with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    _config = json.load(f)

_TCP_HOST = _config["tcp_host"]
_LOG_PORT = _config["log_port"]
_RESEARCH_LOG_PORT = _config["research_log_port"]

_log_client = None
_research_log_client = None

_restart_counter_log = 0
_restart_counter_research = 0


def _connect(port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(3)
    client.connect((_TCP_HOST, port))
    client.settimeout(None)
    return client


def _log_worker():
    global _log_client
    global _restart_counter_log

    while True:
        if _log_client is None:
            try:
                _log_client = _connect(_LOG_PORT)
                p.success(
                    f"{_TCP_HOST}:{_LOG_PORT} 接続成功",
                    "tcpSender"
                )
            except Exception as e:
                _restart_counter_log += 1
                if _restart_counter_log >= 5:
                    p.error(
                        f"{_TCP_HOST}:{_LOG_PORT}に接続失敗 ({e})",
                        "tcpSender"
                    )
                    break
                else:
                    p.warning(
                        f"{_TCP_HOST}:{_LOG_PORT}接続失敗({e})5秒後に再試行({_restart_counter_log}回)",
                        "tcpSender"
                    )
                    time.sleep(5)


def _research_worker():
    global _research_log_client
    global _restart_counter_research

    while True:
        if _research_log_client is None:
            try:
                _research_log_client = _connect(_RESEARCH_LOG_PORT)
                p.success(
                    f"{_TCP_HOST}:{_RESEARCH_LOG_PORT} 接続成功",
                    "tcpSender"
                )

            except Exception as e:
                _restart_counter_research += 1
                if _restart_counter_research >= 5:
                    p.error(
                        f"{_TCP_HOST}:{_RESEARCH_LOG_PORT}に接続失敗 ({e}) ",
                        "tcpSender"
                    )
                    break
                else:
                    p.warning(
                        f"{_TCP_HOST}:{_RESEARCH_LOG_PORT}接続失敗({e})5秒後に再試行({_restart_counter_research}回)",
                        "tcpSender"
                    )
                    time.sleep(5)


def connect_all():
    threading.Thread(
        target=_log_worker,
        daemon=True
    ).start()

    threading.Thread(
        target=_research_worker,
        daemon=True
    ).start()


def send_log(text):
    global _log_client

    if _log_client is None:
        return

    try:
        _log_client.send(
            (text + "\n").encode("utf-8")
        )

    except Exception as e:
        p.error(
            f"6000送信失敗 : {e}",
            "tcpSender"
        )

        if _log_client:
            _log_client.close()

        _log_client = None


def send_research_log(text):
    global _research_log_client

    if _research_log_client is None:
        return

    try:
        _research_log_client.send(
            (text + "\n").encode("utf-8")
        )

    except Exception as e:
        p.error(
            f"6001送信失敗 : {e}",
            "tcpSender"
        )

        if _research_log_client:
            _research_log_client.close()

        _research_log_client = None


def close_all():
    global _log_client
    global _research_log_client

    if _log_client:
        _log_client.close()
        _log_client = None

    if _research_log_client:
        _research_log_client.close()
        _research_log_client = None