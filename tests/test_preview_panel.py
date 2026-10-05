import unittest
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np

from Feedback.pointingPreview import IMAGE_X, IMAGE_Y, PANEL_WIDTH, click_to_center, draw_preview, preview_geometry


class PreviewPanelTests(unittest.TestCase):
    def result(self):
        return {
            'origin': np.array([960., 600.]),
            'tip': np.array([980., 500.]),
            'candidate': 'AIRCON',
            'gesture': 'POINT',
            'angles': {'AIRCON': 12.4},
            'reason': 'CANDIDATE',
            'best_target': 'AIRCON',
            'best_angle': 12.4,
            'finger_length_px': 101.98,
            'min_finger_length_px': 9.6,
        }

    def test_panel_extends_canvas_without_changing_calibration_geometry(self):
        rgb = np.zeros((1080, 1920, 3), dtype=np.uint8)
        w, h = preview_geometry(rgb.shape)
        display = draw_preview(rgb, {'AIRCON': (-.08, .1)}, self.result(), 'AIRCON', False)
        self.assertEqual(display.shape, (h + 300, w + 280 + PANEL_WIDTH, 3))
        self.assertEqual(click_to_center(IMAGE_X, IMAGE_Y, rgb.shape), (0, 0))
        self.assertEqual(click_to_center(IMAGE_X + w / 2, IMAGE_Y + h / 2, rgb.shape), (.5, .5))
        self.assertLess(click_to_center(IMAGE_X - 40, IMAGE_Y, rgb.shape)[0], 0)
        self.assertLess(click_to_center(IMAGE_X, IMAGE_Y - 40, rgb.shape)[1], 0)
        for point in ((w + 280, IMAGE_Y), (w + 300, IMAGE_Y), (40, 104), (-1, 300), (40, h + 300)):
            self.assertIsNone(click_to_center(*point, rgb.shape))

    def test_overlay_leaves_recognition_frame_and_results_untouched(self):
        rgb = np.full((1080, 1920, 3), (91, 113, 137), dtype=np.uint8)
        original = rgb.copy()
        result = self.result()
        origin = result['origin'].copy()
        tip = result['tip'].copy()
        display = draw_preview(rgb, {'AIRCON': (-.08, .1)}, result, 'AIRCON', False)
        np.testing.assert_array_equal(rgb, original)
        np.testing.assert_array_equal(result['origin'], origin)
        np.testing.assert_array_equal(result['tip'], tip)
        self.assertFalse(np.shares_memory(rgb, display))
        np.testing.assert_array_equal(display[IMAGE_Y + 10, IMAGE_X + 10], [137, 113, 91])

    def test_status_values_override_standalone_trial_values(self):
        trial = SimpleNamespace(state='TRIAL STATE', selected='LIGHT', last_event='TRIAL EVENT', hold_elapsed=.4, hold_seconds=.5)
        status = {
            'input': 'VIDEO', 'frame_index': 88, 'fps': 29.9, 'hand': 'DETECTED',
            'gesture': 'POINT', 'confirmed_gesture': 'OPEN_HAND', 'state': 'COMBO',
            'selected': 'AIRPURI', 'last_action': 'airpuri_power_on', 'action_status': 'SIMULATED',
            'hold_elapsed': .25, 'hold_seconds': .7, 'max_angle_degrees': 20,
            'mode': 'SIMULATION', 'history': ['selected AIRPURI'], 'combo_history': ['OPEN_HAND'], 'combo_remaining': 2.1,
        }
        with patch('Feedback.pointingPreview.cv2.putText', wraps=cv2.putText) as draw_text:
            draw_preview(np.zeros((1080, 1920, 3), dtype=np.uint8), {}, self.result(), 'AIRCON', False, trial, status=status)
        texts = [call.args[1] for call in draw_text.call_args_list]
        for expected in ('DETECTED', 'POINT', 'OPEN_HAND', 'COMBO', 'AIRPURI', 'airpuri_power_on', 'SIMULATED', '0.25 / 0.70 s', '12.4 / 20.0 deg', 'selected AIRPURI'):
            self.assertIn(expected, texts)
        self.assertNotIn('TRIAL STATE', texts)
        self.assertNotIn('TRIAL EVENT', texts)
        self.assertIn('AIRCON', texts)

    def test_small_frame_keeps_diagnostics_visible_and_extra_padding_unclickable(self):
        rgb = np.zeros((100, 160, 3), dtype=np.uint8)
        result = {'origin': None, 'tip': None, 'candidate': None, 'gesture': 'NO HAND', 'angles': {}, 'reason': 'NO HAND'}
        display = draw_preview(rgb, {}, result, 'AIRCON', True)
        self.assertGreaterEqual(display.shape[0], 740)
        self.assertIsNone(click_to_center(50, 450, rgb.shape))

    def test_no_candidate_shows_nearest_and_finger_diagnostics(self):
        result = self.result()
        result.update(candidate=None, reason='FINGER TOO SHORT', finger_length_px=3., min_finger_length_px=9.6)
        with patch('Feedback.pointingPreview.cv2.putText', wraps=cv2.putText) as draw_text:
            draw_preview(np.zeros((1080, 1920, 3), dtype=np.uint8), {}, result, 'LIGHT', False)
        texts = [call.args[1] for call in draw_text.call_args_list]
        self.assertIn('FINGER  3.0 px  /  MIN 9.6 px', texts)
        self.assertIn('CHECK   FINGER TOO SHORT', texts)
        self.assertIn('NEAREST AIRCON (12.4 deg)', texts)


if __name__ == '__main__':
    unittest.main()
