#? tests/test_gesture.py
#? 実機へ送信せず、判定とコンボのつながりを確認する

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

import cv2
import numpy as np

import main
from Managers import appliancesManager as appliances
from Managers import comboManager as combo
from Managers import cameraManager as camera
from Managers import recognitionManager as recognition
from Managers import positionManager as position
from Managers import previewManager as preview
from Recognizers import pointingEstimator as pointing
from Recognizers import gestureStabilizer as stabilizer


def config():
    return json.loads(Path("ex_config.json").read_text(encoding="utf-8"))


def result(candidate="LIGHT", gesture="POINT", reason=None):
    return {"candidate": candidate, "gesture": gesture,
            "reason": reason or ("TARGET_READY" if candidate else "NO_HAND")}


class HoldTests(unittest.TestCase):
    def setUp(self):
        stabilizer.reset()

    def update(self, timestamp, candidate="LIGHT", gesture="POINT"):
        return stabilizer.target_process(result(candidate, gesture), timestamp, 0.5, 0.15)

    def test_hold_and_release(self):
        self.assertIsNone(self.update(0))
        self.assertEqual(self.update(0.5), "LIGHT")
        for index, gesture in enumerate(("POINT", "NO HAND", "UNKNOWN", "UNRECOGNIZED"), 1):
            self.assertIsNone(self.update(index, None, gesture))
            self.assertEqual(stabilizer.target_state, "WAIT_RELEASE")
        self.update(5, None, "OPEN_HAND")
        self.assertIsNone(self.update(6, "AIRCON"))
        self.assertEqual(self.update(6.5, "AIRCON"), "AIRCON")

    def test_short_gap_does_not_count_missing_time(self):
        self.update(0)
        self.update(0.2)
        self.update(0.23, None, "NO HAND")
        self.assertEqual(stabilizer.target_state, "TRACKING_GAP")
        self.update(0.3)
        self.assertAlmostEqual(stabilizer.hold_elapsed, 0.2)
        self.assertIsNone(self.update(0.59))
        self.assertEqual(self.update(0.6), "LIGHT")

    def test_long_gap_and_target_change(self):
        self.update(0)
        self.update(0.4)
        self.update(0.45, None, "NO HAND")
        self.update(0.6)
        self.assertEqual(stabilizer.hold_elapsed, 0)
        self.update(0.9, "AIRCON")
        self.assertEqual(stabilizer.hold_elapsed, 0)
        self.assertEqual(self.update(1.4, "AIRCON"), "AIRCON")

    def test_pause_rewind_and_known_release(self):
        self.update(10)
        self.update(10.3)
        self.update(10.3)
        self.assertAlmostEqual(stabilizer.hold_elapsed, 0.3)
        self.update(0)
        self.assertEqual(stabilizer.hold_elapsed, 0)
        self.update(0.4, None, "FIST")
        self.assertIsNone(stabilizer.pending_target)
        self.assertIsNone(self.update(0.5))
        self.assertEqual(self.update(1), "LIGHT")


class DirectionTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(pointing.Initialization(config()))
        pointing.centers = {"ahead": (0.8, 0.5), "behind": (0.1, 0.5)}

    def hand(self, tip=(0.3, 0.5)):
        landmarks = [{"x": 0.2, "y": 0.5} for _ in range(21)]
        landmarks[8] = dict(zip(("x", "y"), tip))
        return {"hands": [{"landmarks": landmarks}]}

    def test_angles_and_aspect_ratio(self):
        data = pointing.get_target(self.hand(), (720, 1280, 3), {"name": "POINT"})
        self.assertEqual(data["candidate"], "ahead")
        self.assertAlmostEqual(data["angles"]["ahead"], 0)
        self.assertAlmostEqual(data["angles"]["behind"], 180)
        pointing.centers = {"above": (0.4, 0.3)}
        data = pointing.get_target(self.hand((0.3, 0.4)), (720, 1280, 3), {"name": "POINT"})
        self.assertAlmostEqual(data["best_angle"], 0)

    def test_short_missing_nonpoint_and_wrong_angle(self):
        for hand, gesture, reason in ((self.hand((0.201, 0.5)), "POINT", "FINGER_TOO_SHORT"),
                                      ({"hands": []}, "POINT", "NO_HAND"),
                                      (self.hand(), "OPEN_HAND", "NOT_POINTING"),
                                      (self.hand((0.2, 0.4)), "POINT", "OUT_OF_ANGLE")):
            with self.subTest(reason=reason):
                data = pointing.get_target(hand, (720, 1280, 3), {"name": gesture})
                self.assertIsNone(data["candidate"])
                self.assertEqual(data["reason"], reason)

    def test_center_csv_validation(self):
        header = "device,x_normalized,y_normalized\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "centers.csv"
            for text in ("", header + "LIGHT,nan,0\n", header + "LIGHT,0,0\nLIGHT,1,1\n",
                         header + "LIGHT,0\n", header + "LIGHT,0,0,extra\n", header + "LIGHT,-2,0\n"):
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    pointing.load_centers(path)
            path.write_text(header + "LIGHT,0.2,-0.1\n", encoding="utf-8")
            self.assertEqual(pointing.load_centers(path), {"LIGHT": (0.2, -0.1)})

    def test_invalid_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            settings = config()
            settings["pointing"]["settings_path"] = str(path)
            for values in ((0, 20, 0), (0.5, 90, 0), (0.5, 20, -1), (float("inf"), 20, 0)):
                path.write_text(json.dumps(dict(zip(("hold_seconds", "max_angle_degrees", "gap_tolerance_seconds"), values))))
                self.assertFalse(pointing.Initialization(settings))


class ControlTests(unittest.TestCase):
    def setUp(self):
        settings = config()
        self.assertTrue(appliances.Initialization(settings))
        self.assertTrue(combo.Initialization(settings))
        self.assertTrue(recognition.Initialization(settings))
        self.status = {"wait_point_release": False, "history": [], "last_action": None, "action_status": None}
        self.actions = self.enterContext(patch.object(main.action, "action_process", return_value=True))
        self.enterContext(patch.object(main.feedback, "feedback"))
        self.enterContext(patch.object(pointing, "get_direction", return_value={"direction": "UP"}))

    def run_frames(self, frames, dry_run=False):
        with patch.object(recognition, "get_gesture_data") as raw, patch.object(pointing, "get_target") as target, patch.object(stabilizer, "stabilizer_process") as stable:
            for frame in frames:
                timestamp, candidate, gesture = frame[:3]
                confirmed = frame[3] if len(frame) > 3 else gesture
                raw.return_value = {"name": gesture}
                target.return_value = result(candidate, gesture)
                stable.return_value = {"confirmed_gesture": confirmed, "confirmed_direction": "UP"}
                main.gesture_process({"is_hand": gesture != "NO HAND", "hands": []}, (100, 100, 3), timestamp, None, self.status, dry_run)
        return [call.args[0] for call in self.actions.call_args_list]

    def test_light_once_and_release(self):
        self.assertEqual(self.run_frames([(0, "LIGHT", "POINT"), (0.7, "LIGHT", "POINT"), (1.4, "LIGHT", "POINT"),
                                         (2, None, "NO HAND"), (3, "LIGHT", "POINT")]), ["all_lights_power_off"])
        self.assertEqual(self.status["state"], "WAIT_RELEASE")
        self.run_frames([(4, None, "OPEN_HAND"), (5, "LIGHT", "POINT"), (5.7, "LIGHT", "POINT")])
        self.assertEqual(self.actions.call_count, 2)

    def test_device_point_actions(self):
        for device, expected in (("AIRCON", "aircon_toggle_power"), ("BRAIND", "braind_toggle_upper"), ("AIRPURI", "airpurifier_toggle_power")):
            with self.subTest(device=device):
                combo.reset_combo()
                stabilizer.reset()
                self.status["wait_point_release"] = False
                self.actions.reset_mock()
                self.assertEqual(self.run_frames([(0, device, "POINT"), (0.7, device, "POINT"), (1.4, device, "POINT"), (2.1, device, "POINT")]), [expected])

    def test_selection_frame_is_not_combo_input(self):
        self.assertEqual(self.run_frames([(0, "AIRCON", "POINT"), (0.7, "AIRCON", "POINT")]), [])
        self.assertEqual(combo.selected_appliance, "AIRCON")
        self.assertEqual(combo.gesture_history, [])

    def test_existing_combo_and_stale_point(self):
        self.assertEqual(self.run_frames([(0, "AIRCON", "POINT"), (0.7, "AIRCON", "POINT"),
                                         (1.4, None, "OPEN_HAND", "POINT"), (1.6, None, "OPEN_HAND")]), ["aircon_cooling"])

    def test_lost_hand_or_other_target_does_not_execute(self):
        self.run_frames([(0, "AIRCON", "POINT"), (0.7, "AIRCON", "POINT"), (1.4, None, "NO HAND", "POINT"), (1.5, "BRAIND", "POINT")])
        self.actions.assert_not_called()

    def test_recovery_is_not_delayed_by_empty_input(self):
        self.assertEqual(self.run_frames([(0, "AIRCON", "POINT"), (0.7, "AIRCON", "POINT"),
                                         (1.4, None, "NO HAND"), (1.5, "AIRCON", "POINT")]), ["aircon_toggle_power"])

    def test_cancel_and_timeout_allow_retry(self):
        for cancel in ([(1.4, None, "NO HAND"), (2, None, "NO HAND")], [(6, "AIRCON", "POINT")]):
            combo.reset_combo()
            stabilizer.reset()
            self.status["wait_point_release"] = False
            self.actions.reset_mock()
            self.run_frames([(0, "AIRCON", "POINT"), (0.7, "AIRCON", "POINT")] + cancel)
            self.assertFalse(combo.is_combo())
            self.assertEqual(self.run_frames([(7, "AIRCON", "POINT"), (7.7, "AIRCON", "POINT"), (8.4, "AIRCON", "POINT")]), ["aircon_toggle_power"])

    def test_simulation_never_sends(self):
        self.run_frames([(0, "LIGHT", "POINT"), (0.7, "LIGHT", "POINT")], True)
        self.actions.assert_not_called()
        self.assertEqual(self.status["action_status"], "SIMULATED")

    def test_action_failure(self):
        self.actions.return_value = False
        self.run_frames([(0, "LIGHT", "POINT"), (0.7, "LIGHT", "POINT")])
        self.assertEqual(self.status["action_status"], "FAILED")

    def test_legacy_direction_selection(self):
        settings = config()
        settings.pop("pointing")
        settings["home_appliances"]["files"].pop("positionmap")
        self.assertTrue(appliances.Initialization(settings))
        self.assertTrue(recognition.Initialization(settings))
        expected = appliances.select_appliance_abstract("UP")
        self.run_frames([(0, None, "POINT")])
        self.assertEqual(combo.selected_appliance, expected["device"])


class PositionPreviewTests(unittest.TestCase):
    def test_overlap_and_scale(self):
        position.load_floor(config()["position"])
        self.assertEqual(len(position.polygons), 7)
        polygon = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float32)
        self.assertAlmostEqual(position.overlap_area(polygon, (5, 5, 20, 20)), 25)
        position.polygons = {"T1": polygon / 10}
        self.assertEqual(position.locate((1, 1, 5, 5), (10, 10, 3)), "T1")
        self.assertEqual(position.locate((10, 10, 50, 50), (100, 100, 3)), "T1")
        self.assertIsNone(position.locate((20, 20, 30, 30), (10, 10, 3)))

    def test_position_mapping_and_unknown(self):
        settings = config()
        settings["pointing"]["enabled"] = False
        self.assertTrue(appliances.Initialization(settings))
        self.assertEqual(appliances.select_appliance_abstract("UP_RIGHT", "T1")["device"], "AIRCON")
        self.assertIsNone(appliances.select_appliance_abstract("UP_RIGHT", None))
        self.assertIsNone(appliances.select_appliance_abstract("DOWN", "T1"))

    def test_preview_does_not_change_recognition_frame(self):
        pointing.Initialization(config())
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        before = frame.copy()
        display = preview.draw_pointing(frame, {"state": "WAIT_RELEASE", "last_action": "all_lights_power_off"})
        self.assertEqual(display.shape, (840, 1600, 3))
        np.testing.assert_array_equal(frame, before)

    def test_edit_coordinates_and_save(self):
        pointing.Initialization(config())
        with tempfile.TemporaryDirectory() as directory, patch.object(pointing, "centers_path", Path(directory) / "centers.csv"):
            preview.preview_size = (960, 540)
            preview.edit_devices = ["LIGHT"]
            preview.edit_index = 0
            preview.edit_center_click(cv2.EVENT_LBUTTONDOWN, 620, 176, 0, None)
            self.assertEqual(pointing.centers["LIGHT"], (0.5, -0.1))
            preview.edit_center_key(ord("s"))
            self.assertEqual(pointing.load_centers(pointing.centers_path)["LIGHT"], (0.5, -0.1))
            self.assertFalse(preview.centers_dirty)


class CameraTests(unittest.TestCase):
    def tearDown(self):
        camera.stop_camera()

    def test_movie_loop_and_timestamp(self):
        capture = Mock()
        capture.read.side_effect = [(False, None), (True, "frame")]
        capture.get.side_effect = lambda prop: 30 if prop == cv2.CAP_PROP_FPS else 1
        camera.captures["front"] = capture
        camera.source_settings["front"] = {"type": "movie", "loop": True}
        camera.playback_count["front"] = 0
        self.assertEqual(camera.read_frame("front"), "frame")
        self.assertEqual(camera.playback_count["front"], 1)
        self.assertAlmostEqual(camera.get_timestamp("front"), 1 / 30)

    def test_eof_without_loop(self):
        capture = Mock()
        capture.read.return_value = (False, None)
        camera.captures["front"] = capture
        camera.source_settings["front"] = {"type": "movie", "loop": False}
        self.assertIsNone(camera.read_frame("front"))
        self.assertTrue(camera.is_finished("front"))
        self.assertIsNone(camera.read_frame("front"))
        capture.read.assert_called_once()


if __name__ == "__main__":
    unittest.main()
