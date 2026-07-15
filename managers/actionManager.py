# actionManager.py
# Norifumi Konndo

import utils.logPrint as p
import managers.echonetManager as echonetManager


_initialized = False


def Initialization(settings):
    global _initialized

    p.info("actionManagerを初期化中")

    _initialized = True

    p.success("actionManagerの初期化成功")
    return True


def run(combo_result):
    if not _initialized:
        raise RuntimeError("actionManagerが初期化されていません")

    if combo_result is None:
        return None

    device = str(combo_result.get("device") or "").strip()
    action = str(combo_result.get("action") or "").strip()

    if not device:
        p.error("操作対象のデバイスがありません")
        return False

    if not action:
        p.error("アクション名がありません")
        return False

    p.info(f"家電操作を要求: {device} / {action}")

    result = echonetManager.execute(device, action)

    if result:
        p.success(f"{device}：{action}を実行しました")
    else:
        p.error(f"{device}：{action}の実行に失敗しました")

    return result