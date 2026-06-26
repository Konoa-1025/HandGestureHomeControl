#lowLevel.py
#Norifumi Kondo
import cv2
import logPrint as p
import cameraManager as camera

def _startCas():
    p.info("切り替わりました。")
    camera.change_resolution("1280x720")
p.info("起動")