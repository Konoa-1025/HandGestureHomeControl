
#? Managers/appliancesManager.py
#? Norifumi Konndo

import Utils.logger as p
import csv
from pathlib import Path

appliances = []
position_appliances = {}
use_position_map = False

def Initialization(settings):
    global appliances
    global position_appliances, use_position_map

    position_appliances = {}
    position_path = settings["home_appliances"]["files"].get("positionmap")
    use_position_map = bool(position_path) and not settings.get("pointing", {}).get("enabled", False)

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

    if use_position_map and not load_position_map(position_path):
        return False

    p.success(f"appliancesManagerの初期化完了 ({len(appliances)}件)")
    return True


def select_appliance_abstract(direction, current_position=None):
    if use_position_map:
        return position_appliances.get((current_position, direction))

    for appliance in appliances:
        if appliance["abstract"] == direction:
            return appliance

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


def get_appliance(device):
    for appliance in appliances:
        if appliance["device"] == device:
            return appliance
    return None


def load_position_map(csv_path):
    global position_appliances
    path = Path(__file__).resolve().parent.parent / csv_path
    directions = ("UP_LEFT", "UP", "UP_RIGHT", "LEFT", "RIGHT", "DOWN_LEFT", "DOWN", "DOWN_RIGHT")
    mapping = {}
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if not {"tatami_id", "direction", "device"}.issubset(reader.fieldnames or []):
                raise ValueError("畳別家電CSVのヘッダーが正しくありません")
            for row in reader:
                device = (row.get("device") or "").strip()
                if not device:
                    continue
                position = (row.get("tatami_id") or "").strip()
                direction = (row.get("direction") or "").strip()
                appliance = get_appliance(device)
                if not position or direction not in directions or appliance is None:
                    raise ValueError(f"{reader.line_num}行目の畳・方向・家電が正しくありません")
                if (position, direction) in mapping:
                    raise ValueError(f"{position}の{direction}が重複しています")
                mapping[(position, direction)] = appliance
    except (OSError, ValueError, csv.Error) as error:
        p.error(f"畳別家電CSVの読み込みに失敗しました: {error}")
        return False
    position_appliances = mapping
    return True
