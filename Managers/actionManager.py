
#? Managers/actionManager.py
#? Norifumi Konndo

import Utils.logger as p
import Managers.echonetManager as echonet

action_functions = {}


def Initialization(settings):
    global action_functions

    p.info("actionManagerを初期化中")

    action_functions = {
        "toggle_power": toggle_power,
        "color_up": color_up,
        "color_down": color_down,

        "TEST": TEST,

        "aircon_toggle_power": aircon_toggle_power,
        "aircon_temp_up": aircon_temp_up,
        "aircon_temp_down": aircon_temp_down,
        "aircon_cooling": aircon_cooling,
        "aircon_heating": aircon_heating,

        "braind_toggle_upper": braind_toggle_upper,
        "braind_stop": braind_stop,
        "braind_angle_up": braind_angle_up,
        "braind_angle_down": braind_angle_down,

        "airpurifier_toggle_power": airpurifier_toggle_power,
        "airpurifier_temp_up": airpurifier_temp_up,
        "airpurifier_temp_down": airpurifier_temp_down,
    }


    p.success("actionManagerの初期化完了")
    return True


def action_process(action_name):

    if action_name not in action_functions:
        p.error(f"未登録のアクションです: {action_name}")
        return False

    try:
        return action_functions[action_name]()

    except Exception as error:
        p.error(f"アクション実行中にエラーが発生しました: {error}")
        return False


# ==========================================================
# 照明
# ==========================================================

def toggle_power():
    return echonet.toggle_power("LIGHT")


def color_up():
    p.warning("照明の色温度アップ用EPC・EDTは未設定です")
    return False


def color_down():
    p.warning("照明の色温度ダウン用EPC・EDTは未設定です")
    return False


# ==========================================================
# テスト
# ==========================================================

def TEST():
    p.success("TEST")
    return True


# ==========================================================
# エアコン
# ==========================================================

def aircon_toggle_power():
    return echonet.toggle_power("AIRCON")


def aircon_temp_up():
    return echonet.temperature_up("AIRCON")


def aircon_temp_down():
    return echonet.temperature_down("AIRCON")


def aircon_cooling():
    return echonet.aircon_cooling()


def aircon_heating():
    return echonet.aircon_heating()


# ==========================================================
# ブラインド
# ==========================================================

def braind_toggle_upper():
    return echonet.braind_toggle_upper()


def braind_stop():
    return echonet.braind_stop()


def braind_angle_up():
    return echonet.braind_angle_up()


def braind_angle_down():
    return echonet.braind_angle_down()



# ==========================================================
# 空気清浄機
# ==========================================================

def airpurifier_toggle_power():
    return echonet.toggle_power("AIRPURI")


def airpurifier_temp_up():
    return echonet.temperature_up("AIRPURI")


def airpurifier_temp_down():
    return echonet.temperature_down("AIRPURI")
