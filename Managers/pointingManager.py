import json
import math
from pathlib import Path

import Utils.logger as p
from Recognizers.devicePointing import load_centers, compare_direction
from Recognizers.pointingTrial import PointingTrial
from Managers import appliancesManager as appliances

enabled = False
centers = {}
settings = {}
trial = None
result = {'origin': None, 'tip': None, 'angles': {}, 'candidate': None, 'gesture': 'NO HAND'}


def Initialization(config):
    global enabled, centers, settings, trial, result
    enabled = config.get('pointing', {}).get('enabled', False)
    centers, settings, trial = {}, {}, None
    result = compare_direction({'hands': []}, (1,1,3), {})
    if not enabled:
        return True
    root = Path(__file__).resolve().parent.parent
    try:
        centers = load_centers(root / 'Data/homeAppliances/pointCenters.csv')
        settings = json.loads((root / 'Data/homeAppliances/pointingTrial.json').read_text())
        hold = float(settings['hold_seconds'])
        angle = float(settings['max_angle_degrees'])
        length = float(settings.get('min_finger_length_ratio', .005))
        if not (math.isfinite(hold) and hold > 0 and 0 < angle < 90 and 0 <= length <= 1):
            raise ValueError('指差し設定値が不正です')
        if any(appliances.get_appliance(device) is None for device in centers):
            raise ValueError('中心点CSVに未登録の家電IDがあります')
        trial = PointingTrial(hold)
        p.success('家電中心への指差し判定を初期化しました')
        return True
    except (OSError, ValueError, KeyError, TypeError) as error:
        p.error(f'指差し判定の初期化に失敗しました: {error}')
        return False


def update(hand_data, frame_shape, timestamp, allow_selection=True):
    global result
    result = compare_direction(hand_data, frame_shape, centers, settings['max_angle_degrees'], settings.get('min_finger_length_ratio', .005))
    event = trial.update(result if allow_selection else dict(result, candidate=None), timestamp)
    if event == 'all_lights_power_off':
        return {'action': event, 'appliance': None}
    if event and event.startswith('SELECT '):
        return {'action': None, 'appliance': appliances.get_appliance(event[7:])}
    return {'action': None, 'appliance': None}
