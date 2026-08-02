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


def Initialization(settings):
    global el
    global devices
    global controller_eoj
    global esv
    global default_temperature
    global minimum_temperature
    global maximum_temperature
    global device_temperatures

    p.info("echonetManagerを初期化中")

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

    except FileNotFoundError:
        p.error(f"ECHONET Lite機器CSVが見つかりません: {csv_path}")
        return False

    except KeyError as error:
        p.error(f"ECHONET Liteの設定が不足しています: {error}")
        return False

    except Exception as error:
        p.error(f"echonetManagerの初期化に失敗しました: {error}")
        return False

    p.success(f"echonetManagerの初期化完了 ({len(devices)}件)")
    return True


def get_device(device):
    if device not in devices:
        p.error(f"ECHONET Lite機器が登録されていません: {device}")
        return None

    return devices[device]


def send(device, epc, pdcedt):
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
        f"EPC={epc} / PDCEDT={pdcedt}"
    )

    return True


def power_on(device):
    return send(
        device,
        "80",
        "0130"
    )


def power_off(device):
    return send(
        device,
        "80",
        "0131"
    )


def toggle_power(device):
    p.warning(
        f"{device}の現在の電源状態を取得できないため、"
        f"現在はON命令を送信します"
    )

    return power_on(device)


def set_temperature(device, temperature):
    if temperature < minimum_temperature:
        temperature = minimum_temperature

    if temperature > maximum_temperature:
        temperature = maximum_temperature

    temperature_hex = format(
        temperature,
        "02X"
    )

    pdcedt = f"01{temperature_hex}"

    result = send(
        device,
        "B3",
        pdcedt
    )

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


def aircon_cooling():
    return send(
        "AIRCON",
        "B0",
        "0142"
    )


def aircon_heating():
    return send(
        "AIRCON",
        "B0",
        "0141"
    )


def braind_toggle_upper():
    p.warning("ブラインド開閉用のEPC・EDTは未設定です")
    return False


def braind_stop():
    p.warning("ブラインド停止用のEPC・EDTは未設定です")
    return False


def braind_angle_up():
    p.warning("ブラインド角度アップ用のEPC・EDTは未設定です")
    return False


def braind_angle_down():
    p.warning("ブラインド角度ダウン用のEPC・EDTは未設定です")
    return False