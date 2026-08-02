
#? Managers/modelManager.py
#? Norifumi Konndo
#! 未実装GPU

import Utils.logger as p
import Models.cpu.highModel as highModel
import Models.cpu.lowModel as lowModel

low = 70
high = 90
current_mode = "high"
old_mode = "high"

def Initialization(settings):
    global low,high

    p.info("modelManagerを初期化中")
    low = settings["model"]["switch_threshold"]["cpu_percent"]["low"]
    high = settings["model"]["switch_threshold"]["cpu_percent"]["high"]
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

    p.success("modelManagerの初期化完了")
    
    p.info("highModelを初期化中")
    if not highModel.Initialization(settings):
        p.error("highModelの初期化に失敗しました")
        return False

    if not lowModel.Initialization(settings):
        p.error("lowModelの初期化に失敗しました")
        return False    

    return True

def model_selection(frame,select_mode):
    if select_mode == "low":
        hand_landmarks = lowModel.run(frame)
    else:
        hand_landmarks = highModel.run(frame)
    return hand_landmarks

def model_process(frame,cpu_usage_rate,gpu_usage_rate = None):
    global current_mode,old_mode
    
    if frame is None:
        p.error("フレームがNoneです。")
        return False
    
    #?ヒステリシス制御
    if cpu_usage_rate >= high:
        current_mode = "low"
        if old_mode != current_mode:
            p.change("lowModel")
            old_mode = current_mode
        
    elif cpu_usage_rate <= low:
        current_mode = "high"
        if old_mode != current_mode:
            p.change("high")
            old_mode = current_mode
    hand_landmarks = model_selection(frame,current_mode)
    return hand_landmarks