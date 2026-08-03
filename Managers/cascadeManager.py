
#? Managers/cascadeManager.py
#? Norifumi Konndo

import Utils.logger as p
import Cascades.highCascade as highCascade
import Cascades.motionCascade as motionCascade
import Cascades.lowCascade as lowCascade


low = None
high = None
current_mode = "high"


def Initialization(settings):
    global low, high
    global current_mode

    p.info("cascadeManagerを初期化中")

    try:
        low = settings["cascade"]["memory_threshold_percent"]["low"]
        high = settings["cascade"]["memory_threshold_percent"]["high"]

    except (KeyError, TypeError) as error:
        p.error(f"cascade設定の読み込みに失敗しました: {error}")
        return False

    if low is None or high is None:
        p.error("cascade設定エラー")
        p.error("lowまたはhighが設定されていません。")
        return False

    if not isinstance(low, (int, float)):
        p.error("lowは数値で設定してください。")
        return False

    if not isinstance(high, (int, float)):
        p.error("highは数値で設定してください。")
        return False

    # lowとhighの順番チェック
    if low >= high:
        p.error("cascade設定エラー")
        p.error("lowはhighより小さくしてください。")
        return False

    # ヒステリシス幅チェック
    if high - low < 10:
        p.error("cascade設定エラー")
        p.error("ヒステリシス幅は10%以上必要です。")
        p.error(f"現在: {high - low}%")
        return False

    current_mode = "high"

    p.info("Cascadesを初期化中")

    if not highCascade.Initialization(settings):
        p.error("highCascadeの初期化に失敗しました。")
        return False

    if not motionCascade.Initialization(settings):
        p.error("motionCascadeの初期化に失敗しました。")
        return False

    if not lowCascade.Initialization(settings):
        p.error("lowCascadeの初期化に失敗しました。")
        return False

    p.success("Cascadesの初期化完了")
    p.success("cascadeManagerの初期化完了")

    return True


def cascade_selection(frame, select_mode):
    if select_mode == "low":
        return lowCascade.run(frame)

    if select_mode == "high":
        return highCascade.run(frame)

    p.error(f"不明なCascadeモードです: {select_mode}")
    return None


def motion_check(frame):
    return motionCascade.is_human(frame)


def cascade_process(frame, memory_usage_rate):
    global current_mode

    if frame is None:
        p.error("フレームがNoneです。")
        return None

    if memory_usage_rate is None:
        p.error("メモリ使用率がNoneです。")
        return None

    is_motion = motion_check(frame)

    # ヒステリシス制御
    if memory_usage_rate >= high:
        if current_mode != "low":
            current_mode = "low"
            p.change("lowCascade")

    elif memory_usage_rate <= low:
        if current_mode != "high":
            current_mode = "high"
            p.change("highCascade")

    cased_frame = cascade_selection(
        frame,
        current_mode
    )

    if cased_frame is None:
        return None

    return {
        "is_motion": is_motion,
        "cased_frame": cased_frame
    }


def get_mode():
    return current_mode