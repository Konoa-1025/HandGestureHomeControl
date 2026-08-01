
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
import Managers.feedbackManager as feedback

def Managers_initialize(config):
    #!Managersの初期化
    p.info("Managersの初期化中")
    if not action.Initialization(config):
        p.error("actionManagerの初期化に失敗しました")
        return False
    
    if not camera.Initialization(config):
        p.error("cameraManagerの初期化に失敗しました")
        return False
    
    if not cascade.Initialization(config):
        p.error("cascadeManagerの初期化に失敗しました")
        return False
    
    if not combo.Initialization(config):
        p.error("comboManagerの初期化に失敗しました")
        return False
    
    if not system.Initialization():
        p.error("systemManagerの初期化に失敗しました")
        return False
    
    if not tcp.Initialization(config):
        p.error("tcpManagerの初期化に失敗しました")
        return False
    
    if not echonet.Initialization(config):
        p.error("echonetManagerの初期化に失敗しました")
        return False
    
    if not recognition.Initialization(config):
        p.error("recognitionManagerの初期化に失敗しました")
        return False
    
    if not experiment.Initialization(config):
        p.error("experimentManagerの初期化に失敗しました")
        return False
    
    if not model.Initialization(config):
        p.error("modelManagerの初期化に失敗しました")
        return False
    
    if not feedback.Initialization(config):
        p.error("feedbackManagerの初期化に失敗しました")
        return False
    
    if not feedback.Initialization(config):
        p.error("feedbackManagerの初期化に失敗しました")
        return False
    
    p.success("Managersの初期化完了")
    return True