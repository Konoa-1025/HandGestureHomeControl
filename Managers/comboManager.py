# Managers/comboManager.py
# Norifumi Kondo

import csv
import time
from pathlib import Path

import Utils.logger as p


def Initialization(_settings):
    p.info("初期化中")

    p.success(f"初期化成功:件")

    return True

combo_active = False
selected_appliance = None

def is_combo():
    return combo_active

def start_combo(appliance):
    global combo_active
    global selected_appliance

    selected_appliance = appliance
    combo_active = True

def reset_combo():
    global combo_active
    global selected_appliance

    combo_active = False
    selected_appliance = None