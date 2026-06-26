#highLevel.py
#Norifumi Kondo
import cv2
import logPrint as p
import cameraManager as camera

def _startCas():
    p.info("切り替わりました。")
    camera.change_resolution("1920x1080")
p.info("起動")