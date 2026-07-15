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


# ========================================
# LIGHT
# ========================================

def toggle_power(device):
    """照明の電源を切り替える"""
    return echonetManager.execute(
        device,
        "toggle_power"
    )


def color_up(device):
    """照明の色温度を暖色方向へ変更する"""
    return echonetManager.execute(
        device,
        "color_up"
    )


def color_down(device):
    """照明の色温度を寒色方向へ変更する"""
    return echonetManager.execute(
        device,
        "color_down"
    )


# ========================================
# AIRCON
# ========================================

def aircon_toggle_power(device):
    """エアコンの電源を切り替える"""
    return echonetManager.execute(
        device,
        "toggle_power"
    )


def aircon_temp_up(device):
    """エアコンの設定温度を上げる"""
    return echonetManager.execute(
        device,
        "temp_up"
    )


def aircon_temp_down(device):
    """エアコンの設定温度を下げる"""
    return echonetManager.execute(
        device,
        "temp_down"
    )


def aircon_cooling(device):
    """エアコンを冷房運転にする"""
    return echonetManager.execute(
        device,
        "cooling"
    )


def aircon_heating(device):
    """エアコンを暖房運転にする"""
    return echonetManager.execute(
        device,
        "heating"
    )


# ========================================
# BRAIND
# ========================================

def braind_toggle_upper(device):
    """ブラインド上部の開閉状態を切り替える"""
    return echonetManager.execute(
        device,
        "toggle_upper"
    )


def braind_stop(device):
    """ブラインドの動作を停止する"""
    return echonetManager.execute(
        device,
        "stop"
    )


def braind_angle_up(device):
    """ブラインドの角度を上げる"""
    return echonetManager.execute(
        device,
        "angle_up"
    )


def braind_angle_down(device):
    """ブラインドの角度を下げる"""
    return echonetManager.execute(
        device,
        "angle_down"
    )


# ========================================
# AIRPURI
# ========================================

def airpurifier_toggle_power(device):
    """空気清浄機の電源を切り替える"""
    return echonetManager.execute(
        device,
        "toggle_power"
    )


def airpurifier_temp_up(device):
    """空気清浄機の設定値を上げる"""
    return echonetManager.execute(
        device,
        "temp_up"
    )


def airpurifier_temp_down(device):
    """空気清浄機の設定値を下げる"""
    return echonetManager.execute(
        device,
        "temp_down"
    )


def airpurifier_cooling(device):
    """空気清浄機を冷房相当の動作にする"""
    return echonetManager.execute(
        device,
        "cooling"
    )


def airpurifier_heating(device):
    """空気清浄機を暖房相当の動作にする"""
    return echonetManager.execute(
        device,
        "heating"
    )


# CSVから実行を許可するアクション
_ACTIONS = {
    # LIGHT
    "toggle_power": toggle_power,
    "color_up": color_up,
    "color_down": color_down,

    # AIRCON
    "aircon_toggle_power": aircon_toggle_power,
    "aircon_temp_up": aircon_temp_up,
    "aircon_temp_down": aircon_temp_down,
    "aircon_cooling": aircon_cooling,
    "aircon_heating": aircon_heating,

    # BRAIND
    "braind_toggle_upper": braind_toggle_upper,
    "braind_stop": braind_stop,
    "braind_angle_up": braind_angle_up,
    "braind_angle_down": braind_angle_down,

    # AIRPURI
    "airpurifier_toggle_power": airpurifier_toggle_power,
    "airpurifier_temp_up": airpurifier_temp_up,
    "airpurifier_temp_down": airpurifier_temp_down,
    "airpurifier_cooling": airpurifier_cooling,
    "airpurifier_heating": airpurifier_heating,
}


def run(combo_result):
    if not _initialized:
        raise RuntimeError(
            "actionManagerが初期化されていません"
        )

    if combo_result is None:
        return None

    device = str(
        combo_result.get("device") or ""
    ).strip().upper()

    action = str(
        combo_result.get("action") or ""
    ).strip()

    if not device:
        p.error("操作対象のデバイスがありません")
        return False

    if not action:
        p.error("アクション名がありません")
        return False

    action_function = _ACTIONS.get(action)

    if action_function is None:
        p.error(
            f"未対応のアクションです: {action}"
        )
        return False

    p.info(
        f"家電操作を要求: {device} / {action}"
    )

    try:
        result = action_function(device)

    except Exception as error:
        p.error(
            f"{device}：{action}の実行中に"
            f"エラーが発生しました: {error}"
        )
        return False

    if result:
        p.success(
            f"{device}：{action}を実行しました"
        )
    else:
        p.error(
            f"{device}：{action}の実行に失敗しました"
        )

    return result