
#? Recognizers/gestureStabilizer.py
#? Norifumi Kondo

import time
import math
import Utils.logger as p


confirmation_seconds = 0.3
mismatch_tolerance_seconds = 0.1
lost_timeout_seconds = 0.5


current_gesture = None
gesture_started_at = None
gesture_mismatch_started_at = None
confirmed_gesture = None

current_direction = None
direction_started_at = None
direction_mismatch_started_at = None
confirmed_direction = None

last_hand_detected_at = None

#?家電中心への指差し保持。ジェスチャ確定とは別に時間を数える
pending_target = None
hold_elapsed = 0.0
last_target_time = None
last_valid_time = None
previous_valid = False
target_latched = False
target_state = "NO_HAND"



def Initialization(settings):
    global confirmation_seconds
    global mismatch_tolerance_seconds
    global lost_timeout_seconds

    p.info("gestureStabilizerを初期化中")

    try:
        stabilizer_settings = settings["recognition"]["stabilizer"]

        confirmation_seconds = stabilizer_settings[
            "confirmation_seconds"
        ]

        mismatch_tolerance_seconds = stabilizer_settings[
            "mismatch_tolerance_seconds"
        ]

        lost_timeout_seconds = stabilizer_settings[
            "lost_timeout_seconds"
        ]

        if confirmation_seconds <= 0:
            p.error("confirmation_secondsが正しくありません。")
            return False

        if mismatch_tolerance_seconds < 0:
            p.error("mismatch_tolerance_secondsが正しくありません。")
            return False

        if lost_timeout_seconds < 0:
            p.error("lost_timeout_secondsが正しくありません。")
            return False

        reset()

        p.success("gestureStabilizerの初期化完了")
        return True

    except KeyError as error:
        p.error(
            f"gestureStabilizerの設定が不足しています: {error}"
        )
        return False

    except Exception as error:
        p.error(f"gestureStabilizerの初期化に失敗しました: {error}")
        return False


def reset_gesture():
    global current_gesture
    global gesture_started_at
    global gesture_mismatch_started_at
    global confirmed_gesture

    current_gesture = None
    gesture_started_at = None
    gesture_mismatch_started_at = None
    confirmed_gesture = None


def reset_direction():
    global current_direction
    global direction_started_at
    global direction_mismatch_started_at
    global confirmed_direction

    current_direction = None
    direction_started_at = None
    direction_mismatch_started_at = None
    confirmed_direction = None


def reset():
    global last_hand_detected_at

    reset_gesture()
    reset_direction()

    last_hand_detected_at = None
    reset_target()


def get_confirmed_gesture(raw_gesture, timestamp=None):
    global current_gesture
    global gesture_started_at
    global gesture_mismatch_started_at
    global confirmed_gesture
    global last_hand_detected_at

    now = time.monotonic() if timestamp is None else timestamp

    if raw_gesture is None:
        return confirmed_gesture

    gesture_name = raw_gesture.get("name", "UNKNOWN")

    if gesture_name == "UNKNOWN":
        if gesture_mismatch_started_at is None:
            gesture_mismatch_started_at = now

        mismatch_elapsed = (
            now - gesture_mismatch_started_at
        )

        if mismatch_elapsed >= mismatch_tolerance_seconds:
            reset_gesture()
            reset_direction()

        return confirmed_gesture

    last_hand_detected_at = now

    if current_gesture is None:
        current_gesture = gesture_name
        gesture_started_at = now
        gesture_mismatch_started_at = None

        return confirmed_gesture

    if gesture_name == current_gesture:
        gesture_mismatch_started_at = None

        if gesture_started_at is None:
            gesture_started_at = now

        gesture_elapsed = now - gesture_started_at

        if gesture_elapsed >= confirmation_seconds:
            confirmed_gesture = gesture_name

        return confirmed_gesture

    if gesture_mismatch_started_at is None:
        gesture_mismatch_started_at = now

        return confirmed_gesture

    mismatch_elapsed = (
        now - gesture_mismatch_started_at
    )

    if mismatch_elapsed < mismatch_tolerance_seconds:
        return confirmed_gesture

    current_gesture = gesture_name
    gesture_started_at = now
    gesture_mismatch_started_at = None
    confirmed_gesture = None

    reset_direction()

    return confirmed_gesture


def get_confirmed_direction(direction_data, timestamp=None):
    global current_direction
    global direction_started_at
    global direction_mismatch_started_at
    global confirmed_direction

    now = time.monotonic() if timestamp is None else timestamp

    if direction_data is None:
        return confirmed_direction

    direction = direction_data.get(
        "direction",
        "UNKNOWN"
    )

    if direction == "UNKNOWN":
        if direction_mismatch_started_at is None:
            direction_mismatch_started_at = now

        mismatch_elapsed = (
            now - direction_mismatch_started_at
        )

        if mismatch_elapsed >= mismatch_tolerance_seconds:
            reset_direction()

        return confirmed_direction

    if current_direction is None:
        current_direction = direction
        direction_started_at = now
        direction_mismatch_started_at = None

        return confirmed_direction

    if direction == current_direction:
        direction_mismatch_started_at = None

        if direction_started_at is None:
            direction_started_at = now

        direction_elapsed = now - direction_started_at

        if direction_elapsed >= confirmation_seconds:
            confirmed_direction = direction

        return confirmed_direction

    if direction_mismatch_started_at is None:
        direction_mismatch_started_at = now

        return confirmed_direction

    mismatch_elapsed = (
        now - direction_mismatch_started_at
    )

    if mismatch_elapsed < mismatch_tolerance_seconds:
        return confirmed_direction

    current_direction = direction
    direction_started_at = now
    direction_mismatch_started_at = None
    confirmed_direction = None

    return confirmed_direction


def check_lost_hand(timestamp=None):
    global last_hand_detected_at

    if last_hand_detected_at is None:
        return

    now = time.monotonic() if timestamp is None else timestamp
    lost_elapsed = now - last_hand_detected_at

    if lost_elapsed >= lost_timeout_seconds:
        #!手が消えても家電の解除待ちは残す
        reset_gesture()
        reset_direction()
        last_hand_detected_at = None


def stabilizer_process(raw_gesture,direction_data=None,timestamp=None):
    check_lost_hand(timestamp)

    stable_gesture = get_confirmed_gesture(raw_gesture, timestamp)

    stable_direction = None

    if raw_gesture is not None:
        gesture_name = raw_gesture.get("name","UNKNOWN")

        if gesture_name == "POINT":
            stable_direction = get_confirmed_direction(direction_data, timestamp)

        else:
            reset_direction()

    return {"confirmed_gesture": stable_gesture,"confirmed_direction": stable_direction}



def clear_target_hold():
    global pending_target, hold_elapsed, last_valid_time, previous_valid
    pending_target = None
    hold_elapsed = 0.0
    last_valid_time = None
    previous_valid = False


def reset_target():
    global last_target_time, target_latched, target_state
    clear_target_hold()
    last_target_time = None
    target_latched = False
    target_state = "NO_HAND"


def target_process(result, timestamp, hold_seconds, gap_seconds, allow_selection=True):
    global pending_target, hold_elapsed, last_target_time, last_valid_time
    global previous_valid, target_latched, target_state

    if not math.isfinite(timestamp):
        raise ValueError("指差し判定の時刻が正しくありません")
    if last_target_time is not None and timestamp < last_target_time:
        reset_target()
    previous_time = last_target_time
    last_target_time = timestamp
    target_state = result["reason"] if allow_selection else "COMBO"

    if result["gesture"] in ("OPEN_HAND", "FIST", "PEACE"):
        target_latched = False
        clear_target_hold()
        return None
    if target_latched:
        target_state = "WAIT_RELEASE"
        return None

    candidate = result["candidate"] if allow_selection else None
    if candidate is None:
        previous_valid = False
        if not allow_selection:
            target_state = "COMBO"
        if (pending_target is not None and gap_seconds > 0
                and timestamp - last_valid_time <= gap_seconds + 1e-9):
            target_state = "TRACKING_GAP"
        else:
            clear_target_hold()
        return None

    if candidate != pending_target:
        clear_target_hold()
        pending_target = candidate
    elif previous_valid:
        hold_elapsed += timestamp - previous_time
    elif timestamp - last_valid_time > gap_seconds + 1e-9:
        hold_elapsed = 0.0

    last_valid_time = timestamp
    previous_valid = True
    target_state = "SELECTING"
    if hold_elapsed + 1e-9 < hold_seconds:
        return None

    hold_elapsed = hold_seconds
    target_latched = True
    target_state = "WAIT_RELEASE"
    return candidate
