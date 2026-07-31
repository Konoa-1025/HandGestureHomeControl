
#? Managers/modelManager.py
#? Norifumi Konndo

import Utils.logger as p
import Models.cpu.highModel as highModel
import Models.cpu.lowModel as lowModel


def Initialization(settings):

    p.info("modelManagerを初期化中")

    p.success("modelManagerの初期化完了")
    
    p.info("highModelを初期化中")
    if not highModel.Initialization(settings):
        p.error("highModelの初期化に失敗しました")
        return False

    if not lowModel.Initialization(settings):
        p.error("lowModelの初期化に失敗しました")
        return False    

    return True