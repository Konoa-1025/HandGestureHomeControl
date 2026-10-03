
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
import Managers.appliancesManager as appliances
import Managers.comboManager as combo
import Managers.actionManager as action
import Managers.previewManager as preview
import Managers.feedbackManager as feedback
import Managers.positionManager as human_position
import Managers.pointingManager as pointing



def main():
    wait_point_release = False
    last_is_hand = False
    setting_config = figload.load_setting_config() #?設定の読み込み
    if not initializer.Managers_initialize(setting_config):
        human_position.close()
        preview.close_window()
        return False

    #?カメラの起動
    if not camera.start_camera():
            p.error("カメラを1台も開くことができませんでした")
            return False

    try:
        while True:
            front_frame = camera.read_frame("front")

            #!メインカメラ
            if front_frame is None: #?フレーム取得失敗
                if camera.is_finished("front"):
                    break
                p.warning("フロントカメラの映像を取得できませんでした")
                continue

            cascade_result = cascade.cascade_process(front_frame,system.get_mem()) #?返り値：軽量化フレーム
            if cascade_result is None:
                continue

            is_motion = cascade_result["is_motion"]
            cased_frame = cascade_result["cased_frame"]

            current_position = None
            pointing_event = None
            if pointing.enabled:
                hand_landmarks = model.model_process(cased_frame, system.get_cpu(), 0)
                pointing_event = pointing.update(hand_landmarks, cased_frame.shape, camera.get_timestamp("front"), not combo.is_combo())
                if not preview.show_frame_pointing(cased_frame, pointing):
                    break
            else:
                current_position = human_position.update(cased_frame)
                if not preview.show_frame_detail(cased_frame, human_position.get_debug_state(), current_position):
                    break
                if not is_motion and not last_is_hand:
                    continue
                hand_landmarks = model.model_process(cased_frame, system.get_cpu(), 0)

            last_is_hand = hand_landmarks["is_hand"]
            if not last_is_hand: #!
                if not pointing.enabled:
                    wait_point_release = False
                if combo.is_combo():
                    combo_result = combo.combo_process({"confirmed_gesture": None,"confirmed_direction": None})
                continue
            #?家電選択とコンボ
            
            gesture = recognize.gesture_process(hand_landmarks, current_position)#?返り値：確定ジェスチャ,方向

            if wait_point_release:
                if pointing.enabled:
                    if pointing.result["gesture"] in ("POINT", "NO HAND", "UNKNOWN"):
                        continue
                elif gesture["confirmed_gesture"] == "POINT":
                    continue
                wait_point_release = False
            
            #?コンボ中ではない場合は家電を選択
            if not combo.is_combo():
                if pointing.enabled:
                    if pointing_event["action"]:
                        if action.action_process(pointing_event["action"]):
                            p.success("照明全部をOFFにしました")
                        else:
                            p.warning("全灯OFFに失敗しました")
                        wait_point_release = True
                    elif pointing_event["appliance"] is not None:
                        selected_appliance = pointing_event["appliance"]
                        combo.start_combo(selected_appliance)
                        wait_point_release = True
                        p.success(f"家電を選択しました: {selected_appliance['display_name']}")
                    continue
                if (
                    gesture["confirmed_gesture"] == "POINT"
                    and gesture["confirmed_direction"] is not None
                ):
                    selected_appliance = appliances.select_appliance_abstract(gesture["confirmed_direction"], current_position) #?家電の選択
                    if selected_appliance is None:
                        p.warning("指差し方向に家電がありません")
                        continue

                    combo.start_combo(selected_appliance)
                    p.success(f"家電を選択しました: "f"{selected_appliance['display_name']}")
                    continue #!家電選択に使ったPOINTはコンボへ送らない
            #?コンボ中の場合
            else:
                combo_result = combo.combo_process(gesture)
                combo_status = combo_result["status"]

                if combo_status == "COMPLETED":
                    p.success(f"コンボ成功: {combo_result['action']}")
                    feedback.feedback("go",combo_status)
                    if gesture["confirmed_gesture"] == "POINT":
                        feedback.feedback("start","start")
                        wait_point_release = True
                    #!ここでActionManagerへ送る
                    action.action_process(combo_result["action"])
                elif combo_status == "FAILED":
                    feedback.feedback("cancel",combo_status)
                    p.error("登録されたコンボと一致しませんでした")

                elif combo_status == "CANCELED":
                    feedback.feedback("cancel",combo_status)
                    p.warning("コンボをキャンセルしました")
                    

                elif combo_status == "WAITING":
                    feedback.feedback("beep",combo_status)
                    pass


            side_frame = camera.read_frame("side")
            if side_frame is None:
                continue

    finally:
        human_position.close()
        camera.stop_camera()
        preview.close_window()
        p.debug("終わり")

if __name__ == "__main__":
    main()