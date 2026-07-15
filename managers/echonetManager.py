# echonetManager.py
# Norifumi Konndo

import utils.logPrint as p
import senders.echonetSender as echonetSender


_initialized = False
_devices = {}
_actions = {}


def Initialization(settings):
    global _initialized, _devices, _actions

    p.info("echonetManagerを初期化中")

    _echonet_settings = settings.get("echonet", {})

    _devices = _echonet_settings.get("devices", {})
    _actions = _echonet_settings.get("actions", {})

    if not _devices:
        p.error("ECHONET Liteのデバイス設定がありません")
        return False

    if not _actions:
        p.error("ECHONET Liteのアクション設定がありません")
        return False

    _initialized = True

    p.success("echonetManagerの初期化成功")
    return True


def execute(device_name, action_name):
    if not _initialized:
        raise RuntimeError("echonetManagerが初期化されていません")

    device = _devices.get(device_name)

    if device is None:
        p.error(f"未登録のデバイスです: {device_name}")
        return False

    device_type = device.get("type")

    action_table = _actions.get(device_type, {})
    action = action_table.get(action_name)

    if action is None:
        p.error(
            f"{device_name}では未対応のアクションです: {action_name}"
        )
        return False

    ip_address = device.get("ip_address")
    deoj = device.get("deoj")
    epc = action.get("epc")
    edt = action.get("edt")
    esv = action.get("esv", "61")

    p.debug(
        "ECHONET Lite送信\n"
        f"  ip_address : {ip_address}\n"
        f"  deoj       : {deoj}\n"
        f"  esv        : {esv}\n"
        f"  epc        : {epc}\n"
        f"  edt        : {edt}"
    )

    return True