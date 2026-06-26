# main.py
# Norifumi Kondo
import time
import logPrint as p
import tcpSender as tcp
import psutil
import threading
import time
import cv2

p.info("■■ Hand Gesture Home Control ■■")

# TCP接続開始
tcp.connect_all()
p.info("TCP接続開始")
time.sleep(2) #TCP接続の安定化のために少し待機

# モジュールのインポート
import cameraManager as camera
import echonetSender as echonet
import Models.standbyModel as standbyModel
import Models.lowModel as lowModel
import Models.highModel as highModel
import casModels.lowLevel as lowLevel
import casModels.highLevel as highLevel


p.success("システム起動完了")

# システム保護/モデル・カスケード切り替え
_model = "standby"  # standby / low / high
_casModel = "low" #low / high
_autoChangeModels= True      # Trueなら自動切り替えON

def _change_cas(_next_cas):
    global _casModel
    if _casModel == _next_cas:
        return
    _casModel = _next_cas
    
    if _next_cas == "low":
        lowLevel._startCas()
    elif _next_cas == "high":
        highLevel._startCas
    else:
        p.error("切り替え対象が見つかりません")
        return
    p.info(f"カスケードを{_next_cas}に切り替えました。")

def _change_model(_next_model):
    global _model
    if _model == _next_model:
        return
    _model = _next_model

    if _next_model == "standby":
        standbyModel._startModel()
    elif _next_model == "low":
        lowModel._startModel()
    elif _next_model == "high":
        highModel._startModel()
    else:
        p.error("切り替え対象が見つかりません")
        return
    p.info(f"モデルを{_next_model}に切り替えました。")


def monitor_pc(_initial_time, _event):
    p.info("CPUモニター開始")

    while not _event.wait(0.5):
        _mem = psutil.virtual_memory().percent
        _cpu = psutil.cpu_percent()

        # 人がいるときだけ自動切り替え
        if _autoChangeModels:
            if _cpu >= 90.0 or _mem >= 90.0:
                _next_cas = "low"
                _next_model = "low"
            else:
                _next_cas = "high"
                _next_model = "high"

            _change_model(_next_model)
            _change_cas(_next_cas)
        else:
            _change_model("standby")
            _change_cas(_next_cas)

    p.info("END monitor_cpu")


_pc_monitor_event = threading.Event()
_initial_time = time.time()
_pc_monitor = threading.Thread(
    target=monitor_pc,
    args=(_initial_time, _pc_monitor_event),
    daemon=True
)
_pc_monitor.start()



#処理部
if camera.start_camera():
    p.success("カメラに接続できました。")
    
else:
    p.error("カメラが起動できません")
    camera._debug_camera()


# メインループ
while True:
    time.sleep(1)