
#? Managers/cameraManager.py
#? Norifumi Konndo

import Utils.logger as p

settings = {}
captures = []
current_resolution = "1920x1080"

def Initialization(config):
    p.info("cameraManagerを初期化中")

    global settings
    settings = config.get("camera", config)

    if settings is None:
        p.error("cameraManagerの設定が見つかりません")
        return False

    if not start_camera():
        p.error("カメラを開くことに失敗しました。")

    p.success("cameraManagerの初期化完了")

    return True

def make_url(camera,resolution = None):
    if camera["type"] == "axis":
        if resolution is None:
            resolution = current_resolution
        return(f"http:{camera['user']}:{camera['password']}@{camera['host']}/axis-cgi/mjpg/video.cgi?resolution={resolution}")


def start_camera():
    global captures
    captures = []

    camera_source = settings.get("sourcces") or []
    max_cameras = int(settings.get("max_cameras", 2))

    for camera in camera_source:
        if len(captures) >= max_cameras:
            break

        if camera["type"] == "url":
            url = make_url(camera)
            if url is None:
                p.warning(f"{camera['name']}Urlの生成失敗")
                continue
            p.success(f"生成成功 {camera['name']}のURL：{url}")
            p.info(f"URL:{camera['name']}に接続中")
        elif camera['type'] == "webcam":
            p.info(f"Webcam:{camera['name']}に接続中")

        
        #!tryopne関数入れといて俺

