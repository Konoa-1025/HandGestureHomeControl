import math


class PointingTrial:
    def __init__(self, hold_seconds=0.5, gap_tolerance_seconds=0):
        self.hold_seconds = float(hold_seconds)
        self.gap_tolerance_seconds = float(gap_tolerance_seconds)
        if not math.isfinite(self.hold_seconds) or self.hold_seconds <= 0:
            raise ValueError('指差し保持時間は正の有限値で指定してください')
        if not math.isfinite(self.gap_tolerance_seconds) or self.gap_tolerance_seconds < 0:
            raise ValueError('指差しの途切れ許容時間は0以上の有限値で指定してください')
        self.reset()

    def reset(self):
        self._clear_pending()
        self.latched = False
        self.last_time = None
        self.selected = None
        self.last_event = None
        self.event_count = 0
        self.state = 'NO_HAND'

    def _clear_pending(self):
        self.pending = None
        self.started = None
        self.hold_elapsed = 0.0
        self._last_valid_time = None
        self._previous_valid = False

    def update(self, result, timestamp):
        timestamp = float(timestamp)
        if not math.isfinite(timestamp):
            raise ValueError('指差し判定時刻は有限値で指定してください')
        if self.last_time is not None and timestamp < self.last_time:
            self.reset()
        previous_time = self.last_time
        self.last_time = timestamp
        gesture = result.get('gesture', 'NO HAND')
        reason = result.get('reason') or (
            'NO_HAND' if gesture in ('NO HAND', 'NO_HAND') else
            'NOT_POINTING' if gesture != 'POINT' else 'OUT_OF_ANGLE'
        )
        if gesture in ('OPEN_HAND', 'FIST', 'PEACE'):
            self.latched = False
            self._clear_pending()
            self.state = reason
            return None
        if self.latched:
            self.state = 'WAIT_RELEASE'
            return None
        candidate = result.get('candidate') if gesture == 'POINT' else None
        if candidate is None:
            self._previous_valid = False
            self.state = reason
            if (self.pending is not None and self.gap_tolerance_seconds > 0
                    and timestamp - self._last_valid_time <= self.gap_tolerance_seconds + 1e-9):
                self.state = 'TRACKING_GAP'
                return None
            self._clear_pending()
            return None
        if candidate != self.pending:
            self._clear_pending()
            self.pending, self.started = candidate, timestamp
            self._last_valid_time = timestamp
            self._previous_valid = True
            self.state = 'SELECTING'
            return None
        if self._previous_valid:
            self.hold_elapsed = min(self.hold_seconds, self.hold_elapsed + timestamp - previous_time)
        elif timestamp - self._last_valid_time > self.gap_tolerance_seconds + 1e-9:
            self.hold_elapsed = 0.0
            self.started = timestamp
        self._last_valid_time = timestamp
        self._previous_valid = True
        self.state = 'SELECTING'
        if self.hold_elapsed + 1e-9 < self.hold_seconds:
            return None
        self.hold_elapsed = self.hold_seconds
        self.latched = True
        self.state = 'WAIT_RELEASE'
        self.selected = candidate
        event = 'all_lights_power_off' if candidate == 'LIGHT' else f'SELECT {candidate}'
        self.last_event = event
        self.event_count += 1
        return event
