#managers/modelManager.py
#Norifumi Kondo
import models.standbyModel as standby
import models.lowModel as low
import models.highModel as high
import utils.logPrint as p
import time

_current = "standby"
_prev = None
_cpu_low = 70
_cpu_high = 90

_NO_PERSON_TIMEOUT = 5.0
_no_person_since = None

def Initialization(_settings):
    global _current, _prev, _cpu_low, _cpu_high, _cpu
    global _NO_PERSON_TIMEOUT, _no_person_since
    _current = "standby"
    _prev = None
    _cpu_low = _settings["cpu"]["low"]
    _cpu_high = _settings["cpu"]["high"]
    _mem_low = _settings["memory"]["low"]
    _mem_high = _settings["memory"]["high"]
    _NO_PERSON_TIMEOUT = _settings["standby"]["person_timeout"]
    _no_person_since = None
    _standby_flg = standby.Initialization(_settings["standby"])
    _low_flg = low.Initialization(_settings["low"])
    _high_flg = high.Initialization(_settings["high"])
    return _standby_flg and _low_flg and _high_flg

def _log_if_changed():
    global _prev
    if _current != _prev:
        p.change(f"モデル：{_prev} → {_current}")
        _prev = _current

def _empty_result():
    return {
        "is_person": False,
        "hands": []
    }


def _normalize_result(_result):
    if isinstance(_result, dict):
        return {
            "is_person": bool(_result.get("is_person", False)),
            "hands": _result.get("hands", [])
        }

    return {
        "is_person": bool(_result),
        "hands": []
    }

def update(_system):
    global _current, _cpu

    _cpu = _system["cpu"]

    if _current == "high":
        if _cpu >= _cpu_high:
            _current = "low"

    elif _current == "low":
        if _cpu <= _cpu_low:
            _current = "high"

    return _current

def run(_frames, _system):
    global _current, _no_person_since
    _model = update(_system)

    if _model == "standby":
        _no_person_since = None
        _is_person = standby.run(_frames)

        if _is_person:
            _current = "high"

        _log_if_changed()
        return {
            "is_person": bool(_is_person),
            "hands": []
        }

    elif _model in ("low", "high"):
        _result = (low if _model == "low" else high).run(_frames)
        _result = _normalize_result(_result)
        _is_person = _result["is_person"]
        _has_motion = standby.run(_frames)

        if _is_person or _has_motion:
            _no_person_since = None
        else:
            if _no_person_since is None:
                _no_person_since = time.time()
            elif time.time() - _no_person_since >= _NO_PERSON_TIMEOUT:
                _current = "standby"
                _no_person_since = None

        _log_if_changed()
        return _result

    _log_if_changed()
    return _empty_result()