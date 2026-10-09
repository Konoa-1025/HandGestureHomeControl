#? Managers/positionManager.py
#? 役割：人物の足元と畳の重なりから現在位置を取得

import csv
from pathlib import Path

import cv2
import numpy as np
import Utils.logger as p

pose_model = None
polygons = {}
bottom_ratio = 0.3
debug = False
current_position = None
bounding_box = None
position_box = None


def Initialization(config):
    global pose_model, bottom_ratio, debug, polygons
    close()
    polygons = {}
    settings = config.get("position", {})
    debug = settings.get("debug", False)
    if not settings.get("enabled", False):
        return True
    try:
        bottom_ratio = float(settings.get("bottom_ratio", 0.3))
        if not 0 < bottom_ratio <= 1:
            raise ValueError("bottom_ratioは0より大きく1以下にしてください")
        load_floor(settings)
        import mediapipe as mp
        pose_model = mp.solutions.pose.Pose(
            model_complexity=1, smooth_landmarks=False,
            min_detection_confidence=0.5, min_tracking_confidence=0.5
        )
        p.success("positionManagerの初期化完了")
    except Exception as error:
        close()
        p.warning(f"人物位置を取得できません。手の認識を続けます: {error}")
    return True


def load_floor(settings):
    global polygons
    image_size = np.asarray(settings["image_size"], dtype=float)
    if image_size.shape != (2,) or not np.all(np.isfinite(image_size)) or np.any(image_size <= 0):
        raise ValueError("image_sizeは画像の幅と高さで指定してください")
    rect = np.asarray(settings.get("image_rect", [0, 0, *image_size]), dtype=float)
    if (rect.shape != (4,) or not np.all(np.isfinite(rect))
            or np.any(rect[:2] < 0) or np.any(rect[2:] <= 0)
            or np.any(rect[:2] + rect[2:] > image_size)):
        raise ValueError("image_rectは画像内の左・上・幅・高さで指定してください")
    columns = [corner + "_" + axis for corner in ("tl", "tr", "br", "bl") for axis in ("x", "y")]
    path = Path(__file__).resolve().parent.parent / settings["csv_path"]
    loaded = {}
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not set(["tatami_id"] + columns).issubset(reader.fieldnames or []):
            raise ValueError("畳CSVのヘッダーが正しくありません")
        for row in reader:
            name = row["tatami_id"].strip()
            points = np.array([float(row[key]) for key in columns], dtype=np.float32).reshape(4, 2)
            if not name or name in loaded or not np.all(np.isfinite(points)) or cv2.contourArea(points) <= 0:
                raise ValueError(f"畳CSVの{reader.line_num}行目が正しくありません")
            #?CSVは反転後の映像。スクリーンショットの余白だけを取り除く
            loaded[name] = ((points - rect[:2]) / rect[2:]).astype(np.float32)
    if not loaded:
        raise ValueError("畳CSVが空です")
    polygons = loaded


def scaled_polygons(frame_shape):
    height, width = frame_shape[:2]
    return {name: (points * [width, height]).astype(np.float32) for name, points in polygons.items()}


def overlap_area(polygon, box):
    #?足元の矩形の各辺で畳を切り取り、残った面積を比較する
    points = list(polygon)
    for axis, edge, sign in ((0, box[0], 1), (0, box[2], -1), (1, box[1], 1), (1, box[3], -1)):
        if not points:
            return 0.0
        clipped = []
        before = points[-1]
        for point in points:
            inside = sign * (point[axis] - edge) >= 0
            before_inside = sign * (before[axis] - edge) >= 0
            if inside != before_inside:
                ratio = (edge - before[axis]) / (point[axis] - before[axis])
                clipped.append(before + ratio * (point - before))
            if inside:
                clipped.append(point)
            before = point
        points = clipped
    if len(points) < 3:
        return 0.0
    return float(cv2.contourArea(np.asarray(points, dtype=np.float32)))


def locate(box, frame_shape):
    areas = {name: overlap_area(points, box) for name, points in scaled_polygons(frame_shape).items()}
    if not areas:
        return None
    position = max(areas, key=areas.get)
    return position if areas[position] > 0 else None


def position_process(frame):
    global current_position, bounding_box, position_box
    current_position = bounding_box = position_box = None
    if pose_model is None or frame is None:
        return None
    try:
        result = pose_model.process(frame)
        if result.pose_landmarks is None:
            return None
        landmarks = result.pose_landmarks.landmark
        if (not any(landmarks[index].visibility >= 0.5 for index in (27, 28, 29, 30, 31, 32))
                or not any(landmarks[index].visibility >= 0.5 for index in (11, 12))):
            return None
        points = np.array([(point.x, point.y) for point in landmarks if point.visibility >= 0.5])
        if len(points) < 4 or not np.all(np.isfinite(points)):
            return None
        height, width = frame.shape[:2]
        points *= [width, height]
        left, top = points.min(axis=0)
        right, bottom = points.max(axis=0)
        pad_x, pad_y = (right - left) * 0.05, (bottom - top) * 0.05
        left, right = np.clip([left - pad_x, right + pad_x], 0, width)
        top, bottom = np.clip([top - pad_y, bottom], 0, height)
        if right <= left or bottom <= top:
            return None
        bounding_box = (left, top, right, bottom)
        position_box = (left, bottom - (bottom - top) * bottom_ratio, right, bottom)
        current_position = locate(position_box, frame.shape)
        return current_position
    except Exception as error:
        p.warning(f"人物位置の取得を停止しました: {error}")
        close()
        return None


def close():
    global pose_model, current_position, bounding_box, position_box
    if pose_model is not None:
        pose_model.close()
        pose_model = None
    current_position = bounding_box = position_box = None
