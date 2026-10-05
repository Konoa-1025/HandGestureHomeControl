
#? Managers/previweManager.py
#? Norifumi Konndo

import cv2
import Utils.logger as p
import Managers.appliancesManager as appliances_manager
window_created = False
last_key = -1
last_display = None
window_name = "HandGestureHomeControl Preview"


def Initialization(settings):
    name: str = "HandGestureHomeControl Preview"
    width: int = 1320
    height: int = 710

    # window_name = config["preview"]["window_name"]
    # window_width = config["preview"]["width"]
    # window_height = config["preview"]["height"]

    global window_created
    global window_name
    
    try:
        window_name = name

        # WINDOW_NORMALを指定するとウィンドウサイズを変更できる
        cv2.namedWindow(window_name,cv2.WINDOW_NORMAL)
        # 起動時のウィンドウサイズ
        cv2.resizeWindow(window_name,width,height)
        window_created = True
        p.success("プレビューウィンドウの初期化完了")

        return True
    except cv2.error as error:
        p.error(f"プレビューウィンドウの初期化に失敗しました: {error}")
        return False


def show_frame_simple(frame):

    global window_created

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

def show_frame_detail(frame, position_state=None, current_position=None):
    global window_created

    if frame is None:
        return True

    if not window_created:
        return False

    try:
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

        draw_position_debug(frame, position_state)
        cv2.imshow(window_name, frame)

        key = cv2.waitKey(1) & 0xFF

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

    # --------------------
    # 座標計算
    # --------------------

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

    # --------------------
    # 背景
    # --------------------

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

    # --------------------
    # 文字
    # --------------------

    cv2.putText(frame,text,(x, y),font,scale,(255, 255, 255),thickness,cv2.LINE_AA)

def select_appliance_abstract(direction, current_position=None):
    appliance = appliances_manager.select_appliance_abstract(direction, current_position)
    return appliance["display_name"] if appliance else "None"


def draw_position_debug(frame, state):
    """表示用BGR画像だけに描画し、認識に渡す画像は変更しない。"""
    if state is None:
        return
    for name, polygon in state.tatami_map.scaled_polygons(frame.shape).items():
        points = polygon.round().astype("int32")
        color = (0, 255, 0) if name == state.current_position else (0, 200, 255)
        cv2.polylines(frame, [points], True, color, 2)
        center = tuple(points.mean(axis=0).astype(int))
        cv2.putText(frame, name, center, cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    for box, color in ((state.bounding_box, (255, 160, 0)), (state.position_box, (255, 0, 255))):
        if box is not None:
            x1, y1, x2, y2 = map(round, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    text = f"CURRENT POSITION: {state.current_position or 'None'}"
    cv2.putText(frame, text, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 5)
    cv2.putText(frame, text, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)


def show_frame_pointing(frame, state, status=None):
    from Feedback.pointingPreview import draw_preview
    global last_key, last_display
    if not window_created:
        return False
    status = status or {}
    last_display = draw_preview(frame, state.centers, state.result, '', status.get('paused', False), state.trial, live=True, status=status)
    cv2.imshow(window_name, last_display)
    last_key = cv2.waitKey(20 if status.get('paused') else 1) & 0xFF
    return last_key not in (ord('q'), 27) and cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) >= 1
