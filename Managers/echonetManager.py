
#? Managers/echonetManager.py
#? Norifumi Konndo

import csv
import os
import sys

import Utils.logger as p


sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

from EchonetLite import EchonetLite # type: ignore


el = None

devices = {}

controller_eoj = [[0x05, 0xff, 0x01]]
esv = "61"

default_temperature = 24
minimum_temperature = 16
maximum_temperature = 30

device_temperatures = {}
device_power_states = {}


def Initialization(settings):
    global el
    global devices
    global controller_eoj
    global esv
    global default_temperature
    global minimum_temperature
    global maximum_temperature
    global device_temperatures
    global device_power_states

    if el is not None:
        p.warning("echonetManagerは既に初期化されています")
        return True

    p.info("echonetManagerを初期化中")

    csv_path = None

    try:
        controller_eoj = settings["echonet"]["controller_eoj"]
        esv = settings["echonet"]["communication"]["esv"]
        default_temperature = settings["echonet"]["temperature"]["default"]
        minimum_temperature = settings["echonet"]["temperature"]["minimum"]
        maximum_temperature = settings["echonet"]["temperature"]["maximum"]
        csv_path = settings["echonet"]["device_map_csv"]

        devices = {}

        with open(csv_path, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            for row in reader:
                device = row.get("device", "").strip()

                if not device:
                    continue

                devices[device] = {
                    "display_name": row.get("display_name", device).strip(),
                    "ip": row.get("ip", "").strip(),
                    "eoj": row.get("eoj", "").strip()
                }

        device_temperatures = {}

        for device in devices:
            device_temperatures[device] = default_temperature

        el = EchonetLite(controller_eoj)
        el.begin(None, None, None)

        device_temperatures = {}
        device_power_states = {}

        for device in devices:
            device_temperatures[device] = default_temperature
            device_power_states[device] = False

    except FileNotFoundError:
        el = None
        p.error(f"ECHONET Lite機器CSVが見つかりません: {csv_path}")
        return False

    except KeyError as error:
        el = None
        p.error(f"ECHONET Liteの設定が不足しています: {error}")
        return False

    except Exception as error:
        el = None
        p.error(f"echonetManagerの初期化に失敗しました: {error}")
        return False

    p.success(f"echonetManagerの初期化完了 ({len(devices)}件)")
    return True


def get_device(device):
    if device not in devices:
        p.error(f"ECHONET Lite機器が登録されていません: {device}")
        return None

    return devices[device]


def create_pdcedt(edt):
    edt = edt.replace(" ", "").upper()

    if len(edt) == 0:
        p.error("EDTが空です")
        return None

    if len(edt) % 2 != 0:
        p.error(f"EDTの文字数が正しくありません: {edt}")
        return None

    try:
        bytes.fromhex(edt)

    except ValueError:
        p.error(f"EDTが16進数ではありません: {edt}")
        return None

    pdc = format(len(edt) // 2, "02X")

    return {
        "pdc": pdc,
        "edt": edt,
        "pdcedt": pdc + edt
    }


def send(device, epc, edt):
    if el is None:
        p.error("echonetManagerが初期化されていません")
        return False

    device_data = get_device(device)

    if device_data is None:
        return False

    target_ip = device_data["ip"]
    deoj = device_data["eoj"]
    display_name = device_data["display_name"]

    if not target_ip or target_ip == "N/A":
        p.error(f"{display_name}のIPアドレスが登録されていません")
        return False

    if not deoj or deoj == "N/A":
        p.error(f"{display_name}のEOJが登録されていません")
        return False

    property_data = create_pdcedt(edt)

    if property_data is None:
        return False

    pdc = property_data["pdc"]
    edt = property_data["edt"]
    pdcedt = property_data["pdcedt"]

    try:
        el.sendOPC1(
            target_ip,
            el.EOJ_Controller,
            deoj,
            esv,
            epc,
            pdcedt
        )

    except Exception as error:
        p.error(f"{display_name}へのECHONET Lite送信に失敗しました: {error}")
        return False

    p.success(
        f"ECHONET Lite送信: "
        f"{display_name} / IP={target_ip} / EOJ={deoj} / "
        f"ESV={esv} / EPC={epc} / PDC={pdc} / EDT={edt}"
    )

    return True


def power_on(device):
    return send(device, "80", "30")


def power_off(device):
    return send(device, "80", "31")

device_power_states = {
    "LIGHT": False,
    "AIRCON": False
}

def toggle_power(device):
    current_state = device_power_states.get(device, False)

    if current_state:
        result = power_off(device)
    else:
        result = power_on(device)

    if result:
        device_power_states[device] = not current_state

    return result


def set_temperature(device, temperature):
    if temperature < minimum_temperature:
        temperature = minimum_temperature

    if temperature > maximum_temperature:
        temperature = maximum_temperature

    edt = format(temperature, "02X")

    result = send(device, "B3", edt)

    if result:
        device_temperatures[device] = temperature

    return result


def temperature_up(device):
    current_temperature = device_temperatures.get(
        device,
        default_temperature
    )

    return set_temperature(
        device,
        current_temperature + 1
    )


def temperature_down(device):
    current_temperature = device_temperatures.get(
        device,
        default_temperature
    )

    return set_temperature(
        device,
        current_temperature - 1
    )


def aircon_toggle_power():
    return toggle_power("AIRCON")

def aircon_set_mode(mode):
    mode_edts = {
        "OTHER": "40",
        "AUTO": "41",
        "COOLING": "42",
        "HEATING": "43",
        "DEHUMIDIFICATION": "44",
        "FAN": "45"
    }

    if mode not in mode_edts:
        p.error(f"未対応のエアコン運転モードです: {mode}")
        return False

    return send("AIRCON", "B0", mode_edts[mode])

def aircon_auto():
    return aircon_set_mode("AUTO")


def aircon_cooling():
    return aircon_set_mode("COOLING")


def aircon_heating():
    return aircon_set_mode("HEATING")


def aircon_dehumidification():
    return aircon_set_mode("DEHUMIDIFICATION")


def aircon_fan():
    return aircon_set_mode("FAN")


def light_set_color(red, green, blue):
    if not 0 <= red <= 255:
        p.error("redは0から255の範囲で指定してください")
        return False

    if not 0 <= green <= 255:
        p.error("greenは0から255の範囲で指定してください")
        return False

    if not 0 <= blue <= 255:
        p.error("blueは0から255の範囲で指定してください")
        return False

    edt = f"{red:02X}{green:02X}{blue:02X}"

    return send("LIGHT", "C0", edt)


def braind_open():
    return send("BRAIND", "E0", "41")


def braind_close():
    return send("BRAIND", "E0", "42")


def braind_stop():
    return send("BRAIND", "E0", "43")


def braind_set_level(level):
    if not 0 <= level <= 100:
        p.error("ブラインド開閉レベルは0から100の範囲で指定してください")
        return False

    edt = format(level, "02X")

    return send("BRAIND", "E1", edt)


def braind_set_angle(angle):
    if not 0 <= angle <= 100:
        p.error("ブラインド角度は0から100の範囲で指定してください")
        return False

    edt = format(angle, "02X")

    return send("BRAIND", "E2", edt)


#======ブラインド操作のための関数======
braind_is_open = False

def braind_toggle_upper():
    global braind_is_open

    if braind_is_open:
        result = braind_close()
    else:
        result = braind_open()

    if result:
        braind_is_open = not braind_is_open

    return result


def braind_angle_up():
    return braind_set_angle(100)


def braind_angle_down():
    return braind_set_angle(0)

#==============================空気清浄機操作のための関数==============================
airpurifier_airflow_level = 1

def airpurifier_power_on():
    return power_on("AIRPURI")


def airpurifier_power_off():
    return power_off("AIRPURI")


def airpurifier_set_airflow(level):
    if not 1 <= level <= 8:
        p.error("空気清浄機の風量は1から8の範囲で指定してください")
        return False

    edt_value = 0x30 + level
    edt = format(edt_value, "02X")

    return send("AIRPURI", "A0", edt)


def airpurifier_auto():
    return send("AIRPURI", "A0", "41")

def airpurifier_airflow_up():
    global airpurifier_airflow_level

    next_level = airpurifier_airflow_level + 1

    if next_level > 8:
        next_level = 8

    result = airpurifier_set_airflow(next_level)

    if result:
        airpurifier_airflow_level = next_level

    return result


def airpurifier_airflow_down():
    global airpurifier_airflow_level

    next_level = airpurifier_airflow_level - 1

    if next_level < 1:
        next_level = 1

    result = airpurifier_set_airflow(next_level)

    if result:
        airpurifier_airflow_level = next_level

    return result

# ==========================================================
# 照明1
# ==========================================================

def light1_power_on():
    result = power_on("LIGHT1")

    if result:
        device_power_states["LIGHT1"] = True

    return result


def light1_power_off():
    result = power_off("LIGHT1")

    if result:
        device_power_states["LIGHT1"] = False

    return result


def light1_toggle_power():
    return toggle_power("LIGHT1")


# ==========================================================
# 照明2
# ==========================================================

def light2_power_on():
    result = power_on("LIGHT2")

    if result:
        device_power_states["LIGHT2"] = True

    return result


def light2_power_off():
    result = power_off("LIGHT2")

    if result:
        device_power_states["LIGHT2"] = False

    return result


def light2_toggle_power():
    return toggle_power("LIGHT2")


# ==========================================================
# 照明3
# ==========================================================

def light3_power_on():
    result = power_on("LIGHT3")

    if result:
        device_power_states["LIGHT3"] = True

    return result


def light3_power_off():
    result = power_off("LIGHT3")

    if result:
        device_power_states["LIGHT3"] = False

    return result


def light3_toggle_power():
    return toggle_power("LIGHT3")


# ==========================================================
# 照明4
# ==========================================================

def light4_power_on():
    result = power_on("LIGHT4")

    if result:
        device_power_states["LIGHT4"] = True

    return result


def light4_power_off():
    result = power_off("LIGHT4")

    if result:
        device_power_states["LIGHT4"] = False

    return result


def light4_toggle_power():
    return toggle_power("LIGHT4")

def all_lights_power_on():
    light_devices = ["LIGHT1", "LIGHT2", "LIGHT3", "LIGHT4"]
    all_success = True

    for device in light_devices:
        result = power_on(device)

        if result:
            device_power_states[device] = True
        else:
            all_success = False

    return all_success


def all_lights_power_off():
    light_devices = ["LIGHT1", "LIGHT2", "LIGHT3", "LIGHT4"]
    all_success = True

    for device in light_devices:
        result = power_off(device)

        if result:
            device_power_states[device] = False
        else:
            all_success = False

    return all_success

def all_lights_toggle_power():
    light_devices = ["LIGHT1", "LIGHT2", "LIGHT3", "LIGHT4"]

    all_lights_on = all(
        device_power_states.get(device, False)
        for device in light_devices
    )

    if all_lights_on:
        return all_lights_power_off()

    return all_lights_power_on()