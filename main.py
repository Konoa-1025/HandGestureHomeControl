#main.py
#Norifumi Konndo
#情報集め役 兼 司令塔
#親　上層

import debug.watching

#モジュール読み込み
import time
import art

art.tprint("HandGestureHC")
# *ファイル読み込み 優先順位 >上<
import utils.logPrint as p
import senders.tcpSender as tcp
import utils.configLoader as figload
import managers.cascadeManager as cas
import managers.modelManager as model
import managers.cameraManager as camera
import managers.systemMonitor as systemM
import managers.appliancesManager as home

def main():
    #設定読み込み
    _config = figload.load_config()
    
    #tcp初期化・接続
    p.info("TCP通信開始"); tcp.connect_all(_config)
    time.sleep(_config["system"]["startup_wait"])

    #カスケード初期化
    cascade_settings = {
    "memory": {
            "low": _config["thresholds"]["cascade"]["memory"]["low"],
            "high": _config["thresholds"]["cascade"]["memory"]["high"]
    },
    "tracking": {
            "lost_count": 0,
            "lost_limit": 10,
            "crop_size": 500
    },
    "low": {
            "width": _config["cascade"]["low"]["width"],
            "height": _config["cascade"]["low"]["height"]
    },
    "high": {
            "width": _config["cascade"]["high"]["width"],
            "height": _config["cascade"]["high"]["height"]
        }
    }
    p.info("カスケード初期化")
    cas.Initialization(cascade_settings)
    
    #モデル初期化
    model_settings = {
    "memory": {
            "low": _config["thresholds"]["model"]["memory"]["low"],
            "high": _config["thresholds"]["model"]["memory"]["high"]
    },
    "cpu": {
            "low": _config["thresholds"]["model"]["cpu"]["low"],
            "high": _config["thresholds"]["model"]["cpu"]["high"]
    },
    "standby": {
            "person_timeout": 5.0,
            "threshold": 25,
            "min_pixels": 1000
    },
    "low": {
            "process_width": 640,
            "process_height": 360,
            "max_hands": 1,
            "detection_confidence": 0.4,
            "tracking_confidence": 0.4
    },
    "high": {
            "process_width": 1280,
            "process_height": 720,
            "max_hands": 2,
            "detection_confidence": 0.7,
            "tracking_confidence": 0.7
        }
    }
    p.info("モデル初期化")
    model.Initialization(model_settings)

    
    p.info("家電の読み込み");home.Initialization()


    p.info("カメラ初期化")
    if not camera.start_camera():
        camera._debug_camera()

    p.success("◆◇◆ Ready Hand Gesture Home Control ◆◇◆")

    time.sleep(1)
    
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
