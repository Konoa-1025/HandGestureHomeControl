
#? Recognizers/personTracker.py
#? Norifumi Kondo

"""
将来用

役割
・人物ごとの状態管理
・人物IDの割り当て
・複数人対応
・人物と手の対応付け
・ターゲット選択状態の保持

現在のシステムは1人のみ対応のため未使用
"""

import Utils.logger as p

def Initialization(settings):

    p.info("personTrackerを初期化中")

    p.success("personTrackerの初期化完了")

    return True