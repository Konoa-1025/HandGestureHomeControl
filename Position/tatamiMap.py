"""反転後の画像座標で畳を保持する。画像の反転は行わない。"""
import csv
from pathlib import Path

import cv2
import numpy as np


class TatamiMap:
    def __init__(self, csv_path, image_size):
        self.image_size = np.asarray(image_size, dtype=float)
        if self.image_size.shape != (2,) or not np.all(np.isfinite(self.image_size)) or np.any(self.image_size <= 0):
            raise ValueError("image_sizeはCSV作成画像の[幅, 高さ]で指定してください")
        path = Path(csv_path).expanduser()
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent / path
        self.polygons = {}
        columns = [f"{corner}_{axis}" for corner in ("tl", "tr", "br", "bl") for axis in ("x", "y")]
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if not set(["tatami_id"] + columns).issubset(reader.fieldnames or []):
                raise ValueError("畳CSVのヘッダーが不正です")
            for row in reader:
                name = row["tatami_id"].strip()
                polygon = np.array([float(row[key]) for key in columns], dtype=np.float32).reshape(4, 2)
                if not name or name in self.polygons:
                    raise ValueError("畳IDが空欄または重複しています")
                if not np.all(np.isfinite(polygon)) or cv2.contourArea(polygon) <= 0:
                    raise ValueError(f"{name}の頂点が不正です")
                self.polygons[name] = polygon
        if not self.polygons:
            raise ValueError("畳CSVにデータがありません")

    def scaled_polygons(self, frame_shape):
        height, width = frame_shape[:2]
        scale = np.array([width, height]) / self.image_size
        return {name: (polygon * scale).astype(np.float32) for name, polygon in self.polygons.items()}

    def locate(self, box, frame_shape):
        areas = {name: overlap_area(polygon, box) for name, polygon in self.scaled_polygons(frame_shape).items()}
        best = max(areas, key=areas.get)
        return best if areas[best] > 0 else None


def overlap_area(polygon, box):
    """矩形の4辺でPolygonをクリップし、共通部分の面積を求める。"""
    points = [tuple(point) for point in polygon]
    x1, y1, x2, y2 = box
    for axis, boundary, sign in ((0, x1, 1), (0, x2, -1), (1, y1, 1), (1, y2, -1)):
        if not points:
            return 0.0
        clipped = []
        previous = points[-1]
        previous_inside = sign * (previous[axis] - boundary) >= 0
        for point in points:
            inside = sign * (point[axis] - boundary) >= 0
            if inside != previous_inside:
                ratio = (boundary - previous[axis]) / (point[axis] - previous[axis])
                clipped.append(tuple(previous[i] + ratio * (point[i] - previous[i]) for i in (0, 1)))
            if inside:
                clipped.append(point)
            previous, previous_inside = point, inside
        points = clipped
    return float(cv2.contourArea(np.asarray(points, dtype=np.float32))) if len(points) >= 3 else 0.0
