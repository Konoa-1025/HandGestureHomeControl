
#? Managers/actionManager.py
#? Norifumi Konndo

import Utils.logger as p
import Managers.echonetManager as echonet

action_functions = {}
light_colors = [
    (255, 255, 255), # 白
    (255, 0, 0),     # 赤
    (0, 255, 0),     # 緑
    (0, 0, 255)      # 青
]

light_color_index = 0


def Initialization(settings):
    global action_functions

    p.info("actionManagerを初期化中")

    action_functions = {
        "toggle_power": toggle_power,
        "color_up": color_up,
        "color_down": color_down,

        "TEST": TEST,

        "aircon_toggle_power": aircon_toggle_power,
        "aircon_auto": aircon_auto,
        "aircon_cooling": aircon_cooling,
        "aircon_heating": aircon_heating,
        "aircon_dehumidification": aircon_dehumidification,
        "aircon_fan": aircon_fan,

        "braind_toggle_upper": braind_toggle_upper,
        "braind_stop": braind_stop,
        "braind_angle_up": braind_angle_up,
        "braind_angle_down": braind_angle_down,

        "airpurifier_toggle_power": airpurifier_toggle_power,
        "airpurifier_airflow_up": airpurifier_airflow_up,
        "airpurifier_airflow_down": airpurifier_airflow_down,
        "airpurifier_auto": airpurifier_auto,
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
    global light_color_index

    light_color_index += 1

    if light_color_index >= len(light_colors):
        light_color_index = 0

    red, green, blue = light_colors[light_color_index]

    return echonet.light_set_color(
        red,
        green,
        blue
    )


def color_down():
    global light_color_index

    light_color_index -= 1

    if light_color_index < 0:
        light_color_index = len(light_colors) - 1

    red, green, blue = light_colors[light_color_index]

    return echonet.light_set_color(
        red,
        green,
        blue
    )


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
    return echonet.aircon_toggle_power()


def aircon_auto():
    return echonet.aircon_auto()


def aircon_cooling():
    return echonet.aircon_cooling()


def aircon_heating():
    return echonet.aircon_heating()


def aircon_dehumidification():
    return echonet.aircon_dehumidification()


def aircon_fan():
    return echonet.aircon_fan()

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


def airpurifier_airflow_up():
    return echonet.airpurifier_airflow_up()


def airpurifier_airflow_down():
    return echonet.airpurifier_airflow_down()


def airpurifier_auto():
    return echonet.airpurifier_auto()
