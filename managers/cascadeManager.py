#managers/cascadeManager.py
#Norifumi Konndo
import utils.logPrint as p
import cascades.highCascade as highCas
import cascades.lowCascade as lowCas

def Initialization(_settings):
    global _current
    global _memory_high
    global _memory_low

    _current = "low"
    _memory_low = _settings["memory"]["low"]
    _memory_high = _settings["memory"]["high"]

    _low_flg = lowCas.Initialization(_settings["low"])
    _high_flg = highCas.Initialization(_settings["high"])

    _intflg = _low_flg and _high_flg

    if _intflg:
        p.success("初期化終了")
    else:
        p.error("初期化失敗")
    return _intflg

def update(_system):
    global _current

    _memory = _system["memory"]
    _cpu = _system["cpu"]

    if _cpu >= 90:
        if _current != "low":
            _current = "low"
            p.warning("CPU高負荷：カスケード low")
            lowCas._startCas()
        return _current

    if _current == "high":
        if _memory >= _memory_high:
            _current = "low"
            p.change(f"カスケード：low {_memory}")
            lowCas._startCas()

    elif _current == "low":
        if _memory <= _memory_low:
            _current = "high"
            p.change(f"カスケード：high {_memory}")
            highCas._startCas()

    return _current
def run(_frames):
    for i in range(len(_frames)):
        if _frames[i] is None:
            continue

        if _current == "low":
            _frames[i] = lowCas._casRun(_frames[i])
        else:
            _frames[i] = highCas._casRun(_frames[i])

    return _frames