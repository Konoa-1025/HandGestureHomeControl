#managers/systemMonitor.py
#Norifumi Konndo

import psutil

def get_status():
    _cpu = psutil.cpu_percent(interval=None)
    _mem = psutil.virtual_memory().percent

    return _cpu, _mem