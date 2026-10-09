
#? Managers/cameraManager.py
#? Norifumi Konndo

import cv2
import sys
import time
import math
from pathlib import Path
import Utils.logger as p

settings = {}
captures = {}
source_settings = {}
finished_sources = set()
playback_count = {}
current_resolution = "1920x1080"
url = None

def Initialization(config):
    p.info("cameraManagerを初期化中")

    global settings
    settings = config.get("camera")

    if not settings:
        p.error("cameraManagerの設定が見つかりません")
        return False
    

    p.success("cameraManagerの初期化完了")
    return True

def make_url(camera, resolution=None):
    camera_type = str(camera.get("type", "")).lower()
    connection = camera.get("connection", {})

    if camera_type == "axis":
        host = connection.get("host")
        username = connection.get("username")
        password = connection.get("password")

        if not host or not username or not password:
            return None

        if resolution is None:
            resolution = current_resolution

        url = (
            f"http://{username}:{password}@{host}"
            f"/axis-cgi/mjpg/video.cgi"
            f"?resolution={resolution}"
        )
        p.info(f"Camera URL:{url}")

        return url
    if camera_type in ("url", "iphone"):
        return connection.get("url")
    
    if camera_type == "movie":
        if camera.get("movie") is not True:
            #p.warning("録画映像を使用するにはmovieをtrueにしてください")
            return None

        movie_path = connection.get("path")

        if not isinstance(movie_path, str) or not movie_path.strip():
            p.warning("connection.pathに動画パスが設定されていません")
            return None

        path = Path(movie_path).expanduser()

        # 相対パスはconfig.jsonがあるプロジェクト直下を基準にする
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent / path

        if not path.is_file():
            p.warning(f"動画ファイルが見つかりません: {path}")
            return None

        return str(path)
    return None

def try_open(camera):
    camera_id = camera.get("id", "unknown_camera")
    display_name = camera.get("display_name", camera_id)
    camera_type = str(camera.get("type", "")).lower()
    connection = camera.get("connection", {})

    try:
        if camera_type in ("axis", "url", "iphone","movie"):
            source = make_url(camera)
            if not source:
                p.warning(
                    f"{display_name}の接続URLが設定されていません"
                )
                return None
        elif camera_type == "webcam":
            source = int(connection.get("device_id", 0))
            if camera_type == "webcam":
                capture = cv2.VideoCapture(source, cv2.CAP_MSMF if sys.platform == "win32" else cv2.CAP_ANY)
                capture.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*"MJPG"))
                capture.set(cv2.CAP_PROP_FRAME_WIDTH,connection.get("width", 1280))
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT,connection.get("height", 720))
                capture.set(cv2.CAP_PROP_FPS,connection.get("fps", 60))
                capture.set(cv2.CAP_PROP_BUFFERSIZE,1)
        else:
            p.warning(
                f"{display_name}のカメラ形式が不明です: "
                f"{camera_type}"
            )
            return None
        p.info(f"{display_name}に接続中")

        if camera_type != "webcam":
            capture = cv2.VideoCapture(source)

        if not capture.isOpened():
            p.error(f"{display_name}を開くことができませんでした")
            capture.release()
            return None
        p.success(f"{display_name}への接続に成功しました")
        if display_name == "iPhoneカメラ":
            p.debug("Macbookで起動してる場合は上部のカメラとして動く可能性があります。")
        return capture
    
    except (TypeError, ValueError) as error:
        p.error(
            f"{display_name}の設定値が不正です: {error}"
        )
        return None
    
    except Exception as error:
        p.error(
            f"{display_name}への接続中にエラーが発生しました: "
            f"{error}"
        )
        return None

def start_camera():
    global captures

    stop_camera()
    captures = {}

    camera_sources = settings.get("sources")

    if camera_sources is None:
        p.error(
            "camera.sourcesが設定されていません。"
            "config.jsonのcamera階層を確認してください"
        )
        return False

    if not isinstance(camera_sources, list):
        p.error("camera.sourcesは配列で指定してください")
        return False

    if not camera_sources:
        p.error("camera.sourcesにカメラが登録されていません")
        return False

    for camera in camera_sources:
        if not camera.get("enabled", True):
            continue

        camera_id = camera.get("id")

        if not camera_id:
            p.warning("IDが設定されていないカメラをスキップしました")
            continue

        if camera_id in captures:
            p.warning(f"カメラIDが重複しています: {camera_id}")
            continue

        capture = try_open(camera)

        if capture is None:
            continue

        captures[camera_id] = capture
        source_settings[camera_id] = camera
        playback_count[camera_id] = 0

    if not captures:
        p.error("有効なカメラを開くことができませんでした")
        return False

    p.success(f"{len(captures)}台のカメラを開始しました")
    return True

def get_capture(camera_id):
    return captures.get(camera_id)

def read_frame(camera_id):
    capture = captures.get(camera_id)

    if capture is None or camera_id in finished_sources:
        return None

    success, frame = capture.read()
    source = source_settings.get(camera_id, {})
    if not success and source.get("type", "").lower() == "movie":
        if source.get("loop", True):
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            success, frame = capture.read()
            playback_count[camera_id] += 1
        if not success:
            finished_sources.add(camera_id)
            return None

    if not success:
        p.warning(
            f"{camera_id}からフレームを取得できませんでした"
        )
        return None

    return frame

def stop_camera(camera_id=None):
    global captures

    if camera_id is not None:
        source_settings.pop(camera_id, None)
        finished_sources.discard(camera_id)
        playback_count.pop(camera_id, None)
        capture = captures.pop(camera_id, None)
        if capture is None:
            return False
        capture.release()
        p.info(f"{camera_id}を停止しました")
        return True

    for current_id, capture in list(captures.items()):
        try:
            capture.release()
            p.info(f"{current_id}を停止しました")
        except Exception as error:
            p.warning(
                f"{current_id}の停止中にエラーが発生しました: "
                f"{error}"
            )

    captures = {}
    source_settings.clear()
    finished_sources.clear()
    playback_count.clear()
    return True

def is_finished(camera_id):
    return camera_id in finished_sources


def get_timestamp(camera_id):
    capture = captures.get(camera_id)
    source = source_settings.get(camera_id, {})
    if capture is not None and source.get("type", "").lower() == "movie":
        fps = capture.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(fps) or fps < 1:
            fps = 1
        return capture.get(cv2.CAP_PROP_POS_FRAMES) / fps
    return time.monotonic()
