#managers/modelManager.py
#Norifumi Konndo
import models.standbyModel as standby
import models.lowModel as low
import models.highModel as high
import utils.logPrint as p

_current = "standby"

_cpu_low = 70
_cpu_high = 90

def Initialization(_low, _high):
    global _current
    global _cpu_low
    global _cpu_high

    _current = "low"
    _cpu_low = _low
    _cpu_high = _high

def update(_system):
    global _current

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

def run(_frames):
    if _current == "standby":
        return standby.run(_frames)

    elif _current == "low":
        return low.run(_frames)

    elif _current == "high":
        return high.run(_frames)
    
    else:
        p.error(f"モデルの指定外です。{_current}")
        return None