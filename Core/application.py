from collections import deque

import Managers.actionManager as action
import Managers.appliancesManager as appliances
import Managers.comboManager as combo
import Managers.feedbackManager as feedback
import Managers.pointingManager as pointing
import Managers.recognitionManager as recognize
import Utils.logger as p


class Application:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.wait_point_release = False
        self.last_timestamp = None
        self.last_action = None
        self.action_status = None
        self.history = deque(maxlen=5)
        self.state = 'NO_HAND'
        self.confirmed_gesture = None
        self.last_selected = None

    def record(self, text):
        self.history.appendleft(text)
        p.info(text)

    def execute(self, name):
        self.last_action = name
        if self.dry_run:
            self.action_status = 'SIMULATED'
        else:
            self.action_status = 'SENT' if action.action_process(name) else 'FAILED'
            feedback.feedback('go' if self.action_status == 'SENT' else 'cancel')
        self.record(f'{self.action_status}: {name}')
        self.state = self.action_status

    def reset_playback(self):
        combo.reset_combo()
        recognize.stabilizer.reset()
        if pointing.trial is not None:
            pointing.trial.reset()
        self.wait_point_release = False
        self.last_selected = None
        self.last_action = self.action_status = None
        self.record('VIDEO RESTART')

    def update(self, hand_data, frame_shape, timestamp, current_position=None):
        if self.last_timestamp is not None and timestamp < self.last_timestamp:
            self.reset_playback()
        self.last_timestamp = timestamp
        expired = combo.expire(timestamp)
        if expired:
            self.record('COMBO TIMEOUT')
            if pointing.enabled:
                pointing.trial.reset()
            if not self.dry_run:
                feedback.feedback('cancel')
        event = {'action': None, 'appliance': None}
        if pointing.enabled:
            event = pointing.update(hand_data, frame_shape, timestamp, not combo.is_combo() and not self.wait_point_release)
            self.state = pointing.trial.state
            raw_gesture = pointing.result['gesture']
        else:
            raw_gesture = recognize.get_gesture_data(hand_data)['name'] if hand_data.get('hands') else 'NO HAND'
            self.state = 'NOT_POINTING' if hand_data.get('is_hand') else 'NO_HAND'
        gesture = recognize.gesture_process(hand_data, current_position, timestamp)
        self.confirmed_gesture = gesture['confirmed_gesture']
        if self.wait_point_release:
            released = raw_gesture in ('OPEN_HAND','FIST','PEACE') and self.confirmed_gesture == raw_gesture
            if not released:
                self.state = 'COMBO_TIMEOUT' if expired else 'WAIT_RELEASE'
                return self.snapshot(hand_data, timestamp)
            self.wait_point_release = False
        if combo.is_combo():
            if raw_gesture != self.confirmed_gesture or raw_gesture not in ('POINT', 'OPEN_HAND', 'FIST', 'PEACE'):
                gesture = dict(gesture, confirmed_gesture=None)
            elif pointing.enabled and raw_gesture == 'POINT' and pointing.result['candidate'] != combo.selected_appliance:
                gesture = dict(gesture, confirmed_gesture=None)
            outcome = combo.combo_process(gesture, timestamp)
            status = outcome['status']
            self.state = 'COMBO' if status == 'WAITING' else f'COMBO_{status}'
            if status == 'COMPLETED':
                self.execute(outcome['action'])
                self.wait_point_release = self.confirmed_gesture == 'POINT'
            elif status in ('FAILED','CANCELED'):
                self.record(f'COMBO {status}')
                if pointing.enabled:
                    pointing.trial.reset()
                if not self.dry_run:
                    feedback.feedback('cancel')
        else:
            if not pointing.enabled and self.confirmed_gesture == 'POINT':
                event['appliance'] = appliances.select_appliance_abstract(gesture['confirmed_direction'], current_position)
            if event['action']:
                self.execute(event['action'])
                self.wait_point_release = True
            elif event['appliance']:
                selected = event['appliance']
                combo.start_combo(selected, timestamp)
                self.last_selected = selected['device']
                self.wait_point_release = False
                self.state = 'COMBO'
                self.record(f'SELECT: {self.last_selected}')
                if not self.dry_run:
                    feedback.feedback('start')
            elif expired:
                self.state = 'COMBO_TIMEOUT'
        return self.snapshot(hand_data, timestamp)

    def snapshot(self, hand_data, timestamp):
        trial = pointing.trial if pointing.enabled else None
        return {
            'mode': 'SIMULATION' if self.dry_run else 'LIVE',
            'hand': 'DETECTED' if hand_data.get('is_hand') else 'NONE',
            'gesture': pointing.result['gesture'] if pointing.enabled else self.confirmed_gesture,
            'confirmed_gesture': self.confirmed_gesture,
            'state': self.state,
            'selected': combo.selected_appliance if combo.is_combo() else None,
            'last_action': self.last_action,
            'action_status': self.action_status,
            'history': list(self.history),
            'combo_history': list(combo.gesture_history),
            'combo_remaining': max(0, combo.timeout_seconds - (timestamp - combo.combo_started_at)) if combo.combo_started_at is not None else None,
            'hold_elapsed': trial.hold_elapsed if trial else 0,
            'hold_seconds': trial.hold_seconds if trial else 0,
            'max_angle_degrees': pointing.settings.get('max_angle_degrees',20),
        }
