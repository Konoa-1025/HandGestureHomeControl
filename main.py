#main.py
#Norifumi Konndo
#情報集め役 兼 司令塔
#親　上層

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
    p.info("TCP通信開始"); tcp.connect_all(_config)
    time.sleep(_config["system"]["startup_wait"])

    #カスケード初期化
    p.info("カスケード初期化");cas.Initialization(
            _config["thresholds"]["cascade"]["memory"]["low"],
            _config["thresholds"]["cascade"]["memory"]["high"],
            _config["cascade"]["low"]["width"],
            _config["cascade"]["low"]["height"],
            _config["cascade"]["high"]["width"],
            _config["cascade"]["high"]["height"],
            0,  #lostcount
            10, #lostlimit
            400 #cutsize
        )
    
    #モデル初期化
    p.info("モデル初期化");model.Initialization(
            _config["thresholds"]["model"]["memory"]["low"],
            _config["thresholds"]["model"]["memory"]["high"],
            5.0,    #PARSON_TIMEOUT
            25,     #standby_threshould
            1000    #standby_minpx
        )

    p.info("カメラ初期化")
    if not camera.start_camera():
        camera._debug_camera()
    p.success("◆◇◆ Ready Hand Gesture Home Control ◆◇◆")
    while True:
        _system = systemM.get_status()                      #使用率の取得
        cas.update(_system)                                 #カスケードの切り替え
        _frames = camera.read_frames()                      #カメラ映像取得
        _original_frames = _frames.copy()                   #カメラ映像のコピー
        _frames = cas.run(_frames)                          #カメラ映像をカスケードマネージャーに与える
        _result = model.run(_frames, _system)               #カメラ映像をモデルマネージャーに与える
        cas.updateHandPositions(_result, _original_frames)  #モデルMGからカスケードMGにROIを与える

if __name__ == "__main__":
    
    main()
