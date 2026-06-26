#managers/modelManager.py
#Norifumi Konndo

_current_model = "standby"

def update(_cpu, _mem):
    global _current_model

    if _cpu >= 90:
        _current_model = "low"
    else:
        _current_model = "high"

    return _current_model