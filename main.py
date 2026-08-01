
#? main.py
#? Norifumi Konndo
#! Python 3.11以上指定
#? 役割：親,司令塔

import art
art.tprint("HandGestureHC")

import Utils.logger as p
import Utils.configLoader as figload
import Core.initializer as initializer

import Managers.cameraManager as camera

def main():
    setting_config = figload.load_setting_config() #?設定の読み込み
    initializer.Managers_initialize(setting_config) #?初期化

    #?カメラの起動
    if not camera.start_camera():
            p.error("カメラを1台も開くことができませんでした")
            return False

    try:
        while True:
            #!メインカメラの処理
            front_frame = camera.read_frame("front")
            if front_frame is None:
                p.warning("フロントカメラの映像を取得できませんでした")
                continue
            
            else:
                # 認識処理
                pass

            #!サブカメラの処理
            side_frame = camera.read_frame("side")
    finally:
        p.debug("終わり")

if __name__ == "__main__":
    main()