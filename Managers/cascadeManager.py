
#? Managers/cascadeManager.py
#? Norifumi Konndo

import Utils.logger as p
import Cascades.highCascade as highCascade
import Cascades.motionCascade as motionCascade
import Cascades.lowCascade as lowCascade

import cv2

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
    low_width = settings["cascade"]["resolution"]["low"]["width"]
    low_height = settings["cascade"]["resolution"]["low"]["height"]
    high_width = settings["cascade"]["resolution"]["high"]["width"]
    high_height = settings["cascade"]["resolution"]["high"]["height"]

    # lowとhighの順番チェック
    if low >= high:
        p.error("cascade設定エラー")
        p.error("lowはhighより小さくしてください。")
        return False

    # ヒステリシス幅チェック
    if high - low < 20:
        p.error("cascade設定エラー")
        p.error("ヒステリシス幅は20%以上必要です。")
        p.error(f"現在 : {high - low}%")
        return False

    current_mode = "high"

    p.success("cascadeManagerの初期化完了")

    #!Cascadeの初期化
    p.info("Cascadesの初期化中")
    if not highCascade.Initialization(None):
        p.error("highCascadeの初期化に失敗しました")
        return False
    if not motionCascade.Initialization(None):
        p.error("motionCascadeの初期化に失敗しました")
        return False
    if not lowCascade.Initialization(None):
        p.error("lowCascadeの初期化に失敗しました")
        return False
    p.success("Cascadesの初期化完了")

    return True

current_mode = "high"

def cascade_selection(frame,select_mode):
    pass

def motion_check(frame):
    return motionCascade.is_human(frame)

def cascade_process(frame,memory_usage_rate):
    global current_mode

    if frame is None:
            p.error("フレームがNoneです。")
            return False
    
    if motion_check(frame) == True:
            p.debug("人を検知")
        #?ヒステリシス制御
            if memory_usage_rate >= high:
                current_mode = "low"
                p.change("lowcascade")
            elif memory_usage_rate <= low:
                current_mode = "high"
                p.change("highcascade")
            frame = cascade_selection(frame,current_mode)
            return frame
    else:
        return

def get_mode():
    return current_mode




