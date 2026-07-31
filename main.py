
#? main.py
#? Norifumi Konndo
#! Python 3.11以上指定
#? 役割：親,司令塔

import art
art.tprint("HandGestureHC")

import Utils.logger as p
import Utils.configLoader as figload
import Core.initializer as initializer

def main():
    setting_config = figload.load_setting_config() #?設定の読み込み
    initializer.Managers_initialize() #?初期化

    try:
        while True:
            pass
    finally:
        p.debug("終わり")

if __name__ == "__main__":
    main()