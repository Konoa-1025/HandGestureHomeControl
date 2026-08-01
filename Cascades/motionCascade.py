
#? Cascades/motionCascade.py
#? Norifumi Konndo

import Utils.logger as p
import cv2

before_gray = None
threshold = 25  #!差分の感度(大きいほど鈍感)
minimum_changed_pixels = 1000   #!動きと判断するピクセル数

width = 640
height = 360

def Initialization(settings):
    global threshold,minimum_changed_pixels

    p.info("motionCascadeを初期化中")

    threshold = settings["cascade"]["resolution"]["motion"]["threshold"]
    minimum_changed_pixels = settings["cascade"]["resolution"]["motion"]["minimum_changed_pixels"]

    p.success("motionCascadeの初期化完了")

    return True

def is_human(frame):
    global before_gray

    # リサイズ
    frame = cv2.resize(frame, (width, height))

    # グレースケール
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 初回だけ保存
    if before_gray is None:
        before_gray = gray
        return False

    # 前回との差分
    diff = cv2.absdiff(before_gray, gray)

    # 白黒画像にする
    _, diff = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

    # 白い画素数を数える
    changed_pixels = cv2.countNonZero(diff)

    # 今回の画像を保存
    before_gray = gray

    # 人がいるか判定
    if changed_pixels >= minimum_changed_pixels:
        return True
    return False