
#? Core/initializer.py
#? Norifumi Konndo

import Utils.logger as p

import Managers.actionManager as action
import Managers.cameraManager as camera
import Managers.cascadeManager as cascade
import Managers.comboManager as combo
import Managers.systemManager as system
import Managers.tcpManager as tcp
import Managers.echonetManager as echonet
import Managers.recognitionManager as recognition
import Managers.experimentManager as experiment
import Managers.modelManager as model
import Managers.feedbackManager as sound

def Managers_initialize():
    #!Managersの初期化
    p.info("Managersの初期化中")
    if not action.Initialization(None):
        p.error("actionManagerの初期化に失敗しました")
        return False
    if not camera.Initialization(None):
        p.error("cameraManagerの初期化に失敗しました")
        return False
    if not cascade.Initialization(None):
        p.error("cascadeManagerの初期化に失敗しました")
        return False
    if not combo.Initialization(None):
        p.error("comboManagerの初期化に失敗しました")
        return False
    if not system.Initialization(None):
        p.error("systemManagerの初期化に失敗しました")
        return False
    if not tcp.Initialization(None):
        p.error("tcpManagerの初期化に失敗しました")
        return False
    if not echonet.Initialization(None):
        p.error("echonetManagerの初期化に失敗しました")
        return False
    if not recognition.Initialization(None):
        p.error("recognitionManagerの初期化に失敗しました")
        return False
    if not experiment.Initialization(None):
        p.error("experimentManagerの初期化に失敗しました")
        return False
    if not model.Initialization(None):
        p.error("modelManagerの初期化に失敗しました")
        return False
    if not sound.Initialization(None):
        p.error("soundManagerの初期化に失敗しました")
        return False
    
    p.success("Managersの初期化完了")
    return True