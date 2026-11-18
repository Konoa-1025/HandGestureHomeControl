"""Standalone PipeTRT webcam test. No HGHC config, cascades or network control.

Jetson desktop: python test_pipetrt_webcam.py
SSH: python test_pipetrt_webcam.py --headless --frames 300
Fresh engines: python test_pipetrt_webcam.py --fresh-engines
"""

import argparse
from collections import Counter
import os
import tempfile
import time


CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--model", choices=("full", "lite"), default="full")
    parser.add_argument("--precision", choices=("fp16", "fp32"), default="fp16")
    parser.add_argument("--frames", type=int, default=0, help="0 = until Q / Esc / Ctrl+C")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--fresh-engines", action="store_true",
                        help="Use a new cache directory; retain existing engines")
    args = parser.parse_args(argv)
    if args.frames < 0 or args.width <= 0 or args.height <= 0:
        parser.error("frames must be >= 0; width and height must be > 0")
    if args.headless and args.frames == 0:
        parser.error("Use --frames with --headless")

    # Set before importing PipeTRT. Its Linux engine manager uses XDG_CACHE_HOME.
    if args.fresh_engines:
        cache = tempfile.mkdtemp(prefix="hghc-pipetrt-test-")
        os.environ["XDG_CACHE_HOME"] = cache
        print("Fresh cache root:", cache, flush=True)

    import cv2
    import numpy as np
    import tensorrt as trt

    if trt.__version__.startswith("8.5.") and "bool" not in np.__dict__:
        np.bool = bool

    import pipetrt

    print("TensorRT:", trt.__version__, "NumPy:", np.__version__,
          "OpenCV:", cv2.__version__, flush=True)
    print("PipeTRT:", pipetrt.__file__, flush=True)
    print("Input: raw OpenCV BGR; no flip, blur or HGHC preprocessing", flush=True)
    camera = cv2.VideoCapture(args.camera)
    model = None
    count = detected = 0
    modes = Counter()
    try:
        if not camera.isOpened():
            raise RuntimeError("Cannot open webcam index {}".format(args.camera))
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
        camera.set(cv2.CAP_PROP_FPS, 30)
        print("Initializing PipeTRT (engine build may take time)...", flush=True)
        model = pipetrt.HandLandmarker(model=args.model, precision=args.precision)
        manager = getattr(model, "engine_manager", None)
        print("Engine cache:", getattr(manager, "engine_dir", "not exposed"), flush=True)
        print("Show a hand close to the camera. Q / Esc exits.", flush=True)
        last_log = 0.0
        while args.frames == 0 or count < args.frames:
            ok, frame = camera.read()
            if not ok or frame is None:
                raise RuntimeError("Webcam frame read failed")
            # Pass the unmodified BGR frame directly to PipeTRT.
            started = time.perf_counter()
            result = model.detect(frame)
            elapsed_ms = (time.perf_counter() - started) * 1000
            landmarks = result.hand_landmarks
            points = 0 if landmarks is None else len(landmarks)
            timings = result.timings or {}
            mode = timings.get("mode", "UNKNOWN")
            count += 1
            detected += int(points > 0)
            modes[mode] += 1
            now = time.monotonic()
            if count == 1 or now - last_log >= 1:
                print("frame={} mode={} landmarks={} time={:.1f}ms timings={}".format(
                    count, mode, points, elapsed_ms, timings), flush=True)
                last_log = now

            if not args.headless:
                canvas = frame.copy()
                if points:
                    xy = [(int(point[0]), int(point[1])) for point in landmarks]
                    for a, b in CONNECTIONS:
                        if a < points and b < points:
                            cv2.line(canvas, xy[a], xy[b], (0, 200, 0), 2)
                    for point in xy:
                        cv2.circle(canvas, point, 4, (0, 255, 255), -1)
                label = "{} | points={} | {:.1f} ms | {}/{} detected".format(
                    mode, points, elapsed_ms, detected, count)
                cv2.putText(canvas, label, (12, 32), cv2.FONT_HERSHEY_SIMPLEX,
                            0.65, (0, 255, 0), 2)
                cv2.imshow("PipeTRT standalone - raw BGR", canvas)
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")):
                    break
                if cv2.getWindowProperty("PipeTRT standalone - raw BGR",
                                         cv2.WND_PROP_VISIBLE) < 1:
                    break
    except KeyboardInterrupt:
        print("Stopped.", flush=True)
    finally:
        camera.release()
        if model is not None:
            model.close()
        if not args.headless:
            cv2.destroyAllWindows()
        print("Summary: frames={} detected={} modes={}".format(
            count, detected, dict(modes)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
