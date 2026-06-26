#main.py
#26/06/26
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
    tcp.connect_all()
    time.sleep(1)
    p.success("◆◇◆ Ready Hand Gesture Home Control ◆◇◆")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()

