"""Shared Jetson experiment runner. Python 3.8+, no HGHC device control."""
import argparse
from collections import Counter
from datetime import datetime
from importlib.metadata import version, PackageNotFoundError
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import sys
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parent.parent
GESTURES = ("OPEN_HAND", "FIST", "PEACE", "POINT")
EDGES = ((0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7),
         (7, 8), (5, 9), (9, 10), (10, 11), (11, 12), (9, 13),
         (13, 14), (14, 15), (15, 16), (13, 17), (0, 17), (17, 18),
         (18, 19), (19, 20))
TIMING_KEYS = ("palm_trt_ms", "palm_decode_ms", "roi_ms", "roi_transform_ms",
               "landmark_trt_ms", "restore_ms", "total_ms")
FRAME_FIELDS = ("trial", "frame", "sample_s", "trial_elapsed_s", "expected",
                "hand_detected", "raw", "stable", "mode", "capture_ms",
                "detect_wall_ms", "recognize_ms", "stabilize_ms", "pipeline_ms",
                "cpu_percent", "memory_percent") + TIMING_KEYS
TRIAL_FIELDS = ("trial", "expected", "completed", "distance_cm", "angle_deg",
                "angle_axis", "frames", "detected_frames", "detection_rate",
                "raw_majority", "stable_majority", "raw_trial_correct",
                "stable_trial_correct", "raw_frame_accuracy", "stable_frame_accuracy",
                "raw_unknown_frames", "stable_unknown_frames", "raw_state_changes",
                "stable_state_changes", "raw_wrong_entries", "stable_wrong_entries",
                "raw_cue_to_first_correct_s", "stable_cue_to_first_correct_s")


class CsvLog:
    def __init__(self, path, fields):
        self.file = path.open("w", encoding="utf-8-sig", newline="")
        self.writer = csv.DictWriter(self.file, fieldnames=fields, extrasaction="raise")
        self.writer.writeheader()
        self.file.flush()

    def write(self, row):
        self.writer.writerow(row)
        self.file.flush()

    def close(self):
        self.file.close()


def majority(labels):
    if not labels:
        return "UNKNOWN"
    counts = Counter(labels)
    best = max(counts.values())
    winners = [label for label, count in counts.items() if count == best]
    return winners[0] if len(winners) == 1 else "AMBIGUOUS"


def label_metrics(rows, key, expected):
    labels = [row[key] for row in rows]
    correct = [row["trial_elapsed_s"] for row in rows if row[key] == expected]
    changes = sum(a != b for a, b in zip(labels, labels[1:]))
    wrong_entries = sum(label not in (expected, "UNKNOWN") and
                        (i == 0 or labels[i - 1] != label)
                        for i, label in enumerate(labels))
    return dict(majority=majority(labels),
                trial_correct=int(bool(labels) and majority(labels) == expected),
                frame_accuracy=sum(label == expected for label in labels) / len(labels)
                if labels else "", unknown_frames=labels.count("UNKNOWN"),
                state_changes=changes, wrong_entries=wrong_entries,
                cue_to_first_correct_s=min(correct) if correct else "")


def trial_summary(rows, trial, expected, completed, args):
    row = dict(trial=trial, expected=expected, completed=int(completed),
               distance_cm=args.distance_cm if args.distance_cm is not None else "",
               angle_deg=args.angle_deg if args.angle_deg is not None else "",
               angle_axis=args.angle_axis, frames=len(rows),
               detected_frames=sum(r["hand_detected"] for r in rows),
               detection_rate=sum(r["hand_detected"] for r in rows) / len(rows)
               if rows else "")
    for key in ("raw", "stable"):
        row.update({key + "_" + k: v for k, v in label_metrics(rows, key, expected).items()})
    return row


def distribution(values):
    values = sorted(float(v) for v in values if isinstance(v, (int, float)) and math.isfinite(v))
    if not values:
        return dict(n=0, mean="", median="", p95="", minimum="", maximum="")
    i = (len(values) - 1) * 0.95
    lo, hi = math.floor(i), math.ceil(i)
    p95 = values[lo] + (values[hi] - values[lo]) * (i - lo)
    return dict(n=len(values), mean=statistics.mean(values), median=statistics.median(values),
                p95=p95, minimum=values[0], maximum=values[-1])


def arguments(experiment, argv):
    parser = argparse.ArgumentParser(description="Jetson PipeTRT experiment: " + experiment)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--model", choices=("full", "lite"), default="full")
    parser.add_argument("--precision", choices=("fp16", "fp32"), default="fp16")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "experiments")
    parser.add_argument("--participant", default="P01", help="Use an anonymous ID")
    parser.add_argument("--note", default="")
    parser.add_argument("--distance-cm", type=float)
    parser.add_argument("--angle-deg", type=float)
    parser.add_argument("--angle-axis", choices=("unspecified", "yaw", "pitch", "roll"),
                        default="unspecified")
    parser.add_argument("--trials", type=int, default=20, help="Repeats PER gesture")
    parser.add_argument("--gestures", nargs="+", choices=GESTURES, default=list(GESTURES))
    parser.add_argument("--seed", type=int, default=1025)
    parser.add_argument("--prepare-seconds", type=float, default=2.0)
    parser.add_argument("--hold-seconds", type=float, default=3.0)
    parser.add_argument("--confirmation-seconds", type=float, default=0.3)
    parser.add_argument("--mismatch-seconds", type=float, default=0.1)
    parser.add_argument("--lost-seconds", type=float, default=0.5)
    parser.add_argument("--warmup-frames", type=int, default=30)
    parser.add_argument("--seconds", type=float, default=30.0, help="Timing experiment duration")
    parser.add_argument("--headless", action="store_true",
                        help="Timing experiment only; no preview overhead")
    parser.add_argument("--fresh-engines", action="store_true")
    args = parser.parse_args(argv)
    if len(set(args.gestures)) != len(args.gestures):
        parser.error("gestures must not contain duplicates")
    for name in ("width", "height", "fps", "trials", "prepare_seconds", "hold_seconds",
                 "confirmation_seconds", "seconds"):
        value = getattr(args, name)
        if not math.isfinite(value) or value <= 0:
            parser.error(name + " must be finite and > 0")
    for name in ("mismatch_seconds", "lost_seconds", "warmup_frames"):
        value = getattr(args, name)
        if not math.isfinite(value) or value < 0:
            parser.error(name + " must be finite and >= 0")
    if args.distance_cm is not None and (not math.isfinite(args.distance_cm) or args.distance_cm <= 0):
        parser.error("distance-cm must be finite and > 0")
    if args.angle_deg is not None and not math.isfinite(args.angle_deg):
        parser.error("angle-deg must be finite")
    if experiment == "conditions" and (args.distance_cm is None or args.angle_deg is None):
        parser.error("conditions requires --distance-cm and --angle-deg")
    if args.headless and experiment != "timing":
        parser.error("Guided experiments require a desktop preview; headless is timing only")
    return args


def timing_summary(rows):
    fields = ("capture_ms", "detect_wall_ms", "recognize_ms", "stabilize_ms",
              "pipeline_ms", "cpu_percent", "memory_percent") + TIMING_KEYS
    result = []
    for mode in ("ALL",) + tuple(sorted({r["mode"] for r in rows})):
        group = rows if mode == "ALL" else [r for r in rows if r["mode"] == mode]
        for metric in fields:
            result.append(dict(mode=mode, metric=metric, **distribution([r[metric] for r in group])))
    return result


def run(experiment, argv=None):
    args = arguments(experiment, argv)
    # Import only after --help and argument validation; config.json is not needed.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from Recognizers import gestureRecognizer as recognizer
    from Recognizers import gestureStabilizer as stabilizer
    import cv2
    import numpy as np
    import psutil
    import tensorrt as trt
    if trt.__version__.startswith("8.5.") and "bool" not in np.__dict__:
        np.bool = bool
    if args.fresh_engines:
        os.environ["XDG_CACHE_HOME"] = tempfile.mkdtemp(prefix="hghc-experiment-engines-")
    import pipetrt

    args.output.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix=datetime.now().strftime("%Y%m%d-%H%M%S-") +
                                    experiment + "-", dir=str(args.output)))
    schedule = [g for g in args.gestures for _ in range(args.trials)]
    random.Random(args.seed).shuffle(schedule)
    metadata = dict(experiment=experiment, started_at=datetime.now().astimezone().isoformat(),
                    arguments={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
                    input="raw webcam BGR, no flip/blur/cascade", schedule=schedule,
                    python=sys.version, tensorrt=trt.__version__, numpy=np.__version__,
                    opencv=cv2.__version__, pipetrt_path=pipetrt.__file__, status="initializing")
    metadata["source_sha256"] = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (Path(__file__).resolve(), Path(recognizer.__file__), Path(stabilizer.__file__))
    }
    try:
        metadata["pipetrt_version"] = version("pipetrt")
    except PackageNotFoundError:
        metadata["pipetrt_version"] = "unknown"

    def save_metadata():
        (directory / "session.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2),
                                                encoding="utf-8")

    save_metadata()
    frames_csv = CsvLog(directory / "frames.csv", FRAME_FIELDS)
    trials_csv = CsvLog(directory / "trials.csv", TRIAL_FIELDS)
    all_rows, summaries, current_rows = [], [], []
    camera = model = None
    index = 0
    phase = "READY"
    trial_start = phase_start = benchmark_start = None
    count = 0
    baseline = None
    last_log = 0.0
    window = "HGHC experiment - " + experiment
    status = "aborted"
    exit_code = 0
    print("CSV output:", directory, flush=True)
    print("OPEN_HAND=パー FIST=グー PEACE=チョキ POINT=指差し", flush=True)
    print("SPACE: start next trial / Q: stop. Keep camera and lighting fixed.", flush=True)

    def finish_trial(completed):
        summary = trial_summary(current_rows, index + 1, schedule[index], completed, args)
        trials_csv.write(summary)
        summaries.append(summary)
        print("Trial {}/{} {}: frames={} raw={} stable={} completed={}".format(
            index + 1, len(schedule), schedule[index], len(current_rows),
            summary["raw_majority"], summary["stable_majority"], completed), flush=True)

    try:
        stabilizer.confirmation_seconds = args.confirmation_seconds
        stabilizer.mismatch_tolerance_seconds = args.mismatch_seconds
        stabilizer.lost_timeout_seconds = args.lost_seconds
        stabilizer.reset()
        camera = cv2.VideoCapture(args.camera)
        if not camera.isOpened():
            raise RuntimeError("Cannot open webcam index {}".format(args.camera))
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
        camera.set(cv2.CAP_PROP_FPS, args.fps)
        metadata["camera_actual"] = dict(width=camera.get(cv2.CAP_PROP_FRAME_WIDTH),
                                         height=camera.get(cv2.CAP_PROP_FRAME_HEIGHT),
                                         fps=camera.get(cv2.CAP_PROP_FPS))
        print("Initializing PipeTRT...", flush=True)
        model = pipetrt.HandLandmarker(model=args.model, precision=args.precision)
        manager = getattr(model, "engine_manager", None)
        metadata["engine_directory"] = str(getattr(manager, "engine_dir", "not exposed"))
        metadata["status"] = "running"
        save_metadata()
        psutil.cpu_percent(interval=None)
        if experiment == "timing":
            phase = "WARMUP"
        while True:
            t0 = time.perf_counter()
            ok, frame = camera.read()
            t1 = time.perf_counter()
            if not ok or frame is None:
                raise RuntimeError("Webcam frame read failed")
            if baseline is None:
                baseline = t1
            # Trial timestamps refer to frame acquisition, before inference.
            if phase == "PREPARE" and t1 - phase_start >= args.prepare_seconds:
                phase = "MEASURE"
                trial_start = t1
                current_rows = []
                stabilizer.reset()
                print("MEASURE:", schedule[index], flush=True)
            if phase == "MEASURE" and t1 - trial_start >= args.hold_seconds:
                finish_trial(True)
                current_rows = []
                index += 1
                phase = "READY"
                if index >= len(schedule):
                    status = "completed"
                    break
            if phase == "WARMUP" and count >= args.warmup_frames:
                phase = "BENCHMARK"
                benchmark_start = t1
                stabilizer.reset()
                psutil.cpu_percent(interval=None)
            if phase == "BENCHMARK" and t1 - benchmark_start >= args.seconds:
                metadata["benchmark_elapsed_s"] = t1 - benchmark_start
                status = "completed"
                break

            infer_start = time.perf_counter()
            result = model.detect(frame)
            t2 = time.perf_counter()
            points = result.hand_landmarks
            valid = (points is not None and len(points) == 21 and np.isfinite(points).all())
            if valid:
                height, width = frame.shape[:2]
                landmarks = [dict(id=i, x=float(p[0]) / width, y=float(p[1]) / height,
                                  z=float(p[2])) for i, p in enumerate(points)]
                raw_data = recognizer.recognize(landmarks)
            else:
                raw_data = {"name": "UNKNOWN", "fingers": {}}
            t3 = time.perf_counter()
            stable = stabilizer.stabilizer_process(raw_data, timestamp=t1)["confirmed_gesture"] or "UNKNOWN"
            t4 = time.perf_counter()
            count += 1
            timings = result.timings or {}
            mode = str(timings.get("mode", "UNKNOWN"))
            row = dict(trial=index + 1 if phase == "MEASURE" else 0, frame=count,
                       sample_s=t1 - baseline,
                       trial_elapsed_s=t1 - trial_start if phase == "MEASURE" else "",
                       expected=schedule[index] if phase == "MEASURE" else "",
                       hand_detected=int(valid), raw=raw_data["name"], stable=stable, mode=mode,
                       capture_ms=(t1 - t0) * 1000, detect_wall_ms=(t2 - infer_start) * 1000,
                       recognize_ms=(t3 - t2) * 1000, stabilize_ms=(t4 - t3) * 1000,
                       pipeline_ms=(t4 - t0) * 1000, cpu_percent=psutil.cpu_percent(interval=None),
                       memory_percent=psutil.virtual_memory().percent)
            row.update({key: timings.get(key, "") for key in TIMING_KEYS})
            if phase in ("MEASURE", "BENCHMARK"):
                frames_csv.write(row)
                all_rows.append(row)
                if phase == "MEASURE":
                    current_rows.append(row)
            now = time.perf_counter()
            if now - last_log >= 1:
                print("{} frame={} raw={} stable={} mode={} detect={:.1f}ms".format(
                    phase, count, row["raw"], stable, mode, row["detect_wall_ms"]), flush=True)
                last_log = now
            if not args.headless:
                canvas = frame.copy()
                if valid:
                    xy = [(int(p[0]), int(p[1])) for p in points]
                    for a, b in EDGES:
                        cv2.line(canvas, xy[a], xy[b], (0, 200, 0), 2)
                    for p in xy:
                        cv2.circle(canvas, p, 4, (0, 255, 255), -1)
                label = "{}: {}/{} target={}".format(phase, index + 1, len(schedule), schedule[index])
                if experiment == "timing":
                    label = "{}: frames={} {}".format(phase, count, mode)
                elif phase == "PREPARE":
                    label += " start in {:.1f}s".format(max(0, args.prepare_seconds - (now - phase_start)))
                elif phase == "MEASURE":
                    label += " {:.1f}s left".format(max(0, args.hold_seconds - (now - trial_start)))
                for y, line in ((30, label), (60, "raw={} stable={} {:.1f} ms".format(
                        row["raw"], stable, row["detect_wall_ms"])),
                        (90, "SPACE: next trial | Q / Esc: stop")):
                    cv2.putText(canvas, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.imshow(window, canvas)
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")) or cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                    break
                if key == 32 and phase == "READY":
                    phase = "PREPARE"
                    phase_start = time.perf_counter()
                    print("Prepare trial {}/{}: {}".format(index + 1, len(schedule), schedule[index]), flush=True)
    except KeyboardInterrupt:
        print("Interrupted; partial data will be retained.", flush=True)
    except Exception:
        status = "error"
        exit_code = 1
        metadata["error"] = traceback.format_exc()
        print(metadata["error"], file=sys.stderr)
    finally:
        if phase == "MEASURE":
            finish_trial(False)
        if camera is not None:
            camera.release()
        try:
            if model is not None:
                model.close()
        except Exception:
            metadata["close_error"] = traceback.format_exc()
            exit_code = 1
        if not args.headless:
            try:
                cv2.destroyAllWindows()
            except Exception:
                metadata["display_close_error"] = traceback.format_exc()
        frames_csv.close()
        trials_csv.close()
        timing_csv = CsvLog(directory / "timing_summary.csv",
                            ("mode", "metric", "n", "mean", "median", "p95", "minimum", "maximum"))
        for row in timing_summary(all_rows):
            timing_csv.write(row)
        timing_csv.close()
        completed = [row for row in summaries if row["completed"]]
        accuracy_csv = CsvLog(directory / "accuracy_summary.csv",
                              ("expected", "trials", "raw_correct", "stable_correct",
                               "raw_trial_accuracy", "stable_trial_accuracy"))
        for gesture in args.gestures:
            group = [row for row in completed if row["expected"] == gesture]
            n = len(group)
            raw_correct = sum(row["raw_trial_correct"] for row in group)
            stable_correct = sum(row["stable_trial_correct"] for row in group)
            accuracy_csv.write(dict(expected=gesture, trials=n, raw_correct=raw_correct,
                                    stable_correct=stable_correct,
                                    raw_trial_accuracy=raw_correct / n if n else "",
                                    stable_trial_accuracy=stable_correct / n if n else ""))
        accuracy_csv.close()
        confusion_csv = CsvLog(directory / "confusion.csv", ("output", "expected", "predicted", "trials"))
        for key in ("raw", "stable"):
            counts = Counter((row["expected"], row[key + "_majority"]) for row in completed)
            for (expected, predicted), n in sorted(counts.items()):
                confusion_csv.write(dict(output=key, expected=expected, predicted=predicted, trials=n))
        confusion_csv.close()
        metadata.update(status=status, finished_at=datetime.now().astimezone().isoformat(),
                        measured_frames=len(all_rows), completed_trials=len(completed))
        if experiment == "timing" and benchmark_start is not None:
            elapsed = metadata.get("benchmark_elapsed_s", time.perf_counter() - benchmark_start)
            metadata["benchmark_elapsed_s"] = elapsed
            metadata["throughput_fps"] = len(all_rows) / elapsed if elapsed > 0 else None
        save_metadata()
        print("Saved:", directory, "status=" + status, flush=True)
    return exit_code
