#managers/systemMonitor.py
#Norifumi Konndo

import psutil

def get_status():
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "memory": psutil.virtual_memory().percent
    }