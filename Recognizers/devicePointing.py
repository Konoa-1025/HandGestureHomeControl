import csv
import math
from pathlib import Path
import numpy as np
from Recognizers import gestureRecognizer as gesture

def load_centers(path):
    centers = {}
    with Path(path).open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames or []
        required = {'device', 'x_normalized', 'y_normalized'}
        if not required.issubset(columns) or len(columns) != len(set(columns)):
            raise ValueError('中心点CSVにはdevice,x_normalized,y_normalized列が必要です')
        for row in reader:
            device = (row.get('device') or '').strip()
            if not device or None in row:
                raise ValueError(f'中心点CSVの{reader.line_num}行目が不正です')
            if device in centers:
                raise ValueError(f'中心点CSVで家電IDが重複しています: {device}')
            try:
                point = (float(row['x_normalized']), float(row['y_normalized']))
            except (TypeError, ValueError) as error:
                raise ValueError(f'中心点CSVの{reader.line_num}行目の座標が不正です') from error
            if not all(math.isfinite(v) and -1 <= v <= 2 for v in point):
                raise ValueError('中心点は-1〜2の正規化座標で指定してください')
            centers[device] = point
    return centers


def compare_direction(hand_data, frame_shape, centers, max_angle=20, min_finger_length_ratio=0.005):
    height, width = frame_shape[:2]
    result = {
        'origin': None, 'tip': None, 'angles': {}, 'candidate': None,
        'gesture': 'NO HAND', 'reason': 'NO_HAND', 'best_target': None,
        'best_angle': None, 'finger_length_px': None,
        'min_finger_length_px': width * min_finger_length_ratio,
    }
    hands = hand_data.get('hands') or []
    if not hands or len(hands[0].get('landmarks', [])) < 21:
        return result
    landmarks = hands[0]['landmarks']
    origin = np.array([landmarks[5]['x'] * width, landmarks[5]['y'] * height])
    tip = np.array([landmarks[8]['x'] * width, landmarks[8]['y'] * height])
    if not np.all(np.isfinite([origin, tip])):
        return result
    result.update(origin=origin, tip=tip, gesture=gesture.run(hands)['name'])
    vector = tip - origin
    length = float(np.linalg.norm(vector))
    result['finger_length_px'] = length
    if length > 0:
        for device, center in centers.items():
            target = np.array(center) * [width, height] - origin
            distance = np.linalg.norm(target)
            if distance < 1:
                continue
            cosine = float(np.dot(vector, target) / (length * distance))
            result['angles'][device] = math.degrees(math.acos(np.clip(cosine, -1, 1)))
    if result['angles']:
        nearest = min(result['angles'], key=result['angles'].get)
        result.update(best_target=nearest, best_angle=result['angles'][nearest])
    if result['gesture'] != 'POINT':
        result['reason'] = 'NOT_POINTING'
    elif length <= 0 or length < result['min_finger_length_px']:
        result['reason'] = 'FINGER_TOO_SHORT'
    elif not result['angles']:
        result['reason'] = 'NO_TARGETS'
    elif result['best_angle'] > max_angle:
        result['reason'] = 'OUT_OF_ANGLE'
    else:
        result.update(candidate=result['best_target'], reason='TARGET_READY')
    return result

