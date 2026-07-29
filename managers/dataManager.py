# managers/dataManager.py
# Norifumi Kondo
# Python 3.8対応

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, TextIO

import senders.tcpSender as tcp
import utils.logPrint as p


_lock = threading.Lock()

_initialized = False
_measuring = False

_log_directory = Path("research_logs")
_measurement_duration = 10.0
_live_send_interval = 0.5

_measurement_start_time = 0.0
_last_live_send_time = 0.0
_frame_id = 0

_experiment: Dict[str, Any] = {}
_log_file: Optional[TextIO] = None
_log_path: Optional[Path] = None


def Initialization(_settings):
    """dataManagerを初期化する。"""
    global _initialized
    global _log_directory
    global _measurement_duration
    global _live_send_interval

    p.info("初期化中", "dataManager")

    try:
        _data_settings = _settings.get("data", {})

        _log_directory = Path(
            _data_settings.get("log_directory", "research_logs")
        )
        _measurement_duration = float(
            _data_settings.get("measurement_duration", 10.0)
        )
        _live_send_interval = float(
            _data_settings.get("live_send_interval", 0.5)
        )

        if _measurement_duration <= 0:
            raise ValueError(
                "measurement_durationは0より大きい値にしてください"
            )

        if _live_send_interval <= 0:
            raise ValueError(
                "live_send_intervalは0より大きい値にしてください"
            )

        _log_directory.mkdir(parents=True, exist_ok=True)

        _initialized = True
        p.success("初期化成功", "dataManager")
        return True

    except Exception as _error:
        _initialized = False
        p.error(
            "初期化失敗: {}".format(_error),
            "dataManager"
        )
        return False


def _check_initialized():
    if not _initialized:
        raise RuntimeError("dataManagerが初期化されていません")


def _now_iso():
    return datetime.now().astimezone().isoformat(
        timespec="milliseconds"
    )


def _safe_name(_value):
    if _value is None:
        return "NONE"

    _text = str(_value)
    _text = _text.replace("/", "_")
    _text = _text.replace("\\", "_")
    _text = _text.replace(" ", "_")
    _text = _text.replace(":", "_")
    return _text


def _get_nested(_data, _section, _key, _default=None):
    _section_data = _data.get(_section, {})

    if not isinstance(_section_data, dict):
        return _default

    return _section_data.get(_key, _default)


def is_measuring():
    return _measuring


def get_log_path():
    if _log_path is None:
        return None

    return str(_log_path)


def start_measurement(_experiment_data):
    """
    計測を開始する。

    _experiment例:
    {
        "experiment_id": "gesture_001",
        "trial_id": 1,
        "expected_gesture": "FIST",
        "brightness_percent": 50,
        "distance_m": 2.0,
        "angle_degrees": 0,
        "background": "WHITE"
    }
    """
    global _measuring
    global _measurement_start_time
    global _last_live_send_time
    global _frame_id
    global _experiment
    global _log_file
    global _log_path

    _check_initialized()

    if not isinstance(_experiment_data, dict):
        p.error("実験条件は辞書で指定してください", "dataManager")
        return False

    with _lock:
        if _measuring:
            _close_log_file()

        _experiment = {
            "experiment_id": _experiment_data.get("experiment_id"),
            "trial_id": _experiment_data.get("trial_id"),
            "expected_gesture": _experiment_data.get("expected_gesture"),
            "brightness_percent": _experiment_data.get("brightness_percent"),
            "distance_m": _experiment_data.get("distance_m"),
            "angle_degrees": _experiment_data.get("angle_degrees"),
            "background": _experiment_data.get("background")
        }

        _measurement_start_time = time.monotonic()
        _last_live_send_time = 0.0
        _frame_id = 0

        _timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _gesture = _safe_name(_experiment["expected_gesture"])
        _trial = _safe_name(_experiment["trial_id"])

        _file_name = "{}_{}_trial{}.jsonl".format(
            _timestamp,
            _gesture,
            _trial
        )

        _log_path = _log_directory / _file_name
        _log_file = _log_path.open(mode="w", encoding="utf-8")
        _measuring = True

    p.success("計測開始: {}".format(_log_path), "dataManager")
    return True


def record_frame(_frame_data):
    """
    毎フレームmainから呼び出す。

    _frame_data例:
    {
        "system": {
            "cpu_percent": 30.0,
            "gpu_percent": 20.0,
            "memory_percent": 60.0
        },
        "performance": {
            "fps": 28.5,
            "video_latency_ms": 40.0
        },
        "model": {
            "current": "high"
        },
        "recognition": {
            "hand_detected": True,
            "raw_gesture": "FIST",
            "stable_gesture": "FIST"
        }
    }
    """
    global _frame_id

    _check_initialized()

    if not _measuring:
        return False

    if not isinstance(_frame_data, dict):
        return False

    _current_time = time.monotonic()
    _elapsed_ms = (
        _current_time - _measurement_start_time
    ) * 1000.0

    with _lock:
        _frame_id += 1

        _record = {
            "timestamp": _now_iso(),
            "elapsed_ms": round(_elapsed_ms, 3),
            "frame_id": _frame_id,

            "experiment": dict(_experiment),

            "system": {
                "cpu_percent": _get_nested(
                    _frame_data, "system", "cpu_percent"
                ),
                "gpu_percent": _get_nested(
                    _frame_data, "system", "gpu_percent"
                ),
                "memory_percent": _get_nested(
                    _frame_data, "system", "memory_percent"
                )
            },

            "performance": {
                "fps": _get_nested(
                    _frame_data, "performance", "fps"
                ),
                "video_latency_ms": _get_nested(
                    _frame_data,
                    "performance",
                    "video_latency_ms"
                )
            },

            "model": {
                "current": _get_nested(
                    _frame_data, "model", "current"
                )
            },

            "recognition": {
                "hand_detected": _get_nested(
                    _frame_data,
                    "recognition",
                    "hand_detected",
                    False
                ),
                "raw_gesture": _get_nested(
                    _frame_data,
                    "recognition",
                    "raw_gesture"
                ),
                "stable_gesture": _get_nested(
                    _frame_data,
                    "recognition",
                    "stable_gesture"
                )
            }
        }

        if _log_file is None:
            return False

        _json_text = json.dumps(
            _record,
            ensure_ascii=False,
            separators=(",", ":")
        )

        _log_file.write(_json_text + "\n")
        _log_file.flush()

    _send_live_if_due(_record)

    #if (
    #    _current_time - _measurement_start_time
    #    >= _measurement_duration
    #):
    #    #top_measurement()
    #    p.debug("デバックで自動計測終了をストップしています。")

    return True


def _send_live_if_due(_record):
    """リアルタイム表示用に一定間隔でTCP送信する。"""
    global _last_live_send_time

    _current_time = time.monotonic()

    if (
        _current_time - _last_live_send_time
        < _live_send_interval
    ):
        return False

    _last_live_send_time = _current_time

    try:
        _message = {
            "type": "research_live",
            "data": _record
        }

        _json_text = json.dumps(
            _message,
            ensure_ascii=False,
            separators=(",", ":")
        )

        tcp.send_research_log(_json_text)
        return True

    except Exception as _error:
        p.error(
            "リアルタイムデータ送信失敗: {}".format(_error),
            "dataManager"
        )
        return False


def stop_measurement():
    """計測を終了し、ログファイルを閉じる。"""
    global _measuring

    _check_initialized()

    with _lock:
        if not _measuring:
            return None

        _measuring = False
        _close_log_file()
        _finished_path = _log_path

    p.success("計測終了: {}".format(_finished_path), "dataManager")

    if _finished_path is None:
        return None

    return str(_finished_path)


def _close_log_file():
    global _log_file

    if _log_file is not None:
        try:
            _log_file.flush()
            _log_file.close()
        except Exception:
            pass

    _log_file = None


def close():
    """アプリケーション終了時に呼び出す。"""
    global _measuring

    with _lock:
        _measuring = False
        _close_log_file()

    p.info("dataManagerを終了しました", "dataManager")
