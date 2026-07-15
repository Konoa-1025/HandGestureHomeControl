# initializer.py
# Norifumi Konndo

import time

import managers.appliancesManager as home
import managers.cameraManager as camera
import managers.cascadeManager as cascade
import managers.conboManager as combo
import managers.modelManager as model
import managers.recognitionManager as recognition
import senders.tcpSender as tcp
import utils.logPrint as p


def _run_step(_label, _func, *_args):
    try:
        _result = _func(*_args)
    except Exception as _exc:
        p.error(f"{_label}初期化失敗: {_exc}")
        return False

    if _result is False:
        p.error(f"{_label}初期化失敗")
        return False

    return True


def Initialization(_config):
    p.info("初期化中")

    if not _run_step("TCP", tcp.connect_all, _config):
        return False

    _startup_wait = _config.get("system", {}).get("startup_wait", 0)
    if _startup_wait:
        time.sleep(_startup_wait)

    if not _run_step("Cascade", cascade.Initialization, _config):
        return False

    if not _run_step("Model", model.Initialization, _config):
        return False

    if not _run_step("Recognition", recognition.Initialization, _config):
        return False

    if not _run_step("Combo", combo.Initialization, _config):
        return False

    if not _run_step("Appliances", home.Initialization, _config):
        return False

    if not _run_step("Camera", camera.Initialization, _config):
        return False

    p.success("初期化成功")
    return True