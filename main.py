# main.py
# Norifumi Kondo
import time
import logPrint as p
import tcpSender as tcp

p.info("■■ Hand Gesture Home Control ■■")

# TCP接続開始
tcp.connect_all()
p.info("TCP接続開始")
time.sleep(2) #TCP接続の安定化のために少し待機

# モジュールのインポート
import cameraManager as camera
import echonetSender as echonet
import Models.standbyModel as stand
import Models.lowModel as low
import Models.highModel as high


p.success("システム起動完了")

#処理部
camera_cap = camera.start_camera()
if not camera.start_camera():
    p.error("カメラが起動できません")

_frames = camera.read_frames()


# メインループ
while True:
    time.sleep(1)