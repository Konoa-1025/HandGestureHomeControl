
#? Managers/appliancesManager.py
#? Norifumi Konndo

import Utils.logger as p
import csv

appliances = []

def Initialization(settings):
    global appliances

    p.info("appliancesManagerを初期化中")

    csv_path = settings["home_appliances"]["files"]["appliancesmap"]

    try:
        with open(csv_path, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            appliances = []

            for row in reader:
                if not row["device"]:
                    continue

                appliances.append(row)

    except Exception as error:
        p.error(f"CSVの読み込みに失敗しました: {error}")
        return False

    p.success(f"appliancesManagerの初期化完了 ({len(appliances)}件)")
    return True


def select_appliance_abstract(direction):

    for appliance in appliances:
        if appliance["abstract"] == direction:
            return appliance["device"]

    return None


def select_appliance_concrete(x, y, depth=None):

    for appliance in appliances:

        if (
            appliance["x_min"] == ""
            or appliance["x_max"] == ""
            or appliance["y_min"] == ""
            or appliance["y_max"] == ""
        ):
            continue

        if not (
            float(appliance["x_min"]) <= x <= float(appliance["x_max"])
            and float(appliance["y_min"]) <= y <= float(appliance["y_max"])
        ):
            continue

        if (
            depth is not None
            and appliance["depth"] != ""
            and appliance["depth"] != depth
        ):
            continue

        return appliance

    return None