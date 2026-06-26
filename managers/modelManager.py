#managers/modelManager.py
#Norifumi Konndo

_current = "standby"


def update(_system):

    global _current

    if _system["cpu"] >= 90:
        _current = "low"
    else:
        _current = "high"