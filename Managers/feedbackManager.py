
#? Managers/feedbackManager.py
#? Norifumi Konndo

import Utils.logger as p
import Feedback.sound as sound


def Initialization(settings):

    p.info("feedbackManagerを初期化中")
    p.info("フィードバックファイル読み込み中")

    p.success("feedbackManagerの初期化完了")

    sound.Initialization(settings["feedback"]["sound"])

    return True