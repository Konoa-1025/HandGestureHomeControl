import csv
import math
from pathlib import Path
import numpy as np
from Recognizers import gestureRecognizer as gesture

def load_centers(path):
    centers = {}
    with Path(path).open(encoding='utf-8-sig', newline='') as file:
        for row in csv.DictReader(file):
            point = (float(row['x_normalized']), float(row['y_normalized']))
            if not all(math.isfinite(v) and -1 <= v <= 2 for v in point):
                raise ValueError('中心点は-1〜2の正規化座標で指定してください')
            centers[row['device']] = point
    return centers


def compare_direction(hand_data, frame_shape, centers, max_angle=20, min_finger_length_ratio=0.005):
    result = {'origin': None, 'tip': None, 'angles': {}, 'candidate': None, 'gesture': 'NO HAND'}
    hands = hand_data.get('hands', [])
    if not hands or len(hands[0].get('landmarks', [])) < 21:
        return result
    landmarks = hands[0]['landmarks']
    height, width = frame_shape[:2]
    origin = np.array([landmarks[5]['x'] * width, landmarks[5]['y'] * height])
    tip = np.array([landmarks[8]['x'] * width, landmarks[8]['y'] * height])
    if not np.all(np.isfinite([origin, tip])):
        return result
    result.update(origin=origin, tip=tip, gesture=gesture.run(hands)['name'])
    vector = tip - origin
    length = np.linalg.norm(vector)
    if length <= 0 or length < width * min_finger_length_ratio:
        return result
    for device, center in centers.items():
        target = np.array(center) * [width, height] - origin
        distance = np.linalg.norm(target)
        if distance < 1:
            continue
        cosine = float(np.dot(vector, target) / (length * distance))
        result['angles'][device] = math.degrees(math.acos(np.clip(cosine, -1, 1)))
    if result['angles'] and result['gesture'] == 'POINT':
        nearest = min(result['angles'], key=result['angles'].get)
        if result['angles'][nearest] <= max_angle:
            result['candidate'] = nearest
    return result


