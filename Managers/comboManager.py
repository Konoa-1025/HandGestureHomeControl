
#? Managers/comboManager.py
#? Norifumi Kondo

import csv
import time

import Utils.logger as p


combos = []

combo_active = False
selected_appliance = None
gesture_history = []

combo_started_at = None
next_input_at = None
none_started_at = None
last_input_gesture = None

input_interval_seconds = 0.5
timeout_seconds = 5.0
none_timeout_seconds = 0.5


def Initialization(settings):
    global combos
    global input_interval_seconds
    global timeout_seconds
    global none_timeout_seconds

    p.info("comboManagerを初期化中")

    input_interval_seconds = settings["combo"]["timing"]["input_interval_seconds"]
    timeout_seconds = settings["combo"]["timing"]["timeout_seconds"]
    none_timeout_seconds = settings["combo"]["timing"]["none_timeout_seconds"]
    csv_path = settings["combo"]["combo_csv_path"]

    if input_interval_seconds <= 0:
        p.error("input_interval_secondsが正しくありません")
        return False

    if timeout_seconds <= 0:
        p.error("timeout_secondsが正しくありません")
        return False

    if none_timeout_seconds < 0:
        p.error("none_timeout_secondsが正しくありません")
        return False

    try:
        with open(csv_path, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            combos = []

            for row in reader:
                if not row["appliances"]:
                    continue

                gestures = []

                for gesture_key in ["gesture1", "gesture2", "gesture3", "gesture4"]:
                    if row[gesture_key]:
                        gestures.append(row[gesture_key])

                combos.append({
                    "appliances": row["appliances"],
                    "gestures": gestures,
                    "action": row["action"]
                })

    except Exception as error:
        p.error(f"コンボCSVの読み込みに失敗しました: {error}")
        return False

    reset_combo()

    p.success(f"comboManagerの初期化完了 ({len(combos)}件)")
    return True


def is_combo():
    return combo_active


def start_combo(appliance):
    global combo_active
    global selected_appliance
    global gesture_history
    global combo_started_at
    global next_input_at
    global none_started_at
    global last_input_gesture

    now = time.monotonic()

    combo_active = True
    selected_appliance = appliance["device"]
    gesture_history = []

    combo_started_at = now
    next_input_at = now + input_interval_seconds
    none_started_at = None
    last_input_gesture = None

    p.info(f"コンボ開始: {selected_appliance}")

    return True


def reset_combo():
    global combo_active
    global selected_appliance
    global gesture_history
    global combo_started_at
    global next_input_at
    global none_started_at
    global last_input_gesture

    combo_active = False
    selected_appliance = None
    gesture_history = []

    combo_started_at = None
    next_input_at = None
    none_started_at = None
    last_input_gesture = None


def combo_process(gesture):
    global next_input_at
    global gesture_history
    global none_started_at
    global last_input_gesture

    now = time.monotonic()

    if not combo_active:
        return {"status": "INACTIVE","action": None}

    if combo_started_at is None or next_input_at is None:
        reset_combo()

        return {"status": "CANCELED","action": None}

    if now - combo_started_at >= timeout_seconds:
        reset_combo()

        return {"status": "CANCELED","action": None}

    if now < next_input_at:
        return {"status": "WAITING","action": None}

    next_input_at = now + input_interval_seconds

    confirmed_gesture = gesture["confirmed_gesture"]

    #? 一瞬Noneになっても、すぐにはキャンセルしない
    if confirmed_gesture is None:
        if none_started_at is None:
            none_started_at = now

        if now - none_started_at >= none_timeout_seconds:
            reset_combo()

            return {"status": "CANCELED","action": None}

        return {"status": "WAITING","action": None}

    #? 手が確定したのでNone計測を解除
    none_started_at = None

    #? 同じ手を維持しているだけなら、もう一度履歴へ入れない
    if confirmed_gesture == last_input_gesture:
        return {"status": "WAITING","action": None}

    last_input_gesture = confirmed_gesture
    gesture_history.append(confirmed_gesture)

    p.debug(f"コンボ履歴: {gesture_history}")

    return check_combo()


def check_combo():
    candidates = []

    for combo in combos:
        if combo["appliances"] != selected_appliance:
            continue

        combo_gestures = combo["gestures"]

        if len(gesture_history) > len(combo_gestures):
            continue

        if combo_gestures[:len(gesture_history)] == gesture_history:
            candidates.append(combo)

    if not candidates:
        reset_combo()

        return {
            "status": "FAILED",
            "action": None
        }

    for combo in candidates:
        if combo["gestures"] == gesture_history:
            action = combo["action"]

            reset_combo()

            return {"status": "COMPLETED","action": action}

    return {"status": "WAITING","action": None}