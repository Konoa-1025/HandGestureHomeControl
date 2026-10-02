"""既存MediaPipeで1人分の全身ランドマークを囲む概算BBoxを取得。"""
import numpy as np


class PersonDetector:
    def __init__(self):
        import mediapipe as mp
        # complexity=1は既存MediaPipeに同梱されたモデルを使う。
        self.pose = mp.solutions.pose.Pose(
            model_complexity=1, smooth_landmarks=False,
            min_detection_confidence=0.5, min_tracking_confidence=0.5,
        )

    def detect(self, frame):
        # HGHCのCascade出力はすでにRGB・反転済み。
        result = self.pose.process(frame)
        if not result.pose_landmarks:
            return None
        landmarks = result.pose_landmarks.landmark
        # 足が見えないと床接触位置を推定できない。
        if not any(landmarks[i].visibility >= 0.5 for i in (27, 28, 29, 30, 31, 32)):
            return None
        if not any(landmarks[i].visibility >= 0.5 for i in (11, 12)):
            return None
        points = np.array([(p.x, p.y) for p in landmarks if p.visibility >= 0.5])
        if len(points) < 4 or not np.all(np.isfinite(points)):
            return None
        height, width = frame.shape[:2]
        points *= (width, height)
        x1, y1 = points.min(axis=0)
        x2, y2 = points.max(axis=0)
        # ランドマークは体の内側なので、頭頂・体の幅を少し補う。
        pad_x, pad_y = (x2 - x1) * 0.05, (y2 - y1) * 0.05
        return (max(0, x1 - pad_x), max(0, y1 - pad_y),
                min(width, x2 + pad_x), min(height, y2))

    def close(self):
        self.pose.close()
