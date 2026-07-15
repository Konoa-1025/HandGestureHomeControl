# conboManager.py
# Norifumi Konndo

import csv
import time
from pathlib import Path

import pygame
import managers.appliancesManager as home
import utils.logPrint as p


_initialized = False
_sounds = {}
_combos = []

_last_beep_at = 0.0
_beep_interval = 1.0

_combo_started = False
_gesture_history = []
_gesture_released = False

_combo_lost_since = None
_cancel_timeout = 0.7


def Initialization(_settings):
    global _initialized
    global _sounds
    global _combos

    global _last_beep_at
    global _beep_interval

    global _combo_started
    global _gesture_history
    global _gesture_released

    global _combo_lost_since
    global _cancel_timeout

    p.info("初期化中")

    _combo_settings = _settings.get("combo", _settings)

    _sound_paths = {
        "cancel": Path(_combo_settings["cancel_sound_path"]),
        "go": Path(_combo_settings["go_sound_path"]),
        "beep": Path(_combo_settings["beep_sound_path"]),
        "start": Path(_combo_settings["start_sound_path"])
    }

    _combo_path = Path(_combo_settings["combo_csv_path"])

    _beep_interval = float(
        _combo_settings.get("beep_interval", 1.0)
    )

    _cancel_timeout = float(
        _combo_settings.get("cancel_timeout", 0.7)
    )

    for _sound_name, _sound_path in _sound_paths.items():
        if not _sound_path.exists():
            raise FileNotFoundError(
                f"{_sound_name}の効果音ファイルが見つかりません: "
                f"{_sound_path}"
            )

    if not _combo_path.exists():
        raise FileNotFoundError(
            f"コンボCSVが見つかりません: {_combo_path}"
        )

    if not pygame.mixer.get_init():
        pygame.mixer.init()

    _sounds = {
        _sound_name: pygame.mixer.Sound(str(_sound_path))
        for _sound_name, _sound_path in _sound_paths.items()
    }

    _combos = _load_combos(_combo_path)

    _last_beep_at = 0.0
    _combo_started = False
    _gesture_history = []
    _combo_lost_since = None

    _initialized = True

    p.success("初期化成功")

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

    with _combo_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as _file:

        _reader = csv.DictReader(_file)

        if _reader.fieldnames is None:
            return _loaded_combos

        _missing_columns = (
            _required_columns - set(_reader.fieldnames)
        )

        if _missing_columns:
            raise ValueError(
                "コンボCSVに必要な列がありません: "
                + ", ".join(sorted(_missing_columns))
            )

        for _row in _reader:
            _device = (
                _row.get("device") or ""
            ).strip().upper()

            _trigger = (
                _row.get("trigger") or ""
            ).strip().upper()

            _action = (
                _row.get("action") or ""
            ).strip()

            if not _device or not _trigger or not _action:
                continue

            _gesture_sequence = [_trigger]

            for _column_name in (
                "gesture1",
                "gesture2",
                "gesture3",
                "gesture4"
            ):
                _gesture = (
                    _row.get(_column_name) or ""
                ).strip().upper()

                if _gesture:
                    _gesture_sequence.append(_gesture)

            _loaded_combos.append({
                "device": _device,
                "gestures": _gesture_sequence,
                "action": _action
            })

    return _loaded_combos


def _play(_sound_name):
    _sound = _sounds.get(_sound_name)

    if _sound is not None:
        _sound.play()


def _reset_combo():
    global _last_beep_at
    global _combo_started
    global _gesture_history
    global _combo_lost_since
    global _gesture_released

    _last_beep_at = 0.0
    _combo_started = False
    _gesture_history = []
    _combo_lost_since = None
    _gesture_released = False
    home.clear_selected_appliance()


def _handle_lost(_reason):
    global _combo_lost_since
    global _gesture_released

    if not _combo_started:
        return None

    _gesture_released = True
    _now = time.monotonic()

    if _combo_lost_since is None:
        _combo_lost_since = _now
        return None

    if _now - _combo_lost_since < _cancel_timeout:
        return None

    p.error(
        f"コンボキャンセル: "
        f"{' → '.join(_gesture_history)} → {_reason}"
    )

    _play("cancel")
    _reset_combo()

    return None

def _get_device(_recognition_result):
    _selected_appliance = home.get_selected_appliance()

    if _selected_appliance is not None:
        return _selected_appliance

    _device = (
        _recognition_result.get("device")
        or _recognition_result.get("target")
    )

    if _device is None:
        return None

    return str(_device).strip().upper()


def _find_candidates(_device, _gesture_history):
    _candidates = []

    for _combo in _combos:
        if _device is not None:
            if _combo["device"] != _device:
                continue

        _combo_gestures = _combo["gestures"]

        if len(_gesture_history) > len(_combo_gestures):
            continue

        if (
            _combo_gestures[:len(_gesture_history)]
            == _gesture_history
        ):
            _candidates.append(_combo)

    return _candidates


def run(_recognition_result):
    global _last_beep_at
    global _combo_started
    global _gesture_history
    global _combo_lost_since
    global _gesture_released

    if not _initialized:
        raise RuntimeError(
            "conboManagerが初期化されていません"
        )

    if _recognition_result is None:
        return _handle_lost("未検出")
    
    if _recognition_result.get("is_cached", False):
        _gesture_released = True
        return None

    _gesture = _recognition_result.get("gesture")

    if _gesture is None:
        return _handle_lost("UNKNOWN")

    _combo_lost_since = None

    _gesture = str(_gesture).strip().upper()
    _device = _get_device(_recognition_result)

    # コンボ開始前はPOINT以外を無視
    if not _combo_started:
        if _gesture != "POINT":
            return None

        if _device is None:
            return None

        _combo_started = True
        _gesture_history = ["POINT"]
        _last_beep_at = time.monotonic()

        p.success("POINT")
        _play("start")

        return None

    # 同じジェスチャーを維持しているだけなら追加しない
    if (
        _gesture_history
        and _gesture_history[-1] == _gesture
        and not _gesture_released
    ):

        _now = time.monotonic()

        if _now - _last_beep_at >= _beep_interval:
            _play("beep")
            _last_beep_at = _now

        return None

    _gesture_history.append(_gesture)
    _gesture_released = False

    p.success(
        " → ".join(_gesture_history)
    )

    _candidates = _find_candidates(
        _device,
        _gesture_history
    )

    # 候補が1つもない
    if not _candidates:
        p.error(
            f"コンボキャンセル: "
            f"{' → '.join(_gesture_history)}"
        )

        _play("cancel")
        _reset_combo()

        return None

    _exact_matches = [
        _combo
        for _combo in _candidates
        if _combo["gestures"] == _gesture_history
    ]

    # 完全一致がある
    if _exact_matches:
        _matched_combo = _exact_matches[0]

        _play("go")

        _result = {
            **_recognition_result,
            "device": _matched_combo["device"],
            "gestures": _gesture_history.copy(),
            "combo": " → ".join(_gesture_history),
            "action": _matched_combo["action"]
        }

        _reset_combo()

        return _result

    # 部分一致なので次の入力を待つ
    p.info(
        f"コンボ待機: "
        f"{' → '.join(_gesture_history)}"
    )

    return None