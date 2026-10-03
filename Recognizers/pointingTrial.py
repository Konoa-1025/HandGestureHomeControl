class PointingTrial:
    def __init__(self, hold_seconds=0.5):
        self.hold_seconds = hold_seconds
        self.reset()

    def reset(self):
        self.pending = None
        self.started = None
        self.latched = False
        self.last_time = None
        self.selected = None
        self.last_event = None
        self.event_count = 0

    def update(self, result, timestamp):
        if self.last_time is not None and timestamp < self.last_time:
            self.reset()
        self.last_time = timestamp
        gesture = result['gesture']
        if gesture not in ('POINT', 'NO HAND', 'UNKNOWN'):
            self.latched = False
        candidate = result['candidate'] if gesture == 'POINT' else None
        if candidate is None or self.latched:
            self.pending = self.started = None
            return None
        if candidate != self.pending:
            self.pending, self.started = candidate, timestamp
            return None
        if timestamp - self.started < self.hold_seconds:
            return None
        self.latched = True
        self.selected = candidate
        event = 'all_lights_power_off' if candidate == 'LIGHT' else f'SELECT {candidate}'
        self.last_event = event
        self.event_count += 1
        return event
