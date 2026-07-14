# recognitionManager.py
# Norifumi Konndo
# リコグニションマネージャー
import utils.logPrint as p
import recognizers.gestureRecognizer as rico
import recognizers.gestureStabilizer as stab
import recognizers.pointingEstimator as est


def Initialization(_settings):
    rico.Initialization(_settings.get("recognizer", {}))
    stab.Initialization(_settings.get("stabilizer", {}))
    est.Initialization(_settings.get("estimator", {}))

    return True


def run(_handpoints):
    # ランドマークから各フレームの手の形を推定
    _hands = rico.run(_handpoints)
    p.debug(_hands)
    # 複数フレームの結果から手の形を確定
    _gestures = stab.run(_hands)
    #p.debug(_gestures)
    
    # 指差しの場合、手や指の向きを推定
    _results = est.run(_gestures)

    return _results