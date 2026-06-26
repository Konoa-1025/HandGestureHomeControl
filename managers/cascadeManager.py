#managers/cascadeManager.py
#Norifumi Konndo

_current_cascade = "low"

def update(_cpu, _mem):
    global _current_cascade

    if _mem >= 90:
        _current_cascade = "low"
    else:
        _current_cascade = "hige"