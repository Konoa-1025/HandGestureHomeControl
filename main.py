
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
import Managers.systemManager as system
import Managers.cascadeManager as cascade
import Managers.modelManager as model
import Managers.recognitionManager as recognize



def main():
    last_is_hand = False
    setting_config = figload.load_setting_config() #?設定の読み込み
    initializer.Managers_initialize(setting_config) #?初期化

    #?カメラの起動
    if not camera.start_camera():
            p.error("カメラを1台も開くことができませんでした")
            return False

    try:
        while True:
            front_frame = camera.read_frame("front")

            #!メインカメラ
            if front_frame is None: #?フレーム取得失敗
                p.warning("フロントカメラの映像を取得できませんでした")
                continue

            cascade_result = cascade.cascade_process(front_frame,system.get_mem()) #?返り値：軽量化フレーム
            if cascade_result is None:
                continue
            
            is_motion = cascade_result["is_motion"]
            cased_frame = cascade_result["cased_frame"]
            if not is_motion and not last_is_hand: #!人がいないかつ手が映っていないならモデルに投げない
                continue

            hand_landmarks = model.model_process(cased_frame,system.get_cpu(),system.get_gpu()) #?返り値：手の認識,ランドマーク位置
            last_is_hand = hand_landmarks["is_hand"]
            if not last_is_hand: #!手が映ってないならリコライズしない
                continue
            gesture = recognize.gesture_process(hand_landmarks)
            p.debug(gesture)
            #gesture = recognize.get_gesture #?返り値：確定ジェスチャ
            #!指差しだったらpointingEstimator.pyで方向をgetする。
                




            side_frame = camera.read_frame("side")
            if side_frame is None:
                continue

    finally:
        p.debug("終わり")

if __name__ == "__main__":
    main()