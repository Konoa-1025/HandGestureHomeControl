#cascades/highCascade.py
#Norifumi Kondo
import cv2
import utils.logPrint as p
import managers.cameraManager as camera

def _startCas():
    p.info("切り替わりました。")
    camera.change_resolution("1920x1080")
p.info("起動")