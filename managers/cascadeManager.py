#managers/cascadeManager.py
#Norifumi Konndo

_current = "low"


def update(_system):

    global _current

    if _system["memory"] >= 90:
        _current = "low"
    else:
        _current = "high"