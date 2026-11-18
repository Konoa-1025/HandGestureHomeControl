"""Experiment scoring and mocked camera lifecycle; no GPU/camera needed."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

spec = importlib.util.spec_from_file_location(
    "experiment_common", Path(__file__).resolve().parents[1] / "experiments" / "common.py")
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)


class MetricsTests(unittest.TestCase):
    def test_missing_frames_remain_in_denominator_and_tie_does_not_pass(self):
        rows = [dict(raw=g, trial_elapsed_s=i / 10)
                for i, g in enumerate(("UNKNOWN", "FIST", "FIST", "UNKNOWN"))]
        result = common.label_metrics(rows, "raw", "FIST")
        self.assertEqual(result["majority"], "AMBIGUOUS")
        self.assertEqual(result["trial_correct"], 0)
        self.assertEqual(result["frame_accuracy"], 0.5)
        self.assertEqual(result["unknown_frames"], 2)
        self.assertEqual(result["cue_to_first_correct_s"], 0.1)

    def test_state_changes_and_wrong_entries_are_distinct(self):
        labels = ("UNKNOWN", "FIST", "PEACE", "PEACE", "UNKNOWN", "PEACE", "FIST")
        rows = [dict(raw=g, trial_elapsed_s=i) for i, g in enumerate(labels)]
        result = common.label_metrics(rows, "raw", "FIST")
        self.assertEqual(result["state_changes"], 5)
        self.assertEqual(result["wrong_entries"], 2)

    def test_aborted_and_empty_trials_do_not_pass(self):
        args = SimpleNamespace(distance_cm=50, angle_deg=30, angle_axis="yaw")
        row = dict(raw="UNKNOWN", stable="UNKNOWN", trial_elapsed_s=0, hand_detected=0)
        result = common.trial_summary([row], 1, "FIST", False, args)
        self.assertEqual(result["completed"], 0)
        self.assertEqual(result["detection_rate"], 0)
        self.assertEqual(result["stable_cue_to_first_correct_s"], "")
        empty = common.trial_summary([], 2, "FIST", False, args)
        self.assertEqual(empty["raw_trial_correct"], 0)
        self.assertEqual(empty["raw_frame_accuracy"], "")

    def test_timing_mode_groups_and_percentile(self):
        self.assertAlmostEqual(common.distribution([1, 2, 3, 4])["p95"], 3.85)
        rows = []
        for mode, ms in (("DETECTION", 20), ("TRACKING", 5)):
            row = {key: "" for key in common.FRAME_FIELDS}
            row.update(mode=mode, detect_wall_ms=ms)
            rows.append(row)
        result = {(r["mode"], r["metric"]): r for r in common.timing_summary(rows)}
        self.assertEqual(result[("ALL", "detect_wall_ms")]["mean"], 12.5)
        self.assertEqual(result[("DETECTION", "detect_wall_ms")]["mean"], 20)
        self.assertEqual(result[("TRACKING", "palm_trt_ms")]["n"], 0)

    def test_invalid_experiment_arguments_are_rejected(self):
        for experiment, argv in (("accuracy", ["--headless"]), ("conditions", []),
                                 ("accuracy", ["--gestures", "FIST", "FIST"])):
            with self.subTest(experiment=experiment, argv=argv), self.assertRaises(SystemExit):
                common.arguments(experiment, argv)


class RunnerTests(unittest.TestCase):
    def simulate(self, experiment, argv, disconnect=False):
        frame = np.zeros((8, 12, 3), dtype=np.uint8)
        frame[:] = [11, 22, 33]
        camera = Mock()
        camera.isOpened.return_value = True
        camera.read.return_value = True, frame
        if disconnect:
            camera.read.side_effect = [(True, frame)] * 4 + [(False, None)]
        camera.get.return_value = 30.0
        cv = Mock()
        cv.__version__ = "test"
        cv.VideoCapture.return_value = camera
        cv.waitKey.return_value = 32
        cv.getWindowProperty.return_value = 1
        model = Mock()
        model.engine_manager.engine_dir = Path("/test/engines")
        # All coincident joints produce FIST in the actual HGHC angle recognizer.
        model.detect.return_value = SimpleNamespace(
            hand_landmarks=np.zeros((21, 3)),
            timings={"mode": "DETECTION", "palm_trt_ms": 2.0})
        pipe = Mock()
        pipe.__file__ = "/test/pipetrt.py"
        pipe.HandLandmarker.return_value = model
        psutil = Mock()
        psutil.cpu_percent.return_value = 20
        psutil.virtual_memory.return_value.percent = 30
        clock = iter(i * 0.01 for i in range(10000))
        modules = {"cv2": cv, "tensorrt": SimpleNamespace(__version__="8.5.2.2"),
                   "pipetrt": pipe, "psutil": psutil}
        with tempfile.TemporaryDirectory() as directory, patch.dict("sys.modules", modules), \
                patch.object(common.time, "perf_counter", side_effect=lambda: next(clock)):
            code = common.run(experiment, argv + ["--output", directory])
            session = next(Path(directory).iterdir())
            meta = json.loads((session / "session.json").read_text())
            csvs = {}
            for path in session.glob("*.csv"):
                self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))
                with path.open(encoding="utf-8-sig") as f:
                    csvs[path.name] = list(csv.DictReader(f))
            self.assertEqual(meta["measured_frames"], len(csvs["frames.csv"]))
            for call in model.detect.call_args_list:
                self.assertIs(call.args[0], frame)
            camera.release.assert_called_once()
            model.close.assert_called_once()
            return code, meta, csvs, cv

    def test_timing_excludes_warmup_and_exports_rows(self):
        code, meta, csvs, cv = self.simulate("timing", [
            "--headless", "--seconds", "0.2", "--warmup-frames", "2"])
        self.assertEqual(code, 0)
        self.assertEqual(meta["status"], "completed")
        self.assertTrue(csvs["frames.csv"])
        self.assertEqual(int(csvs["frames.csv"][0]["frame"]), 3)
        self.assertTrue(meta["throughput_fps"] > 0)
        cv.imshow.assert_not_called()

    def test_guided_trial_exports_actual_recognizer_and_stabilizer_results(self):
        code, meta, csvs, cv = self.simulate("stability", [
            "--trials", "1", "--gestures", "FIST", "--prepare-seconds", "0.05",
            "--hold-seconds", "0.4", "--confirmation-seconds", "0.05"])
        self.assertEqual(code, 0)
        self.assertEqual(meta["status"], "completed")
        self.assertEqual(meta["completed_trials"], 1)
        row = csvs["trials.csv"][0]
        self.assertEqual(row["raw_majority"], "FIST")
        self.assertEqual(row["stable_majority"], "FIST")
        self.assertEqual(row["completed"], "1")
        self.assertEqual(csvs["accuracy_summary.csv"][0]["raw_trial_accuracy"], "1.0")
        self.assertEqual(len(csvs["confusion.csv"]), 2)
        cv.imshow.assert_called()

    def test_camera_disconnect_retains_partial_trial_and_excludes_it_from_accuracy(self):
        code, meta, csvs, _ = self.simulate("accuracy", [
            "--trials", "1", "--gestures", "FIST", "--prepare-seconds", "0.01",
            "--hold-seconds", "20"], disconnect=True)
        self.assertEqual(code, 1)
        self.assertEqual(meta["status"], "error")
        self.assertTrue(csvs["frames.csv"])
        self.assertEqual(csvs["trials.csv"][0]["completed"], "0")
        self.assertEqual(csvs["accuracy_summary.csv"][0]["trials"], "0")


if __name__ == "__main__":
    unittest.main()
