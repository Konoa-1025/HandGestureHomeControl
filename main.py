#main.py
#Norifumi Konndo
#情報集め役 兼 司令塔

import debug.watching

#モジュール読み込み
import time
import art

art.tprint("HandGestureHC")
#ファイル読み込み 優先順位 >上<
import utils.logPrint as p
import senders.tcpSender as tcp
import utils.configLoader as figload
import managers.cascadeManager as cas
import managers.modelManager as model
import managers.cameraManager as camera
import managers.systemMonitor as systemM

def main():
    #設定読み込み
    _config = figload.load_config()
    

    #tcp初期化・接続
    tcp.connect_all(_config)
    time.sleep(_config["system"]["startup_wait"])

    #カスケード初期化
    cas.Initialization(_config["thresholds"]["cascade"]["memory"]["low"],_config["thresholds"]["cascade"]["memory"]["high"])
    #モデル初期化
    model.Initialization(_config["thresholds"]["cascade"]["memory"]["low"],_config["thresholds"]["cascade"]["memory"]["high"])

    if not camera.start_camera():
        camera._debug_camera()

    p.success("◆◇◆ Ready Hand Gesture Home Control ◆◇◆")
    
    while True:

        #システム情報取得
        _system = systemM.get_status()

        #システム切り替え
        cas.update(_system)
        model.update(_system)

        #カメラから映像を取得
        _frames = camera.read_frames()
        _frames = cas.run(_frames)
        #_result = model.run(_frames)
        time.sleep(_config["system"]["startup_wait"])

if __name__ == "__main__":
    
    main()

