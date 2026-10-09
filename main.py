
#? main.py
#? Norifumi Konndo
#! Python 3.11以上指定
#? 役割：親,司令塔

import argparse
import copy
import time
from pathlib import Path

import cv2
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
import Managers.positionManager as position
import Managers.echonetManager as echonet



def make_options(argv=None):
    parser = argparse.ArgumentParser(description="HGHC ジェスチャー操作とプレビュー")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", dest="dry_run", action="store_true")
    mode.add_argument("--live", dest="dry_run", action="store_false")
    parser.set_defaults(dry_run=None)
    parser.add_argument("--video", type=Path)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, default=0)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--edit-centers", action="store_true", help="家電中心の編集。実機への送信はしません")
    parser.add_argument("--paused", action="store_true")
    options = parser.parse_args(argv)
    if options.start_frame < 0 or options.frames < 0:
        parser.error("フレーム数は0以上にしてください")
    if options.headless and (options.frames == 0 or options.paused or options.edit_centers):
        parser.error("headlessには正の--framesが必要です。一時停止と中心編集は使えません")
    if options.edit_centers and options.dry_run is False:
        parser.error("中心編集中は実機制御できません")
    return options


def record_event(status, message):
    status["history"].insert(0, message)
    del status["history"][5:]
    p.info(message)


def execute_action(action_name, dry_run, status):
    status["last_action"] = action_name
    if dry_run:
        status["action_status"] = "SIMULATED"
    else:
        success = action.action_process(action_name)
        status["action_status"] = "SENT" if success else "FAILED"
        feedback.feedback("go" if success else "cancel")
    status["state"] = status["action_status"]
    record_event(status, f"{status['action_status']}: {action_name}")


def gesture_process(hand_landmarks, frame_shape, timestamp, current_position, status, dry_run):
    #?手が消えたフレームでも、コンボの期限と解除待ちは確認する
    expired = combo.expire(timestamp)
    if expired:
        recognize.stabilizer.reset_target()
        record_event(status, "COMBO TIMEOUT")
        if not dry_run:
            feedback.feedback("cancel")

    gesture = recognize.gesture_process(
        hand_landmarks, timestamp, frame_shape,
        not combo.is_combo() and not status["wait_point_release"]
    )
    raw_gesture = gesture["raw_gesture"]
    confirmed_gesture = gesture["confirmed_gesture"]
    point_data = gesture["point_data"]
    status["point_data"] = point_data
    status["gesture"] = point_data["gesture"] if point_data is not None else raw_gesture
    status["confirmed_gesture"] = confirmed_gesture
    status["hand"] = "DETECTED" if hand_landmarks["is_hand"] else "NONE"
    status["state"] = recognize.stabilizer.target_state if recognize.pointing.enabled else "NOT_POINTING"
    if not hand_landmarks["is_hand"] and not recognize.pointing.enabled:
        status["state"] = "NO_HAND"

    if status["wait_point_release"]:
        if raw_gesture not in ("OPEN_HAND", "FIST", "PEACE") or confirmed_gesture != raw_gesture:
            status["state"] = "COMBO_TIMEOUT" if expired else "WAIT_RELEASE"
            return
        status["wait_point_release"] = False

    #?コンボ中ではない場合は家電を選択
    if not combo.is_combo():
        selected_appliance = None
        if recognize.pointing.enabled:
            if gesture["target"] == "LIGHT":
                execute_action("all_lights_power_off", dry_run, status)
                status["wait_point_release"] = True
                return
            selected_appliance = appliances.get_appliance(gesture["target"])
        elif confirmed_gesture == "POINT" and gesture["confirmed_direction"] is not None:
            selected_appliance = appliances.select_appliance_abstract(gesture["confirmed_direction"], current_position)

        if selected_appliance is not None:
            combo.start_combo(selected_appliance, timestamp)
            status["state"] = "COMBO"
            record_event(status, f"SELECT: {selected_appliance['device']}")
            p.success(f"家電を選択しました: {selected_appliance['display_name']}")
            if not dry_run:
                feedback.reset()
                feedback.feedback("start")
            return #!家電選択に使ったPOINTはコンボへ送らない
        if expired:
            status["state"] = "COMBO_TIMEOUT"

    #?コンボ中の場合
    else:
        #!前の確定結果が残っていても、現在の手や指差し先が違えば入力しない
        if raw_gesture != confirmed_gesture or raw_gesture not in ("POINT", "OPEN_HAND", "FIST", "PEACE"):
            gesture["confirmed_gesture"] = None
        elif recognize.pointing.enabled and raw_gesture == "POINT" and point_data["candidate"] != combo.selected_appliance:
            gesture["confirmed_gesture"] = None
        combo_result = combo.combo_process(gesture, timestamp)
        combo_status = combo_result["status"]
        status["state"] = "COMBO" if combo_status == "WAITING" else "COMBO_" + combo_status

        if combo_status == "COMPLETED":
            p.success(f"コンボ成功: {combo_result['action']}")
            execute_action(combo_result["action"], dry_run, status)
            status["wait_point_release"] = confirmed_gesture == "POINT"
        elif combo_status in ("FAILED", "CANCELED"):
            recognize.stabilizer.reset_target()
            record_event(status, "COMBO " + combo_status)
            if not dry_run:
                feedback.feedback("cancel", combo_status)
        elif combo_status == "WAITING" and not dry_run:
            feedback.feedback("beep", combo_status)


def main(options=None):
    options = options or make_options([])
    last_is_hand = False
    setting_config = copy.deepcopy(figload.load_setting_config()) #?設定の読み込み
    if options.video is not None:
        setting_config["camera"]["sources"] = [{
            "id": "front", "type": "movie", "movie": True, "enabled": True,
            "loop": True, "connection": {"path": str(options.video)}
        }]
    front_source = next((source for source in setting_config["camera"]["sources"]
                        if source.get("id") == "front" and source.get("enabled", True)), {})
    movie = front_source.get("type", "").lower() == "movie"
    dry_run = movie if options.dry_run is None else options.dry_run
    if options.edit_centers:
        dry_run = True
        setting_config.setdefault("pointing", {})["enabled"] = True
    setting_config.setdefault("runtime", {}).update(dry_run=dry_run, headless=options.headless)
    status = {
        "wait_point_release": False, "history": [], "last_action": None,
        "action_status": None, "mode": "SIMULATION" if dry_run else "LIVE"
    }
    frame_count = 0
    last_timestamp = None
    playback_count = 0
    paused = options.paused
    advance = True
    cased_frame = None
    current_position = None
    last_clock = time.monotonic()
    fps = 0.0

    try:
        if not initializer.Managers_initialize(setting_config): #?初期化
            return False
        #?カメラの起動
        if not camera.start_camera() or camera.get_capture("front") is None:
            p.error("フロントカメラを開くことができませんでした")
            return False
        if movie and options.start_frame:
            camera.get_capture("front").set(cv2.CAP_PROP_POS_FRAMES, options.start_frame)
        if options.edit_centers:
            preview.start_center_edit()
        p.info("SIMULATION: 実機送信なし" if dry_run else "LIVE: 実機制御あり")

        while True:
            if not paused or advance:
                front_frame = camera.read_frame("front")
                #!メインカメラ
                if front_frame is None:
                    if movie or camera.is_finished("front"):
                        break
                    p.error("フロントカメラの映像を取得できませんでした")
                    return False

                timestamp = camera.get_timestamp("front")
                current_playback = camera.playback_count.get("front", 0)
                if ((last_timestamp is not None and timestamp < last_timestamp)
                        or current_playback != playback_count):
                    combo.reset_combo()
                    recognize.stabilizer.reset()
                    status.update(wait_point_release=False, last_action=None, action_status=None)
                    record_event(status, "VIDEO RESTART")
                last_timestamp = timestamp
                playback_count = current_playback

                cascade_result = cascade.cascade_process(front_frame,system.get_mem()) #?返り値：軽量化フレーム
                if cascade_result is None:
                    return False
                is_motion = cascade_result["is_motion"]
                cased_frame = cascade_result["cased_frame"]
                current_position = None
                if not recognize.pointing.enabled:
                    current_position = position.position_process(cased_frame)

                hand_landmarks = {"is_hand": False, "hands": []}
                if recognize.pointing.enabled or is_motion or last_is_hand:
                    hand_landmarks = model.model_process(cased_frame,system.get_cpu(),0)
                last_is_hand = hand_landmarks["is_hand"]

                if options.edit_centers:
                    gesture = recognize.gesture_process(hand_landmarks, timestamp, cased_frame.shape)
                    status.update(point_data=gesture["point_data"], gesture=gesture["raw_gesture"],
                                confirmed_gesture=gesture["confirmed_gesture"], state=recognize.stabilizer.target_state)
                    if gesture["target"]:
                        record_event(status, "SIMULATION: " + gesture["target"])
                else:
                    gesture_process(hand_landmarks, cased_frame.shape, timestamp, current_position, status, dry_run)

                #?サイドカメラは既存の読み出しを残す
                camera.read_frame("side")
                frame_count += 1
                now = time.monotonic()
                current_fps = 1 / max(now - last_clock, 0.001)
                fps = current_fps if frame_count == 1 else fps * 0.8 + current_fps * 0.2
                last_clock = now
                status.update(input="VIDEO" if movie else "CAMERA", fps=fps,
                            frame_index=int(camera.get_capture("front").get(cv2.CAP_PROP_POS_FRAMES)) if movie else frame_count)
                advance = False

            if options.edit_centers:
                status["point_data"] = recognize.pointing.get_target(
                    hand_landmarks, cased_frame.shape, {"name": status["gesture"]}
                )
                status["state"] = recognize.stabilizer.target_state
            status.update(paused=paused, selected=combo.selected_appliance, combo_history=list(combo.gesture_history),
                        combo_remaining=max(0, combo.timeout_seconds - (timestamp - combo.combo_started_at)) if combo.combo_started_at is not None else None)
            if not options.headless:
                if recognize.pointing.enabled:
                    if not preview.show_frame_pointing(cased_frame, status):
                        break
                elif not preview.show_frame_detail(cased_frame, current_position):
                    break
                if movie or options.edit_centers:
                    if preview.last_key == ord(" "):
                        paused = not paused
                        last_clock = time.monotonic()
                    elif preview.last_key == ord("n"):
                        paused, advance = True, True
                if options.edit_centers:
                    preview.edit_center_key(preview.last_key)
            if options.frames and frame_count >= options.frames:
                break

        if options.snapshot and cased_frame is not None:
            display = preview.draw_pointing(cased_frame, status) if recognize.pointing.enabled else preview.draw_detail(cased_frame, current_position)
            options.snapshot.parent.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(options.snapshot), display):
                raise OSError("プレビュー画像を保存できませんでした")
        p.info(f"{frame_count}フレームを処理しました")
        return True
    finally:
        if preview.centers_dirty:
            p.warning("中心点の変更は未保存です。保存するときはSを押してください")
        position.close()
        model.close()
        camera.stop_camera()
        preview.close_window()
        combo.reset_combo()
        if not dry_run:
            echonet.close()
        p.debug("終わり")


if __name__ == "__main__":
    main(make_options())
