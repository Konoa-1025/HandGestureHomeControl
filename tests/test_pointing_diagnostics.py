import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from Recognizers.devicePointing import compare_direction, load_centers
from Recognizers.pointingTrial import PointingTrial


class DirectionDiagnosticsTests(unittest.TestCase):
    def hand(self, tip=(.3, .5)):
        points = [{'x': .2, 'y': .5} for _ in range(21)]
        points[8] = dict(zip(('x', 'y'), tip))
        return {'hands': [{'landmarks': points}]}

    def test_missing_hand_has_reason_and_threshold(self):
        result = compare_direction({'hands': []}, (720, 1280, 3), {})
        self.assertEqual(result['reason'], 'NO_HAND')
        self.assertIsNone(result['finger_length_px'])
        self.assertIsNone(result['best_angle'])
        self.assertAlmostEqual(result['min_finger_length_px'], 6.4)

    @patch('Recognizers.devicePointing.gesture.run', return_value={'name': 'POINT'})
    def test_forward_and_opposite_targets_have_distinct_angles(self, _):
        result = compare_direction(self.hand(), (720, 1280, 3),
                                   {'ahead': (.8, .5), 'behind': (.1, .5)})
        self.assertEqual(result['reason'], 'TARGET_READY')
        self.assertEqual(result['candidate'], 'ahead')
        self.assertEqual(result['best_target'], 'ahead')
        self.assertAlmostEqual(result['best_angle'], 0)
        self.assertAlmostEqual(result['angles']['behind'], 180)
        self.assertAlmostEqual(result['finger_length_px'], 128)

    @patch('Recognizers.devicePointing.gesture.run', return_value={'name': 'OPEN_HAND'})
    def test_non_point_still_reports_geometry(self, _):
        result = compare_direction(self.hand(), (720, 1280, 3), {'ahead': (.8, .5)})
        self.assertEqual(result['reason'], 'NOT_POINTING')
        self.assertIsNone(result['candidate'])
        self.assertEqual(result['best_target'], 'ahead')
        self.assertAlmostEqual(result['best_angle'], 0)
        self.assertGreater(result['finger_length_px'], 0)

    @patch('Recognizers.devicePointing.gesture.run', return_value={'name': 'POINT'})
    def test_short_finger_reports_the_actual_length(self, _):
        result = compare_direction(self.hand((.201, .5)), (720, 1280, 3), {'ahead': (.8, .5)})
        self.assertEqual(result['reason'], 'FINGER_TOO_SHORT')
        self.assertIsNone(result['candidate'])
        self.assertAlmostEqual(result['finger_length_px'], 1.28)
        self.assertEqual(result['best_target'], 'ahead')

    @patch('Recognizers.devicePointing.gesture.run', return_value={'name': 'POINT'})
    def test_zero_length_empty_targets_and_wrong_angle(self, _):
        zero = compare_direction(self.hand((.2, .5)), (720, 1280, 3), {'ahead': (.8, .5)})
        empty = compare_direction(self.hand(), (720, 1280, 3), {})
        off = compare_direction(self.hand(), (720, 1280, 3), {'above': (.2, .1)})
        self.assertEqual(zero['reason'], 'FINGER_TOO_SHORT')
        self.assertEqual(empty['reason'], 'NO_TARGETS')
        self.assertEqual(off['reason'], 'OUT_OF_ANGLE')
        self.assertEqual(off['best_target'], 'above')
        self.assertAlmostEqual(off['best_angle'], 90)


class CenterFileTests(unittest.TestCase):
    def load(self, content):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'centers.csv'
            path.write_text(content, encoding='utf-8')
            return load_centers(path)

    def test_off_screen_targets_and_empty_map_are_valid(self):
        self.assertEqual(self.load('\ufeffdevice,x_normalized,y_normalized\nLIGHT,0.2,-0.1\n'),
                         {'LIGHT': (.2, -.1)})
        self.assertEqual(self.load('device,x_normalized,y_normalized\n'), {})

    def test_invalid_headers_duplicates_and_coordinates_are_rejected(self):
        header = 'device,x_normalized,y_normalized\n'
        invalid = [
            '', 'device,x,y\n', 'device,x_normalized,y_normalized,device\n',
            header + 'LIGHT,0,0\nLIGHT,1,1\n',
            header + ',0,0\n', header + 'LIGHT,0\n',
            header + 'LIGHT,0,0,extra\n', header + 'LIGHT,no,0\n',
            header + 'LIGHT,nan,0\n', header + 'LIGHT,0,inf\n',
            header + 'LIGHT,-1.1,0\n', header + 'LIGHT,0,2.1\n',
        ]
        for content in invalid:
            with self.subTest(content=content), self.assertRaises(ValueError):
                self.load(content)


class HoldDiagnosticsTests(unittest.TestCase):
    def result(self, candidate='LIGHT', gesture='POINT', reason=None):
        result = {'candidate': candidate, 'gesture': gesture}
        if reason is not None:
            result['reason'] = reason
        return result

    def test_short_gap_retains_hold_without_counting_unobserved_interval(self):
        trial = PointingTrial(.5, .15)
        trial.update(self.result(), 0)
        trial.update(self.result(), .2)
        self.assertAlmostEqual(trial.hold_elapsed, .2)
        self.assertIsNone(trial.update(self.result(None, 'NO HAND'), .23))
        self.assertEqual(trial.state, 'TRACKING_GAP')
        self.assertIsNone(trial.update(self.result(), .3))
        self.assertAlmostEqual(trial.hold_elapsed, .2)
        self.assertIsNone(trial.update(self.result(), .59))
        self.assertEqual(trial.update(self.result(), .6), 'all_lights_power_off')
        self.assertEqual(trial.state, 'WAIT_RELEASE')
        self.assertAlmostEqual(trial.hold_elapsed, .5)

    def test_long_gap_resets_hold_and_never_fires_while_missing(self):
        trial = PointingTrial(.5, .15)
        trial.update(self.result(), 0)
        trial.update(self.result(), .49)
        self.assertIsNone(trial.update(self.result(None, 'UNKNOWN'), .55))
        self.assertEqual(trial.state, 'TRACKING_GAP')
        self.assertIsNone(trial.update(self.result(None, 'NO HAND'), .7))
        self.assertEqual(trial.state, 'NO_HAND')
        self.assertIsNone(trial.pending)
        self.assertEqual(trial.hold_elapsed, 0)
        self.assertIsNone(trial.update(self.result(), .8))
        self.assertEqual(trial.update(self.result(), 1.3), 'all_lights_power_off')

    def test_recovery_after_tolerance_restarts_even_without_more_missing_frames(self):
        trial = PointingTrial(.5, .15)
        trial.update(self.result(), 0)
        trial.update(self.result(), .4)
        trial.update(self.result(None, 'UNKNOWN'), .45)
        self.assertIsNone(trial.update(self.result(), .6))
        self.assertEqual(trial.hold_elapsed, 0)
        self.assertEqual(trial.update(self.result(), 1.1), 'all_lights_power_off')

    def test_target_switch_discards_previous_target_hold(self):
        trial = PointingTrial(.5, .15)
        trial.update(self.result(), 0)
        trial.update(self.result(), .4)
        trial.update(self.result('AIRCON'), .45)
        self.assertEqual(trial.hold_elapsed, 0)
        self.assertIsNone(trial.update(self.result('AIRCON'), .9))
        self.assertEqual(trial.update(self.result('AIRCON'), .95), 'SELECT AIRCON')

    def test_only_known_non_point_gesture_rearms(self):
        trial = PointingTrial(.5, .15)
        trial.update(self.result(), 0)
        trial.update(self.result(), .5)
        for timestamp, name in enumerate(('NO HAND', 'NO_HAND', 'UNKNOWN', 'UNRECOGNIZED'), 1):
            self.assertIsNone(trial.update(self.result(None, name), timestamp))
            self.assertEqual(trial.state, 'WAIT_RELEASE')
        self.assertIsNone(trial.update(self.result('AIRCON'), 5))
        self.assertEqual(trial.event_count, 1)
        trial.update(self.result(None, 'OPEN_HAND'), 6)
        self.assertFalse(trial.latched)
        trial.update(self.result('AIRCON'), 7)
        self.assertEqual(trial.update(self.result('AIRCON'), 7.5), 'SELECT AIRCON')

    def test_known_release_clears_pending_even_with_gap_tolerance(self):
        trial = PointingTrial(.5, .15)
        trial.update(self.result(), 0)
        trial.update(self.result(), .4)
        trial.update(self.result(None, 'FIST'), .45)
        self.assertEqual(trial.hold_elapsed, 0)
        self.assertIsNone(trial.pending)
        self.assertEqual(trial.state, 'NOT_POINTING')

    def test_same_timestamp_does_not_advance_hold(self):
        trial = PointingTrial(.5, .15)
        trial.update(self.result(), 1)
        trial.update(self.result(), 1.2)
        for _ in range(10):
            self.assertIsNone(trial.update(self.result(), 1.2))
        self.assertAlmostEqual(trial.hold_elapsed, .2)

    def test_video_rewind_resets_event_and_hold_state(self):
        trial = PointingTrial(.5, .15)
        trial.update(self.result(), 10)
        trial.update(self.result(), 10.5)
        self.assertIsNone(trial.update(self.result(), 0))
        self.assertEqual(trial.state, 'SELECTING')
        self.assertEqual(trial.event_count, 0)
        self.assertIsNone(trial.last_event)
        self.assertIsNone(trial.selected)
        self.assertEqual(trial.update(self.result(), .5), 'all_lights_power_off')

    def test_invalid_timing_settings_are_rejected(self):
        for hold, gap in ((0, 0), (-1, 0), (float('inf'), 0), (.5, -.1), (.5, float('nan'))):
            with self.subTest(hold=hold, gap=gap), self.assertRaises(ValueError):
                PointingTrial(hold, gap)


if __name__ == '__main__':
    unittest.main()
