import argparse
import csv
import math
import json
import time
from pathlib import Path

import cv2
import numpy as np

from Utils.configLoader import load_setting_config
from Managers import cameraManager as camera
from Cascades import highCascade as cascade
from Models.mediapipe import highModel as model
from Recognizers import gestureRecognizer as gesture
from Recognizers.pointingTrial import PointingTrial
from Recognizers.devicePointing import load_centers, compare_direction
from Feedback.pointingPreview import preview_geometry, click_to_center, draw_preview

ROOT = Path(__file__).resolve().parent
CENTERS = ROOT / 'Data/homeAppliances/pointCenters.csv'
WINDOW = 'HGHC Pointing Experiment (preview only)'
TRIAL_CONFIG = ROOT / 'Data/homeAppliances/pointingTrial.json'
IMAGE_X, IMAGE_Y = 140, 230



def save_centers(centers):
    temporary = CENTERS.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['device', 'x_normalized', 'y_normalized'])
        for device, (x, y) in centers.items():
            writer.writerow([device, f'{x:.6f}', f'{y:.6f}'])
    temporary.replace(CENTERS)



def initialize(config):
    for module in (camera, cascade, model, gesture):
        if not module.Initialization(config):
            raise RuntimeError(f'{module.__name__}の初期化に失敗しました')
    if not camera.start_camera() or camera.get_capture('front') is None:
        raise RuntimeError('front入力を開けませんでした')


def main():
    parser = argparse.ArgumentParser(description='手の方向・画面外家電・全灯OFFの表示専用試作')
    parser.add_argument('--start-frame', type=int, default=0, help='録画動画の開始フレーム')
    parser.add_argument('--frames', type=int, default=0, help='確認するフレーム数。0なら終了まで')
    parser.add_argument('--snapshot', type=Path, help='最後の表示画像の保存先')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--paused', action='store_true', help='最初のフレームで一時停止')
    args = parser.parse_args()
    if args.headless and (args.frames <= 0 or args.paused):
        parser.error('--headlessでは--framesに正の数を指定し、--pausedは外してください')
    config = load_setting_config()
    centers = load_centers(CENTERS)
    trial_settings = json.loads(TRIAL_CONFIG.read_text())
    trial = PointingTrial(trial_settings['hold_seconds'])
    timestamp = 0.0
    with (ROOT / config['home_appliances']['files']['appliancesmap']).open(encoding='utf-8-sig') as file:
        devices = [r['device'] for r in csv.DictReader(file) if r.get('display_name')]
    devices = list(dict.fromkeys(['AIRCON','LIGHT','AIRPURI','BRAIND'] + devices))
    selected = 0
    paused = args.paused
    next_frame = True
    rgb = display = None
    hand_data = {'hands': []}
    count = 0
    dirty = False

    def on_click(event, x, y, flags, param):
        nonlocal dirty
        if event == cv2.EVENT_LBUTTONDOWN and display is not None:
            point = click_to_center(x, y, rgb.shape)
            if point is not None:
                centers[devices[selected]] = point
                dirty = True
                trial.reset()

    try:
        initialize(config)
        source = camera.source_settings.get('front', {})
        if args.start_frame and source.get('type') == 'movie':
            camera.get_capture('front').set(cv2.CAP_PROP_POS_FRAMES, args.start_frame)
        if not args.headless:
            cv2.namedWindow(WINDOW, cv2.WINDOW_AUTOSIZE)
            cv2.setMouseCallback(WINDOW, on_click)
        while True:
            if not paused or next_frame:
                raw = camera.read_frame('front')
                if raw is None:
                    break
                rgb = cascade.run(raw)
                hand_data = model.run(rgb)
                capture = camera.get_capture('front')
                timestamp = capture.get(cv2.CAP_PROP_POS_FRAMES) / max(capture.get(cv2.CAP_PROP_FPS), 1) if source.get('type') == 'movie' else time.monotonic()
                count += 1
                next_frame = False
                result = compare_direction(hand_data, rgb.shape, centers, trial_settings['max_angle_degrees'], trial_settings.get('min_finger_length_ratio', 0.005))
                event = trial.update(result, timestamp)
                if event:
                    print(f'SIMULATION {timestamp:.2f}s: {event} (no transmission)', flush=True)
            result = compare_direction(hand_data, rgb.shape, centers, trial_settings['max_angle_degrees'], trial_settings.get('min_finger_length_ratio', 0.005))
            display = draw_preview(rgb, centers, result, devices[selected], paused, trial, dirty)
            if not args.headless:
                cv2.imshow(WINDOW, display)
            if args.frames and count >= args.frames:
                break
            if args.headless:
                continue
            key = cv2.waitKey(20) & 0xFF
            if key in (ord('q'), 27) or cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                break
            if key == ord(' '):
                paused = not paused
            elif key == ord('n'):
                paused, next_frame = True, True
            elif key in (ord('['), ord(']')):
                selected = (selected + (1 if key == ord(']') else -1)) % len(devices)
            elif key == ord('x'):
                centers.pop(devices[selected], None)
                dirty = True
                trial.reset()
            elif key == ord('s'):
                save_centers(centers)
                dirty = False
                print('中心点を保存しました', flush=True)
        if args.snapshot and display is not None:
            if not cv2.imwrite(str(args.snapshot), display):
                raise RuntimeError('画像を保存できませんでした')
        print(f'確認フレーム数: {count}; 候補: {result["candidate"] if count else None}')
        if dirty:
            print('未保存の中心点は破棄しました。保存するときはSを押してください。')
    finally:
        camera.stop_camera()
        if model.hands_model is not None:
            model.hands_model.close()
            model.hands_model = None
            model.initialized = False
        if not args.headless:
            cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
