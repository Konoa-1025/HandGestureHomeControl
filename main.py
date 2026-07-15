#main.py
#Norifumi Konndo
#情報集め役 兼 司令塔
#親　上層

import art

art.tprint("HandGestureHC")

import utils.configLoader as figload
import managers.cameraManager as camera
import managers.systemMonitor as systemM
import core.initializer as initializer
import managers.actionManager as action
import managers.cascadeManager as cas
import managers.modelManager as model
import managers.recognitionManager as rico
import managers.conboManager as target

def main():
    _config = figload.load_config()

    if not initializer.Initialization(_config):
        return

    while True:
        _system = systemM.get_status()                      #使用率の取得
        cas.update(_system)                                 #カスケードの切り替え
        _frames = camera.read_frames()                      #カメラ映像取得
        _frames = cas.run(_frames)                          #カメラ映像をカスケードマネージャーに与える
        _model_result = model.run(_frames, _system)
        _recognition_result = rico.run(_model_result)
        _combo_result = target.run(_recognition_result)
        action.run(_combo_result)
        

        

if __name__ == "__main__":
    main()
