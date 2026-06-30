#managers/modelManager.py
#Norifumi Konndo
import models.standbyModel as standby
import models.lowModel as low
import models.highModel as high
import utils.logPrint as p

_current = "standby"
_cpu = 0

_cpu_low = 70
_cpu_high = 90

def Initialization(_low, _high):
    global _current
    global _cpu_low
    global _cpu_high
    global _cpu

    _current = "standby"
    _cpu_low = _low
    _cpu_high = _high
    _cpu = 0

def update(_system):
    global _current
    global _cpu

    _cpu = _system["cpu"]

    if _current == "high":
        if _cpu >= _cpu_high:
            _current = "low"
            p.info(f"モデル：low CPU={_cpu}")

    elif _current == "low":
        if _cpu <= _cpu_low:
            _current = "high"
            p.info(f"モデル：high CPU={_cpu}")

    return _current

def run(_frames,_system):
    global _current
    _model = update(_system)
    if _model == "standby":
        _is_person = standby.run(_frames)
        if _is_person:
            _current = "high"
        return _is_person
    elif _model == "low":
        _is_person = low.run(_frames)
        if not _is_person:
            _current = "standby"
        return _is_person
    elif _model == "high":
        _is_person = high.run(_frames)
        if not _is_person:
            _current = "standby"
        return _is_person

    return False