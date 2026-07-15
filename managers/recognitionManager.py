# recognitionManager.py
# Norifumi Konndo
# リコグニションマネージャー
import utils.logPrint as p
import managers.appliancesManager as home
import recognizers.gestureRecognizer as rico
import recognizers.gestureStabilizer as stab
import recognizers.pointingEstimator as est


def Initialization(_settings):
    p.info("初期化中")

    _recognition_settings = _settings.get("recognition", _settings)

    rico.Initialization(_recognition_settings.get("recognizer", {}))
    stab.Initialization(_recognition_settings.get("stabilizer", {}))
    est.Initialization(_recognition_settings.get("estimator", {}))

    p.success("初期化成功")
    return True


def run(_model_result):
    _result = _model_result.get("hands", [])

    _result = rico.run(_result)
    _result = stab.run(_result)
    _result = est.run(_result)

    _selected = _select_confirmed_gesture(_result)

    if _selected is None:
        return None

    home.resolve_appliance(_selected.get("direction"))

    return {
        "camera": _selected["camera_index"],
        "gesture": _selected["stabilized_gesture"],
        "direction": _selected.get("direction"),
        "is_cached": _selected.get("is_cached", False)
    }

def _select_confirmed_gesture(_gestures):
    _confirmed = [
        _gesture
        for _gesture in _gestures
        if _gesture["stabilized_gesture"] is not None
    ]

    if not _confirmed:
        return None

    _gesture_names = {
        _gesture["stabilized_gesture"]
        for _gesture in _confirmed
    }

    if len(_gesture_names) > 1:
        return None

    return _confirmed[0]