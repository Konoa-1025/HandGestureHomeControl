
#? Managers/appliancesManager.py
#? Norifumi Konndo

import Utils.logger as p
import csv
from pathlib import Path

appliances = []
position_appliances = {}
use_position_map = False

def Initialization(settings):
    global appliances, position_appliances, use_position_map

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


def load_position_map(csv_path):
    global position_appliances
    directions = {"UP_LEFT", "UP", "UP_RIGHT", "LEFT", "RIGHT", "DOWN_LEFT", "DOWN", "DOWN_RIGHT"}
    devices = {appliance["device"]: appliance for appliance in appliances}
    path = Path(csv_path).expanduser()
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    mapping = {}
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if not {"tatami_id", "direction", "device"}.issubset(reader.fieldnames or []):
                raise ValueError("畳別家電CSVのヘッダーが不正です")
            for row in reader:
                tatami_id = (row["tatami_id"] or "").strip()
                direction = (row["direction"] or "").strip()
                device = (row["device"] or "").strip()
                if not device:
                    continue  # 家電欄が空欄なら未登録
                if not tatami_id or direction not in directions or device not in devices:
                    raise ValueError(f"{reader.line_num}行目の畳・方向・家電IDが不正です")
                key = (tatami_id, direction)
                if key in mapping:
                    raise ValueError(f"{tatami_id}の{direction}が重複しています")
                mapping[key] = devices[device]
    except (OSError, ValueError, csv.Error) as error:
        p.error(f"畳別家電CSVの読み込みに失敗しました: {error}")
        return False
    position_appliances = mapping
    p.success(f"畳別家電の読み込み完了 ({len(mapping)}件)")
    return True


def select_appliance_abstract(direction, current_position=None):
    if use_position_map:
        # 位置不明・未登録なら選択しない。以前の固定対応には戻さない。
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
    return next((item for item in appliances if item["device"] == device), None)
