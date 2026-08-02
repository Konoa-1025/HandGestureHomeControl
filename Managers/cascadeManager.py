
#? Managers/cascadeManager.py
#? Norifumi Konndo

import Utils.logger as p
import Cascades.highCascade as highCascade
import Cascades.motionCascade as motionCascade
import Cascades.lowCascade as lowCascade

low = None
high = None
low_width = None
low_height = None
high_width = None
high_height = None


def Initialization(settings):
    global low,high
    global low_width,low_height
    global high_width,high_height

    p.info("cascadeManagerを初期化中")

    low = settings["cascade"]["memory_threshold_percent"]["low"]
    high = settings["cascade"]["memory_threshold_percent"]["high"]


    # lowとhighの順番チェック
    if low >= high:
        p.error("cascade設定エラー")
        p.error("lowはhighより小さくしてください。")
        return False

    # ヒステリシス幅チェック
    if high - low < 10:
        p.error("cascade設定エラー")
        p.error("ヒステリシス幅は10%以上必要です。")
        p.error(f"現在 : {high - low}%")
        return False

    current_mode = "high"

    p.success("cascadeManagerの初期化完了")

    #!Cascadeの初期化
    p.info("Cascadesの初期化中")
    if not highCascade.Initialization(settings):
        p.error("highCascadeの初期化に失敗しました")
        return False
    if not motionCascade.Initialization(settings):
        p.error("motionCascadeの初期化に失敗しました")
        return False
    if not lowCascade.Initialization(settings):
        p.error("lowCascadeの初期化に失敗しました")
        return False
    p.success("Cascadesの初期化完了")

    return True

current_mode = "high"

def cascade_selection(frame,select_mode):
    if select_mode == "low":
        cased_frame = lowCascade.run(frame)
    else:
        cased_frame = highCascade.run(frame)
    return cased_frame

def motion_check(frame):
    return motionCascade.is_human(frame)

def cascade_process(frame,memory_usage_rate):
    global current_mode

    if frame is None:
            p.error("フレームがNoneです。")
            return False
    
    if motion_check(frame) == True:
        #?ヒステリシス制御
            if memory_usage_rate >= high:
                current_mode = "low"
                p.change("lowcascade")
            elif memory_usage_rate <= low:
                current_mode = "high"
                p.change("highcascade")
            cased_frame = cascade_selection(frame,current_mode)
            return cased_frame
    else:
        return

def get_mode():
    return current_mode




