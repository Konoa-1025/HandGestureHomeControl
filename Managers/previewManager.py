
#? Managers/previweManager.py
#? Norifumi Konndo

import cv2
import Utils.logger as p
import csv
import numpy as np
import Managers.appliancesManager as appliance_manager
import Managers.positionManager as position
import Recognizers.pointingEstimator as pointing
import Recognizers.gestureStabilizer as stabilizer

appliances = []
window_created = False
last_key = -1
center_edit = False
centers_dirty = False
edit_devices = []
edit_index = 0
preview_size = (960, 540)
window_name = "HandGestureHomeControl Preview"


def Initialization(settings):
    name: str = "HandGestureHomeControl Preview"
    width: int = 960
    height: int = 540

    # window_name = config["preview"]["window_name"]
    # window_width = config["preview"]["width"]
    # window_height = config["preview"]["height"]

    global window_created
    global window_name
    global center_edit, centers_dirty
    center_edit = False
    centers_dirty = False
    
    if pointing.enabled:
        width, height = 1320, 710

    try:
        window_name = name

        # WINDOW_NORMALを指定するとウィンドウサイズを変更できる
        cv2.namedWindow(window_name,cv2.WINDOW_NORMAL)
        # 起動時のウィンドウサイズ
        cv2.resizeWindow(window_name,width,height)
        window_created = True
        p.success("プレビューウィンドウの初期化完了")

        global appliances
        
        p.info("appliancesManagerを初期化中")
        
        csv_path = settings["home_appliances"]["files"]["appliancesmap"]
        
        try:
            with open(csv_path, "r", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
    
                appliances = []
        
                for row in reader:
                    if not row["device"]:
                        continue
        
                    appliances.append(row)
        
        except Exception as error:
            p.error(f"CSVの読み込みに失敗しました: {error}")
            return False
        
        p.success(f"プレビュー家電の読み込み完了 ({len(appliances)}件)")
        return True
    except cv2.error as error:
        p.error(f"プレビューウィンドウの初期化に失敗しました: {error}")
        return False


def show_frame_simple(frame):

    global window_created, last_key

    if frame is None:
        return True

    if not window_created:
            return False

    try:
        frame = cv2.cvtColor(frame,cv2.COLOR_RGB2BGR)

        cv2.imshow(
            window_name,
            frame
        )

        key = cv2.waitKey(1) & 0xFF
        last_key = key

        if key == ord("q") or key == 27:
            return False

        # ユーザーが×ボタンで閉じた場合
        window_status = cv2.getWindowProperty(
            window_name,
            cv2.WND_PROP_VISIBLE
        )

        if window_status < 1:
            return False

        return True

    except cv2.error as error:
        p.error(f"フレーム表示中にエラーが発生しました: {error}")
        return False

def show_frame_detail(frame, current_position=None):
    global window_created, last_key

    if frame is None:
        return True

    if not window_created:
        return False

    try:
        frame = draw_detail(frame, current_position)
        cv2.imshow(window_name, frame)

        key = cv2.waitKey(1) & 0xFF
        last_key = key

        if key == ord("q") or key == 27:
            return False

        window_status = cv2.getWindowProperty(
            window_name,
            cv2.WND_PROP_VISIBLE
        )

        if window_status < 1:
            return False

        return True

    except cv2.error as error:
        p.error(f"フレーム表示中にエラーが発生しました: {error}")
        return False

def close_window():
    """
    プレビュー ウィンドウを閉じる
    """

    global window_created

    if not window_created:
        return

    try:
        cv2.destroyWindow(window_name)
        cv2.waitKey(1)

    except cv2.error:
        pass

    window_created = False

import cv2


def draw_text(frame, text, position):

    margin = 20
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 2.0
    thickness = 2

    (text_width, text_height), baseline = cv2.getTextSize(
        text,
        font,
        scale,
        thickness
    )

    frame_height, frame_width = frame.shape[:2]

    #?座標計算

    if position == "top_left":
        x = margin
        y = margin + text_height

    elif position == "top":
        x = (frame_width - text_width) // 2
        y = margin + text_height

    elif position == "top_right":
        x = frame_width - text_width - margin
        y = margin + text_height

    elif position == "left":
        x = margin
        y = frame_height // 2

    elif position == "center":
        x = (frame_width - text_width) // 2
        y = frame_height // 2

    elif position == "right":
        x = frame_width - text_width - margin
        y = frame_height // 2

    elif position == "bottom_left":
        x = margin
        y = frame_height - margin

    elif position == "bottom":
        x = (frame_width - text_width) // 2
        y = frame_height - margin

    elif position == "bottom_right":
        x = frame_width - text_width - margin
        y = frame_height - margin

    else:
        return

    #?背景

    padding = 8

    cv2.rectangle(
        frame,
        (
            x - padding,
            y - text_height - padding
        ),
        (
            x + text_width + padding,
            y + baseline + padding
        ),
        (10, 10, 10),
        -1
    )

    #?文字

    cv2.putText(frame,text,(x, y),font,scale,(255, 255, 255),thickness,cv2.LINE_AA)

def select_appliance_abstract(direction, current_position=None):
    if appliance_manager.use_position_map:
        appliance = appliance_manager.select_appliance_abstract(direction, current_position)
        return appliance["display_name"] if appliance else "None"
    for appliance in appliances:
        if appliance["abstract"] == direction:
            return appliance["display_name"]
    return "None"


def draw_detail(frame, current_position=None):
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    draw_text(
        frame,
        select_appliance_abstract("UP_LEFT", current_position),
        "top_left"
    )

    draw_text(
        frame,
        select_appliance_abstract("UP", current_position),
        "top"
    )

    draw_text(
        frame,
        select_appliance_abstract("UP_RIGHT", current_position),
        "top_right"
    )

    draw_text(
        frame,
        select_appliance_abstract("LEFT", current_position),
        "left"
    )

    draw_text(
        frame,
        select_appliance_abstract("CENTER", current_position),
        "center"
    )

    draw_text(
        frame,
        select_appliance_abstract("RIGHT", current_position),
        "right"
    )

    draw_text(
        frame,
        select_appliance_abstract("DOWN_LEFT", current_position),
        "bottom_left"
    )

    draw_text(
        frame,
        select_appliance_abstract("DOWN", current_position),
        "bottom"
    )

    draw_text(
        frame,
        select_appliance_abstract("DOWN_RIGHT", current_position),
        "bottom_right"
    )

    if position.debug:
        for name, points in position.scaled_polygons(frame.shape).items():
            color = (0, 255, 0) if name == current_position else (0, 200, 255)
            points = points.round().astype("int32")
            cv2.polylines(frame, [points], True, color, 2)
            cv2.putText(frame, name, tuple(points.mean(axis=0).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        for box, color in ((position.bounding_box, (255, 160, 0)), (position.position_box, (255, 0, 255))):
            if box is not None:
                left, top, right, bottom = map(round, box)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, f"CURRENT POSITION: {current_position}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    return frame


def draw_status_text(frame, text, x, y, width, color=(220, 225, 230), scale=0.5):
    text = "--" if text is None else str(text)
    if cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)[0][0] > width:
        while text and cv2.getTextSize(text + "...", cv2.FONT_HERSHEY_SIMPLEX, scale, 1)[0][0] > width:
            text = text[:-1]
        text += "..."
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)


def draw_pointing(frame, status):
    global preview_size
    height, width = frame.shape[:2]
    scale = min(960 / width, 540 / height, 1)
    w, h = round(width * scale), round(height * scale)
    preview_size = (w, h)
    panel_x = w + 280
    display = np.full((max(h + 300, 840), panel_x + 360, 3), 28, dtype=np.uint8)
    display[230:230+h, 140:140+w] = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), (w, h))
    result = status.get("point_data") or {}
    canvas = display[:, :panel_x]

    def screen(x, y):
        return (round(140 + x * w), round(230 + y * h))

    origin = result.get("origin")
    start = screen(origin[0] / width, origin[1] / height) if origin is not None else None
    for device, (x, y) in pointing.centers.items():
        center = screen(x, y)
        color = (152, 211, 147) if result.get("candidate") == device else (107, 187, 236)
        if start is not None:
            cv2.line(canvas, start, center, color, 1, cv2.LINE_AA)
        cv2.drawMarker(canvas, center, color, cv2.MARKER_CROSS, 20, 2)
        angle = result.get("angles", {}).get(device)
        label = "ALL LIGHTS / CEILING" if device == "LIGHT" else device
        if angle is not None:
            label += f": {angle:.1f} deg"
        label_x = max(8, min(center[0] + 10, panel_x - 240))
        draw_status_text(canvas, label, label_x, max(125, min(center[1], display.shape[0] - 15)), panel_x - label_x - 8, color)
    tip = result.get("tip")
    if start is not None and tip is not None:
        vector = np.array([(tip[0] - origin[0]) * w / width, (tip[1] - origin[1]) * h / height])
        length = np.linalg.norm(vector)
        if length >= 1:
            end = tuple(np.rint(np.array(start) + vector / length * 2 * max(w, h)).astype(int))
            cv2.arrowedLine(canvas, start, end, (231, 211, 104), 3, cv2.LINE_AA, tipLength=0.03)
        cv2.circle(canvas, start, 5, (240, 240, 240), -1)
        cv2.circle(canvas, screen(tip[0] / width, tip[1] / height), 5, (231, 211, 104), -1)

    cv2.rectangle(canvas, (0, 0), (panel_x, 105), (23, 22, 20), -1)
    draw_status_text(canvas, "HGHC / POINTING PREVIEW", 20, 30, panel_x - 40, scale=0.65)
    mode = status.get("mode", "SIMULATION")
    playback = "PAUSED" if status.get("paused") else "PLAYING"
    draw_status_text(canvas, f"{mode} | {playback} | CYAN: FINGER / GOLD: TARGET / GREEN: CANDIDATE", 20, 56, panel_x - 40, scale=0.43)
    controls = "Space: pause / N: next frame / Q, Esc: quit"
    if center_edit:
        controls = f"Edit: {edit_devices[edit_index]} {'* UNSAVED' if centers_dirty else ''} / Click: center / [ ]: device / S: save / X: remove"
    draw_status_text(canvas, controls, 20, 84, panel_x - 40, scale=0.43)

    cv2.rectangle(display, (panel_x, 0), (display.shape[1], display.shape[0]), (31, 27, 23), -1)
    elapsed = stabilizer.hold_elapsed
    best_angle = result.get("best_angle")
    angle_text = "--" if best_angle is None else f"{best_angle:.1f} / {pointing.max_angle_degrees:g} deg"
    remaining = status.get("combo_remaining")
    rows = [
        ("HGHC / STATUS", mode),
        ("INPUT", f"{status.get('input', '--')} / FRAME {status.get('frame_index', '--')}"),
        ("FPS", f"{status.get('fps', 0):.1f}"),
        ("HAND", status.get("hand", "DETECTED" if origin is not None else "NONE")),
        ("GESTURE", status.get("gesture")),
        ("CONFIRMED", status.get("confirmed_gesture")),
        ("TARGET", result.get("candidate")),
        ("ANGLE", angle_text),
        ("HOLD", f"{elapsed:.2f} / {pointing.hold_seconds:.2f} s"),
        ("STATE", status.get("state")),
        ("SELECTED", status.get("selected")),
        ("COMBO", " > ".join(status.get("combo_history", [])) or "--"),
        ("TIME LEFT", "--" if remaining is None else f"{remaining:.1f} s"),
        ("LAST ACTION", status.get("last_action")),
        ("RESULT", status.get("action_status")),
        ("CHECK", result.get("reason")),
        ("NEAREST", result.get("best_target")),
        ("FINGER / MIN", "--" if result.get("finger_length_px") is None else f"{result['finger_length_px']:.1f} / {result['min_finger_length_px']:.1f} px")
    ]
    for index, (label, value) in enumerate(rows):
        y = 32 + index * 37
        draw_status_text(display, label, panel_x + 16, y, 112, scale=0.4)
        draw_status_text(display, value, panel_x + 130, y, 215, scale=0.47)
    draw_status_text(display, "SENT = command sent, not device confirmation", panel_x + 16, 707, 328, scale=0.34)
    for index, event in enumerate(status.get("history", [])[:5]):
        draw_status_text(display, event, panel_x + 16, 741 + index * 22, 328, scale=0.43)
    return display


def show_frame_pointing(frame, status):
    global last_key
    if frame is None:
        return True
    if not window_created:
        return False
    try:
        cv2.imshow(window_name, draw_pointing(frame, status))
        last_key = cv2.waitKey(20 if status.get("paused") else 1) & 0xFF
        return last_key not in (ord("q"), 27) and cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) >= 1
    except cv2.error as error:
        p.error(f"指差しプレビューを表示できませんでした: {error}")
        return False


def start_center_edit():
    global center_edit, edit_devices, edit_index, centers_dirty
    center_edit = True
    centers_dirty = False
    edit_devices = list(dict.fromkeys(["AIRCON", "LIGHT", "AIRPURI", "BRAIND"] + [item["device"] for item in appliance_manager.appliances]))
    edit_index = 0
    cv2.setMouseCallback(window_name, edit_center_click)


def edit_center_click(event, x, y, flags, param):
    global centers_dirty
    w, h = preview_size
    if event != cv2.EVENT_LBUTTONDOWN or y < 105 or not 0 <= x < w + 280 or y >= h + 300:
        return
    point = ((x - 140) / w, (y - 230) / h)
    if not all(-1 <= value <= 2 for value in point):
        return
    pointing.centers[edit_devices[edit_index]] = point
    centers_dirty = True
    stabilizer.reset_target()


def edit_center_key(key):
    global edit_index, centers_dirty
    if key in (ord("["), ord("]")):
        edit_index = (edit_index + (1 if key == ord("]") else -1)) % len(edit_devices)
    elif key == ord("x"):
        pointing.centers.pop(edit_devices[edit_index], None)
        centers_dirty = True
        stabilizer.reset_target()
    elif key == ord("s"):
        try:
            pointing.save_centers()
            centers_dirty = False
            p.success("家電中心を保存しました")
        except OSError as error:
            p.error(f"家電中心を保存できませんでした: {error}")
