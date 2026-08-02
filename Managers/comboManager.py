# Managers/comboManager.py
# Norifumi Kondo

import csv
import time
from pathlib import Path

import Utils.logger as p


_initialized = False

_combos = []

_combo_started = False
_gesture_history = []
_active_device = None

_hold_gesture = None
_hold_device = None
_hold_started_at = None
_hold_seconds = 1.0

_combo_lost_since = None
_cancel_timeout = 0.7


def Initialization(_settings):
    global _initialized
    global _combos
    global _combo_started
    global _gesture_history
    global _active_device
    global _hold_gesture
    global _hold_device
    global _hold_started_at
    global _hold_seconds
    global _combo_lost_since
    global _cancel_timeout

    p.info("初期化中")

    _combo_settings = _settings.get("combo", _settings)

    _combo_path = Path(_combo_settings["combo_csv_path"])

    _hold_seconds = float(_combo_settings.get("hold_seconds", 1.0))
    _cancel_timeout = float(_combo_settings.get("cancel_timeout", 0.7))

    if _hold_seconds <= 0:
        raise ValueError("hold_secondsは0より大きい値にしてください")

    if _cancel_timeout <= 0:
        raise ValueError("cancel_timeoutは0より大きい値にしてください")

    if not _combo_path.exists():
        raise FileNotFoundError(f"コンボCSVが見つかりません: {_combo_path}")

    _combos = _load_combos(_combo_path)

    _combo_started = False
    _gesture_history = []
    _active_device = None

    _hold_gesture = None
    _hold_device = None
    _hold_started_at = None

    _combo_lost_since = None
    _initialized = True

    p.success(f"初期化成功: {len(_combos)}件")

    return True


def _load_combos(_combo_path):
    _loaded_combos = []

    _required_columns = {
        "device",
        "trigger",
        "gesture1",
        "gesture2",
        "gesture3",
        "gesture4",
        "action"
    }

    with _combo_path.open("r", encoding="utf-8-sig", newline="") as _file:
        _reader = csv.DictReader(_file)

        if _reader.fieldnames is None:
            return _loaded_combos

        _missing_columns = _required_columns - set(_reader.fieldnames)

        if _missing_columns:
            raise ValueError("コンボCSVに必要な列がありません: " + ", ".join(sorted(_missing_columns)))

        for _row in _reader:
            _device = (_row.get("device") or "").strip().upper()
            _trigger = (_row.get("trigger") or "").strip().upper()
            _action = (_row.get("action") or "").strip()

            if not _device or not _trigger or not _action:
                continue

            _gesture_sequence = [_trigger]

            for _column_name in ("gesture1", "gesture2", "gesture3", "gesture4"):
                _gesture = (_row.get(_column_name) or "").strip().upper()

                if _gesture:
                    _gesture_sequence.append(_gesture)

            _loaded_combos.append({
                "device": _device,
                "gestures": _gesture_sequence,
                "action": _action
            })

    return _loaded_combos


def _reset_hold():
    global _hold_gesture
    global _hold_device
    global _hold_started_at

    _hold_gesture = None
    _hold_device = None
    _hold_started_at = None


def _reset_combo():
    global _combo_started
    global _gesture_history
    global _active_device
    global _combo_lost_since

    _combo_started = False
    _gesture_history = []
    _active_device = None
    _combo_lost_since = None

    _reset_hold()


def _handle_lost(_reason):
    global _combo_lost_since

    _reset_hold()

    if not _combo_started:
        return None

    _now = time.monotonic()

    if _combo_lost_since is None:
        _combo_lost_since = _now
        return None

    if _now - _combo_lost_since < _cancel_timeout:
        return None

    p.error(f"コンボキャンセル: {' → '.join(_gesture_history)} → {_reason}")

    #! ここでコンボキャンセル音を出す『キャンセル音』

    _reset_combo()

    return None


def _get_device(_recognition_result):
    _device = _recognition_result.get("device")

    if _device is None:
        return None

    _device = str(_device).strip().upper()

    if not _device:
        return None

    return _device


def _find_candidates(_device, _gesture_history):
    _candidates = []

    for _combo in _combos:
        if _combo["device"] != _device:
            continue

        _combo_gestures = _combo["gestures"]

        if len(_gesture_history) > len(_combo_gestures):
            continue

        if _combo_gestures[:len(_gesture_history)] == _gesture_history:
            _candidates.append(_combo)

    return _candidates


def _get_expected_gestures():
    if not _combo_started:
        return {"POINT"}

    _candidates = _find_candidates(_active_device, _gesture_history)
    _step_index = len(_gesture_history)
    _expected_gestures = set()

    for _combo in _candidates:
        if _step_index >= len(_combo["gestures"]):
            continue

        _expected_gestures.add(_combo["gestures"][_step_index])

    return _expected_gestures


def _is_gesture_held(_gesture, _device):
    global _hold_gesture
    global _hold_device
    global _hold_started_at

    _now = time.monotonic()

    if _hold_gesture != _gesture or _hold_device != _device:
        _hold_gesture = _gesture
        _hold_device = _device
        _hold_started_at = _now

        return False

    if _hold_started_at is None:
        _hold_started_at = _now

        return False

    _elapsed_seconds = _now - _hold_started_at

    if _elapsed_seconds < _hold_seconds:
        return False

    _hold_started_at = _now

    return True


def _cancel_combo(_gesture):
    p.error(f"コンボキャンセル: {' → '.join(_gesture_history)} → {_gesture}")

    #! ここでコンボキャンセル音を出す『キャンセル音』

    _reset_combo()

    return None


def _complete_combo(_matched_combo):
    _device = _matched_combo["device"]
    _action = _matched_combo["action"]

    p.success(f"コンボ成立: {' → '.join(_gesture_history)}")
    p.success(f"実行要求: {_device} / {_action}")

    #! ここでコンボ成立音を出す『決定音』

    _reset_combo()

    return _device, _action


def run(_recognition_result):
    global _combo_started
    global _gesture_history
    global _active_device
    global _combo_lost_since

    if not _initialized:
        raise RuntimeError("comboManagerが初期化されていません")

    if _recognition_result is None:
        return _handle_lost("未検出")

    if _recognition_result.get("is_cached", False):
        return _handle_lost("キャッシュ")

    _gesture = _recognition_result.get("gesture")

    if _gesture is None:
        return _handle_lost("UNKNOWN")

    _gesture = str(_gesture).strip().upper()

    if not _gesture or _gesture == "UNKNOWN":
        return _handle_lost("UNKNOWN")

    _combo_lost_since = None

    _device = _get_device(_recognition_result)

    if not _combo_started:
        if _gesture != "POINT":
            _reset_hold()

            return None

        if _device is None:
            _reset_hold()

            return None

        if not _is_gesture_held(_gesture, _device):
            return None

        _combo_started = True
        _active_device = _device
        _gesture_history = ["POINT"]

        p.success(f"{_active_device}: POINT")

        #! ここでコンボ開始音を出す『開始音』

        _exact_matches = [_combo for _combo in _find_candidates(_active_device, _gesture_history) if _combo["gestures"] == _gesture_history]

        if _exact_matches:
            return _complete_combo(_exact_matches[0])

        return None

    _expected_gestures = _get_expected_gestures()

    if not _expected_gestures:
        return _cancel_combo("候補なし")

    if _gesture not in _expected_gestures:
        if not _is_gesture_held(_gesture, _active_device):
            return None

        return _cancel_combo(_gesture)

    if not _is_gesture_held(_gesture, _active_device):
        return None

    _gesture_history.append(_gesture)

    p.success(" → ".join(_gesture_history))

    #! ここでコンボ入力音を出す『短いビープ音』

    _candidates = _find_candidates(_active_device, _gesture_history)

    if not _candidates:
        return _cancel_combo(_gesture)

    _exact_matches = [_combo for _combo in _candidates if _combo["gestures"] == _gesture_history]

    if _exact_matches:
        return _complete_combo(_exact_matches[0])

    p.info(f"コンボ待機: {' → '.join(_gesture_history)}")

    return None


def reset():
    if not _initialized:
        return False

    _reset_combo()

    return True


def get_combo_state():
    _expected_gestures = list(_get_expected_gestures()) if _combo_started else ["POINT"]

    return {
        "active": _combo_started,
        "device": _active_device,
        "history": _gesture_history.copy(),
        "expected_gestures": _expected_gestures,
        "hold_gesture": _hold_gesture,
        "hold_seconds": _hold_seconds
    }


def close():
    global _initialized
    global _combos

    _reset_combo()

    _combos = []
    _initialized = False

    p.info("comboManagerを終了しました")

    return True