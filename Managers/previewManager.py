
#? Managers/previweManager.py
#? Norifumi Konndo

import cv2
import Utils.logger as p
import csv

appliances = []
window_created = False
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

def show_frame_detail(frame):
    global window_created

    if frame is None:
        return True

    if not window_created:
        return False

    try:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        draw_text(
            frame,
            select_appliance_abstract("UP_LEFT"),
            "top_left"
        )

        draw_text(
            frame,
            select_appliance_abstract("UP"),
            "top"
        )

        draw_text(
            frame,
            select_appliance_abstract("UP_RIGHT"),
            "top_right"
        )

        draw_text(
            frame,
            select_appliance_abstract("LEFT"),
            "left"
        )

        draw_text(
            frame,
            select_appliance_abstract("CENTER"),
            "center"
        )

        draw_text(
            frame,
            select_appliance_abstract("RIGHT"),
            "right"
        )

        draw_text(
            frame,
            select_appliance_abstract("DOWN_LEFT"),
            "bottom_left"
        )

        draw_text(
            frame,
            select_appliance_abstract("DOWN"),
            "bottom"
        )

        draw_text(
            frame,
            select_appliance_abstract("DOWN_RIGHT"),
            "bottom_right"
        )

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

def select_appliance_abstract(direction):
    for appliance in appliances:
        if appliance["abstract"] == direction:
            return appliance["display_name"]

    return "None"