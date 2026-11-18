
#? Cascades/lowCascade.py
#? Norifumi Konndo

import Utils.logger as p
import cv2

width = 640
height = 360


def Initialization(settings):
    global width,height

    p.info("lowCascadeを初期化中")
    width = settings["cascade"]["resolution"]["low"]["width"]
    height = settings["cascade"]["resolution"]["low"]["height"]

    if width == None or 0:
        p.error("widthの設定が間違えています。")
        return False
    if height == None or 0:
        p.error("heightの設定が間違えています。")
        return False

    p.success("lowCascadeの初期化完了")

    return True

def run(frame):
    frame = cv2.resize(frame, (width, height))

    frame = cv2.GaussianBlur(frame, (3, 3), 0)

    frame = cv2.flip(frame, 1)

    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

    return frame