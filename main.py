#main.py
#Norifumi Konndo
#情報集め役 兼 司令塔
#Python 3.8対応

import time
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
import managers.dataManager as data
import senders.tcpResponse as tcpres



def main():

    _config = figload.load_config()

    if not initializer.Initialization(_config):
        return

    data.start_measurement({
        "experiment_id": "test",
        "trial_id": 1,
        "expected_gesture": "FIST",
        "brightness_percent": 50,
        "distance_m": 2.0,
        "angle_degrees": 0,
        "background": "WHITE"
    })

    tcpres.start_server(_config)

    _previous_frame_time = time.perf_counter()

    try:
        while True:
            _current_frame_time = time.perf_counter()
            _frame_time = _current_frame_time - _previous_frame_time
            _previous_frame_time = _current_frame_time

            _fps = 0.0
            if _frame_time > 0:
                _fps = 1.0 / _frame_time

            _system = systemM.get_status()
            cas.update(_system)

            _frames = camera.read_frames()
            _frames = cas.run(_frames)

            _model_result = model.run(
                _frames,
                _system
            )

            _recognition_result = rico.run(
                _model_result
            )

            _combo_result = target.run(
                _recognition_result
            )

            action.run(_combo_result)

            #!以下は計測アプリケーション用の取得系

            _hands = _model_result.get("hands", [])
            _hand_detected = len(_hands) > 0

            _stable_gesture = None

            if _recognition_result is not None:
                _stable_gesture = _recognition_result.get(
                    "gesture"
                )

            data.record_frame({
                "system": {
                    "cpu_percent": _system.get("cpu", 0.0),
                    "gpu_percent": _system.get("gpu"),
                    "memory_percent": _system.get("memory", 0.0)
                },
                "performance": {
                    "fps": round(_fps, 3),
                    "video_latency_ms": None
                },
                "model": {
                    "current": model.get_current()
                },
                "recognition": {
                    "hand_detected": _hand_detected,
                    "raw_gesture": None,
                    "stable_gesture": _stable_gesture
                }
            })

    except KeyboardInterrupt:
        pass

    finally:
        data.close()


if __name__ == "__main__":
    main()
