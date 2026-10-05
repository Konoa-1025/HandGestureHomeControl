import argparse
import copy
import time
from pathlib import Path

import cv2

import Utils.logger as p
import Utils.configLoader as figload
import Core.initializer as initializer
from Core.application import Application
import Managers.cameraManager as camera
import Managers.systemManager as system
import Managers.cascadeManager as cascade
import Managers.modelManager as model
import Managers.previewManager as preview
import Managers.positionManager as human_position
import Managers.pointingManager as pointing
import Managers.comboManager as combo
import Managers.echonetManager as echonet


def make_options(argv=None):
    parser = argparse.ArgumentParser(description='HGHC camera/video recognition and status preview')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', dest='dry_run', action='store_true')
    mode.add_argument('--live', dest='dry_run', action='store_false')
    parser.set_defaults(dry_run=None)
    parser.add_argument('--video', type=Path)
    parser.add_argument('--start-frame', type=int, default=0)
    parser.add_argument('--frames', type=int, default=0)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--snapshot', type=Path)
    args = parser.parse_args(argv)
    if args.frames < 0 or args.start_frame < 0 or (args.headless and args.frames == 0):
        parser.error('headlessには--framesの正の値が必要です。フレーム番号は0以上にしてください。')
    return args


def main(options=None):
    options = options or make_options([])
    config = copy.deepcopy(figload.load_setting_config())
    if options.video is not None:
        config['camera']['sources'] = [{'id':'front','type':'movie','movie':True,'enabled':True,'loop':True,'connection':{'path':str(options.video)}}]
    front = next((source for source in config['camera']['sources'] if source.get('id') == 'front' and source.get('enabled', True)), {})
    movie = front.get('type', '').lower() == 'movie'
    dry_run = movie if options.dry_run is None else options.dry_run
    config['runtime'] = {'dry_run': dry_run, 'headless': options.headless}
    application = Application(dry_run)
    frame_count = 0
    paused = False
    advance = False
    cased_frame = None
    status = {}
    last_clock = time.monotonic()
    fps = 0.0
    last_is_hand = False
    try:
        if not initializer.Managers_initialize(config):
            return False
        if not camera.start_camera() or camera.get_capture('front') is None:
            p.error('front入力を開けませんでした')
            return False
        if options.start_frame and movie:
            camera.get_capture('front').set(cv2.CAP_PROP_POS_FRAMES, options.start_frame)
        p.info('SIMULATION: 実機送信なし' if dry_run else 'LIVE: 実機制御あり')
        while True:
            if not paused or advance or cased_frame is None:
                front_frame = camera.read_frame('front')
                if front_frame is None:
                    if movie or camera.is_finished('front'):
                        break
                    p.error('カメラ映像を取得できません。入力を確認してください')
                    return False
                cascade_result = cascade.cascade_process(front_frame, system.get_mem())
                if cascade_result is None:
                    return False
                cased_frame = cascade_result['cased_frame']
                current_position = None
                if not pointing.enabled:
                    current_position = human_position.update(cased_frame)
                run_model = pointing.enabled or cascade_result['is_motion'] or last_is_hand
                hands = model.model_process(cased_frame, system.get_cpu(), 0) if run_model else {'is_hand': False, 'hands': []}
                last_is_hand = hands['is_hand']
                timestamp = camera.get_timestamp('front')
                status = application.update(hands, cased_frame.shape, timestamp, current_position)
                now = time.monotonic()
                instantaneous = 1 / max(now - last_clock, .001)
                fps = instantaneous if frame_count == 0 else fps * .8 + instantaneous * .2
                last_clock = now
                frame_count += 1
                advance = False
                status.update(input='VIDEO' if movie else 'CAMERA', frame_index=int(camera.get_capture('front').get(cv2.CAP_PROP_POS_FRAMES)) if movie else frame_count, fps=fps)
            status['paused'] = paused
            if not options.headless:
                if pointing.enabled:
                    if not preview.show_frame_pointing(cased_frame, pointing, status):
                        break
                elif not preview.show_frame_detail(cased_frame, human_position.get_debug_state(), current_position):
                    break
            if options.frames and frame_count >= options.frames:
                break
            if not options.headless and movie and pointing.enabled:
                if preview.last_key == ord(' '):
                    paused = not paused
                    last_clock = time.monotonic()
                elif preview.last_key == ord('n'):
                    paused, advance = True, True
        if options.snapshot and cased_frame is not None:
            if pointing.enabled:
                from Feedback.pointingPreview import draw_preview
                display = draw_preview(cased_frame, pointing.centers, pointing.result, '', paused, pointing.trial, live=True, status=status)
            else:
                display = cv2.cvtColor(cased_frame, cv2.COLOR_RGB2BGR)
            options.snapshot.parent.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(options.snapshot), display):
                raise OSError('プレビュー画像を保存できませんでした')
        p.info(f'{frame_count}フレームを処理しました')
        return True
    finally:
        human_position.close()
        model.close()
        camera.stop_camera()
        preview.close_window()
        combo.reset_combo()
        if not dry_run:
            echonet.close()


if __name__ == '__main__':
    main(make_options())
