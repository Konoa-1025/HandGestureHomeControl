#managers/modelManager.py
#Norifumi Konndo

_current = "standby"

def Initialization(_low,_high):
    global _current 
    global _memory_high
    global _memory_low

    _current = "low"
    _memory_low = _low
    _memory_high = _high

def update(_system):

    global _current

    if _system["cpu"] >= 90:
        _current = "low"
    else:
        _current = "high"