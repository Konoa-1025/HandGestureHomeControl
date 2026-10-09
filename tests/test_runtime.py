#? tests/test_runtime.py
#? 録画入力と終了処理を、実機へ接続せず確認する

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

import main
from Managers import cameraManager as camera
from Managers import comboManager as combo
from Managers import previewManager as preview
from Managers import recognitionManager as recognition
from Recognizers import gestureStabilizer as stabilizer


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.video = self.path / "sample.avi"
        writer = cv2.VideoWriter(str(self.video), cv2.VideoWriter_fourcc(*"MJPG"), 10, (160, 90))
        self.assertTrue(writer.isOpened())
        for value in (30, 60, 90):
            writer.write(np.full((90, 160, 3), value, dtype=np.uint8))
        writer.release()
        self.settings = json.loads(Path("ex_config.json").read_text(encoding="utf-8"))
        self.settings["cascade"]["resolution"]["high"] = {"width": 160, "height": 90}
        self.settings["cascade"]["resolution"]["low"] = {"width": 160, "height": 90}
        self.enterContext(patch.object(main.figload, "load_setting_config", return_value=self.settings))
        self.actions = self.enterContext(patch.object(main.action, "action_process"))
        self.echonet = self.enterContext(patch.object(main.echonet, "Initialization", side_effect=AssertionError("実機接続")))

    def test_real_video_and_mediapipe_headless(self):
        snapshot = self.path / "preview.png"
        options = main.make_options(["--video", str(self.video), "--headless", "--frames", "5", "--snapshot", str(snapshot)])
        self.assertTrue(main.main(options))
        self.assertIsNotNone(cv2.imread(str(snapshot)))
        self.assertFalse(camera.captures)
        self.assertFalse(combo.is_combo())
        self.assertIsNone(main.model.mediapipeHighModel.hands_model)
        self.actions.assert_not_called()
        self.echonet.assert_not_called()

    def test_movie_restart_clears_combo(self):
        self.enterContext(patch.object(main.model, "Initialization", return_value=True))
        self.enterContext(patch.object(main.model, "model_process", return_value={"is_hand": False, "hands": []}))
        states = []

        def update(hands, shape, timestamp, current_position, status, dry_run):
            states.append((combo.is_combo(), status["wait_point_release"], list(status["history"])))
            combo.start_combo({"device": "AIRCON"}, timestamp)
            status["wait_point_release"] = True

        self.enterContext(patch.object(main, "gesture_process", side_effect=update))
        self.assertTrue(main.main(main.make_options(["--video", str(self.video), "--headless", "--frames", "4"])))
        self.assertFalse(states[-1][0])
        self.assertFalse(states[-1][1])
        self.assertIn("VIDEO RESTART", states[-1][2])

    def test_preview_close_on_no_hand_frame(self):
        self.enterContext(patch.object(main.model, "Initialization", return_value=True))
        self.enterContext(patch.object(main.model, "model_process", return_value={"is_hand": False, "hands": []}))
        self.enterContext(patch.object(preview, "Initialization", return_value=True))
        show = self.enterContext(patch.object(preview, "show_frame_pointing", return_value=False))
        self.assertTrue(main.main(main.make_options(["--video", str(self.video)])))
        show.assert_called_once()
        self.assertFalse(camera.captures)

    def test_initialization_failure_cleans_up(self):
        self.enterContext(patch.object(main.initializer, "Managers_initialize", return_value=False))
        self.assertFalse(main.main(main.make_options(["--video", str(self.video), "--headless", "--frames", "1"])))
        self.assertFalse(camera.captures)
        self.actions.assert_not_called()

    def test_hand_loss_preserves_release_latch(self):
        self.assertTrue(recognition.Initialization(self.settings))
        stabilizer.target_process({"gesture": "POINT", "candidate": "LIGHT", "reason": "TARGET_READY"}, 0, 0.5, 0.15)
        stabilizer.target_process({"gesture": "POINT", "candidate": "LIGHT", "reason": "TARGET_READY"}, 0.5, 0.5, 0.15)
        stabilizer.last_hand_detected_at = 0.5
        recognition.gesture_process({"is_hand": False, "hands": []}, 2, (90, 160, 3))
        self.assertTrue(stabilizer.target_latched)
        self.assertEqual(stabilizer.target_state, "WAIT_RELEASE")

    def test_invalid_command_options(self):
        for args in (["--headless"], ["--frames", "-1"], ["--headless", "--frames", "1", "--paused"], ["--edit-centers", "--live"]):
            with self.subTest(args=args), self.assertRaises(SystemExit):
                main.make_options(args)


if __name__ == "__main__":
    unittest.main()
