
#? Managers/cascadeManager.py
#? Norifumi Konndo

import Utils.logger as p
import Cascades.highCascade as highCascade
import Cascades.motionCascade as motionCascade
import Cascades.lowCascade as lowCascade


def Initialization(settings):


    p.info("cascadeManagerを初期化中")

    
    p.success("cascadeManagerの初期化完了")

    #!Cascadeの初期化
    p.info("Cascadesの初期化中")
    if not highCascade.Initialization(None):
        p.error("highCascadeの初期化に失敗しました")
        return False
    if not motionCascade.Initialization(None):
        p.error("motionCascadeの初期化に失敗しました")
        return False
    if not lowCascade.Initialization(None):
        p.error("lowCascadeの初期化に失敗しました")
        return False
    p.success("Cascadesの初期化完了")

    return True