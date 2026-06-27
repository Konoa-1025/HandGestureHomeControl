#managers/cascadeManager.py
#Norifumi Konndo
import utils.logPrint as p

def Initialization(_low,_high):
    global _current
    global _memory_high
    global _memory_low

    _current = "low"
    _memory_low = _low
    _memory_high = _high

def update(_system):

    global _current
    _memory = _system["memory"]
    _cpu = _system["cpu"]

    if _cpu >= 90:
        if _current != "low":
            _current = "low"
            p.info("CPU高負荷：カスケード low")
        return _current

    if _current == "high":
        if _memory >= _memory_high:
            _current = "low"
            p.info("カスケード：low")

    elif _current == "low":
        if _memory <= _memory_low:
            _current = "high"
            p.info(f"カスケード：high {_memory}")

    return _current