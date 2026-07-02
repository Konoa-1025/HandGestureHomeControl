#managers/modelManager.py
#Norifumi Kondo
import models.standbyModel as standby
import models.lowModel as low
import models.highModel as high
import utils.logPrint as p
import time

_current = "standby"
_prev = None
_cpu = 0

_cpu_low = 70
_cpu_high = 90

_NO_PERSON_TIMEOUT = 5.0
_no_person_since = None

def Initialization(_low, _high):
    global _current, _prev, _cpu_low, _cpu_high, _cpu, _no_person_since
    _current = "standby"
    _prev = None
    _cpu_low = _low
    _cpu_high = _high
    _cpu = 0
    _no_person_since = None

def _log_if_changed():
    global _prev
    if _current != _prev:
        p.info(f"モデル：{_prev} → {_current}")
        _prev = _current

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
        return _is_person

    elif _model in ("low", "high"):
        _is_person = (low if _model == "low" else high).run(_frames)
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
        return _is_person

    return False