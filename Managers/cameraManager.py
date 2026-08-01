
#? Managers/cameraManager.py
#? Norifumi Konndo

import cv2

import Utils.logger as p

settings = {}
captures = {}
current_resolution = "1920x1080"

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

        return (
            f"http://{username}:{password}@{host}"
            f"/axis-cgi/mjpg/video.cgi"
            f"?resolution={resolution}"
        )

    if camera_type in ("url", "iphone"):
        return connection.get("url")
    return None

def try_open(camera):
    camera_id = camera.get("id", "unknown_camera")
    display_name = camera.get("display_name", camera_id)
    camera_type = str(camera.get("type", "")).lower()
    connection = camera.get("connection", {})

    try:
        if camera_type in ("axis", "url", "iphone"):
            source = make_url(camera)
            if not source:
                p.warning(
                    f"{display_name}の接続URLが設定されていません"
                )
                return None
        elif camera_type == "webcam":
            source = int(connection.get("device_id", 0))
        else:
            p.warning(
                f"{display_name}のカメラ形式が不明です: "
                f"{camera_type}"
            )
            return None
        p.info(f"{display_name}に接続中")

        capture = cv2.VideoCapture(source)

        if not capture.isOpened():
            p.error(f"{display_name}を開くことができませんでした")
            capture.release()
            return None
        p.success(f"{display_name}への接続に成功しました")
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
    camera_sources = settings.get("sources", [])
    max_active_cameras = int(
        settings.get("max_active_cameras", 2)
    )

    for camera in camera_sources:
        if len(captures) >= max_active_cameras:
            break
        camera_id = camera.get("id")

        if not camera_id:
            p.warning("idが設定されていないカメラをスキップしました")
            continue

        if camera_id in captures:
            p.warning(
                f"カメラIDが重複しています: {camera_id}"
            )
            continue

        capture = try_open(camera)
        
        if capture is None:
            continue

        captures[camera_id] = capture

    if not captures:
        return False
    p.info(f"{len(captures)}台のカメラを開始しました")
    return True

def get_capture(camera_id):
    return captures.get(camera_id)

def read_frame(camera_id):
    capture = captures.get(camera_id)
    if capture is None:
        p.warning(
            f"指定されたカメラが開かれていません: {camera_id}"
        )
        return False, None
    success, frame = capture.read()

    if not success:
        p.warning(
            f"{camera_id}から映像を取得できませんでした"
        )
        return False, None
    return True, frame

def stop_camera(camera_id=None):
    global captures

    if camera_id is not None:
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
    return True