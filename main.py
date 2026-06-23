# main.py
# Norifumi Kondo
import time
import logPrint as p
import tcpSender as tcp
import psutil
import threading
import time

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

# システム保護/モデル切り替え
_model = "standby"  # standby / low / highModel
_autoChangeModels= False       # Trueなら自動切り替えON


def _change_model(_next_model):
    global _model
    if _model == _next_model:
        return
    _model = _next_model
    if _next_model == "standby":
        standbyModel._startModel()
    elif _next_model == "low":
        lowModel._startModel()
    elif _next_model == "highModel":
        highModel._startModel()
    else:
        p.error("切り替え対象が見つかりません")
        return
    p.info(f"モデルを{_model}に切り替えました。")


def monitor_cpu(_initial_time, _event):
    p.info("CPUモニター開始")
    while not _event.wait(0.5):
        _mem = psutil.virtual_memory().percent
        _cpu = psutil.cpu_percent()
        # 人がいるときだけ自動切り替え
        if _autoChangeModels:
            if _cpu >= 90.0 or _mem >= 90.0:
                _next_model = "standby"
            elif _cpu >= 80.0 or _mem >= 80.0:
                _next_model = "low"
            else:
                _next_model = "highModel"
            _change_model(_next_model)
    p.info("END monitor_cpu")


_pc_monitor_event = threading.Event()
_initial_time = time.time()
_pc_monitor = threading.Thread(
    target=monitor_cpu,
    args=(_initial_time, _pc_monitor_event),
    daemon=True
)
_pc_monitor.start()



#処理部
camera_cap = camera.start_camera()
if not camera.start_camera():
    p.success("カメラに接続できました。")
    _frames = camera.read_frames()

    #_front = _frames[0]
    #_side = _frames[1]
else:
    p.error("カメラが起動できません")






# メインループ
while True:
    time.sleep(1)