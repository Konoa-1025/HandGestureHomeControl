
#? Recognizers/pointingEstimator.py
#? Norifumi Konndo

import Utils.logger as p
import math
import csv
import json
from pathlib import Path

min_vector_length = 0.5
enabled = False
centers = {}
hold_seconds = 0.5
max_angle_degrees = 20.0
min_finger_length_ratio = 0.005
gap_tolerance_seconds = 0.15
centers_path = None

def Initialization(settings):
    global min_vector_length
    global enabled, centers, centers_path
    global hold_seconds, max_angle_degrees
    global min_finger_length_ratio, gap_tolerance_seconds

    p.info("pointingEstimatorを初期化中")

    min_vector_length = settings["recognition"]["direction_estimator"]["minimum_vector_length"]

    if min_vector_length is None:
        p.error("minimum_vector_lengthが正しくありません。")
        return False

    enabled = settings.get("pointing", {}).get("enabled", False)
    centers = {}
    if enabled:
        root = Path(__file__).resolve().parent.parent
        pointing_settings = settings.get("pointing", {})
        centers_path = root / pointing_settings.get("centers_path", "Data/homeAppliances/pointCenters.csv")
        trial_path = root / pointing_settings.get("settings_path", "Data/homeAppliances/pointingTrial.json")
        try:
            with trial_path.open(encoding="utf-8-sig") as file:
                trial_settings = json.load(file)
            hold_seconds = float(trial_settings["hold_seconds"])
            max_angle_degrees = float(trial_settings["max_angle_degrees"])
            min_finger_length_ratio = float(trial_settings.get("min_finger_length_ratio", 0.005))
            gap_tolerance_seconds = float(trial_settings.get("gap_tolerance_seconds", 0))
            values = (hold_seconds, max_angle_degrees, min_finger_length_ratio, gap_tolerance_seconds)
            if (not all(math.isfinite(value) for value in values)
                    or hold_seconds <= 0 or not 0 < max_angle_degrees < 90
                    or not 0 <= min_finger_length_ratio <= 1 or gap_tolerance_seconds < 0):
                raise ValueError("指差しの設定値が正しくありません")
            centers = load_centers(centers_path)
        except (OSError, ValueError, KeyError, TypeError, csv.Error) as error:
            p.error(f"指差し設定の読み込みに失敗しました: {error}")
            return False

    p.success("pointingEstimatorの初期化完了")
    return True

def abstract_direction(angle): #!使用するならこっちの方が安定してます。
    if -22.5 <= angle < 22.5:
        return "RIGHT"
    elif 22.5 <= angle < 67.5:
        return "UP_RIGHT"
    elif 67.5 <= angle < 112.5:
        return "UP"
    elif 112.5 <= angle < 157.5:
        return "UP_LEFT"
    elif angle >= 157.5 or angle < -157.5:
        return "LEFT"
    elif -157.5 <= angle < -112.5:
        return "DOWN_LEFT"
    elif -112.5 <= angle < -67.5:
        return "DOWN"
    else:
        return "DOWN_RIGHT"

def specific_direction(hand_landmark):#!具体的な角度で正確性に欠けてます。
    mcp = hand_landmark[5]
    tip = hand_landmark[8]
    
    dx = tip["x"] - mcp["x"]
    dy = tip["y"] - mcp["y"]
    
    length = math.hypot(dx, dy)
    
    if length < min_vector_length:
        return "UNKNOWN"
    
    # 画像ではyが下向きに増えるので、符号を反転
    angle = math.degrees(math.atan2(-dy, dx))
    return angle

def get_direction(hand_landmarks):
    hand_landmark = hand_landmarks["hands"][0]["landmarks"]

    angle = specific_direction(hand_landmark)

    if angle == "UNKNOWN":
        return {
            "angle": angle,
            "direction": "UNKNOWN"
        }

    direction = abstract_direction(angle)

    return {
        "angle": angle,
        "direction": direction
    }


def load_centers(csv_path):
    points = {}
    with open(csv_path, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames or []
        if (not {"device", "x_normalized", "y_normalized"}.issubset(columns)
                or len(columns) != len(set(columns))):
            raise ValueError("家電中心CSVのヘッダーが正しくありません")
        for row in reader:
            device = (row.get("device") or "").strip()
            if not device or device in points or None in row:
                raise ValueError(f"家電中心CSVの{reader.line_num}行目が正しくありません")
            try:
                point = (float(row["x_normalized"]), float(row["y_normalized"]))
            except (ValueError, TypeError) as error:
                raise ValueError("家電中心の座標が正しくありません") from error
            if not all(math.isfinite(value) and -1 <= value <= 2 for value in point):
                raise ValueError("家電中心は-1から2までの正規化座標で指定してください")
            points[device] = point
    return points


def save_centers():
    #?保存途中のCSVを読み込まないよう、一時ファイルから置き換える
    temporary_path = centers_path.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["device", "x_normalized", "y_normalized"])
        for device, (x, y) in centers.items():
            writer.writerow([device, f"{x:.6f}", f"{y:.6f}"])
    temporary_path.replace(centers_path)


def get_target(hand_landmarks, frame_shape, raw_gesture):
    height, width = frame_shape[:2]
    result = {
        "origin": None, "tip": None, "angles": {}, "candidate": None,
        "gesture": "NO HAND", "reason": "NO_HAND", "best_target": None,
        "best_angle": None, "finger_length_px": None,
        "min_finger_length_px": width * min_finger_length_ratio
    }
    hands = hand_landmarks.get("hands") or []
    if not hands or len(hands[0].get("landmarks", [])) < 21:
        return result

    landmarks = hands[0]["landmarks"]
    origin = (landmarks[5]["x"] * width, landmarks[5]["y"] * height)
    tip = (landmarks[8]["x"] * width, landmarks[8]["y"] * height)
    if not all(math.isfinite(value) for value in origin + tip):
        return result
    result.update(origin=origin, tip=tip, gesture=raw_gesture["name"])
    dx, dy = tip[0] - origin[0], tip[1] - origin[1]
    length = math.hypot(dx, dy)
    result["finger_length_px"] = length

    #?縦横比の影響を受けないよう、画像上の長さに戻して比較する
    if length > 0:
        for device, (x, y) in centers.items():
            target_x, target_y = x * width - origin[0], y * height - origin[1]
            distance = math.hypot(target_x, target_y)
            if distance < 1:
                continue
            cosine = (dx * target_x + dy * target_y) / (length * distance)
            result["angles"][device] = math.degrees(math.acos(max(-1, min(1, cosine))))
    if result["angles"]:
        nearest = min(result["angles"], key=result["angles"].get)
        result["best_target"] = nearest
        result["best_angle"] = result["angles"][nearest]

    if raw_gesture["name"] != "POINT":
        result["reason"] = "NOT_POINTING"
    elif length == 0 or length < result["min_finger_length_px"]:
        result["reason"] = "FINGER_TOO_SHORT"
    elif not result["angles"]:
        result["reason"] = "NO_TARGETS"
    elif result["best_angle"] > max_angle_degrees:
        result["reason"] = "OUT_OF_ANGLE"
    else:
        result["candidate"] = result["best_target"]
        result["reason"] = "TARGET_READY"
    return result
