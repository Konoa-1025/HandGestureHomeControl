#main.py
#Norifumi Konndo
#情報集め役 兼 司令塔

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
    _config = figload.load_config()
    tcp.connect_all(_config)
    time.sleep(_config["system"]["startup_wait"])

    p.success("◆◇◆ Ready Hand Gesture Home Control ◆◇◆")
    
    while True:
        _system = systemM.get_status()
        cas.update(_system)
        model.update(_system)
        time.sleep(_config["system"]["startup_wait"])

if __name__ == "__main__":
    
    main()

