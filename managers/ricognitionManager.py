#ricognitionManager.py
#Norifumi Konndo
#リコライズマネージャー
import recognizers.gestureRecognizer as rico
import recognizers.gestureStabilizer as stab
import recognizers.pointingEstimator as est

def Initialization(_settings):
    rico.Initialization("")
    stab.Initialization("")
    est.Initialization("")

    return True

def run(_handpoint):
    _hand = rico.run(_handpoint)
    _gesture = stab.run(_hand)
    _gestureEST = est.run(_gesture)
    
    return _gestureEST