
#? Managers/actionManager.py
#? Norifumi Konndo

import Utils.logger as p

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
        "airpurifier_cooling": airpurifier_cooling,
        "airpurifier_heating": airpurifier_heating
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
    p.success("照明: 電源切替")
    return True


def color_up():
    p.success("照明: 色温度アップ")
    return True


def color_down():
    p.success("照明: 色温度ダウン")
    return True


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
    p.success("エアコン: 電源切替")
    return True


def aircon_temp_up():
    p.success("エアコン: 温度アップ")
    return True


def aircon_temp_down():
    p.success("エアコン: 温度ダウン")
    return True


def aircon_cooling():
    p.success("エアコン: 冷房")
    return True


def aircon_heating():
    p.success("エアコン: 暖房")
    return True


# ==========================================================
# ブラインド
# ==========================================================

def braind_toggle_upper():
    p.success("ブラインド: 開閉")
    return True


def braind_stop():
    p.success("ブラインド: 停止")
    return True


def braind_angle_up():
    p.success("ブラインド: 角度アップ")
    return True


def braind_angle_down():
    p.success("ブラインド: 角度ダウン")
    return True


# ==========================================================
# 空気清浄機
# ==========================================================

def airpurifier_toggle_power():
    p.success("空気清浄機: 電源切替")
    return True


def airpurifier_temp_up():
    p.success("空気清浄機: 強くする")
    return True


def airpurifier_temp_down():
    p.success("空気清浄機: 弱くする")
    return True


def airpurifier_cooling():
    p.success("空気清浄機: モード1")
    return True


def airpurifier_heating():
    p.success("空気清浄機: モード2")
    return True
