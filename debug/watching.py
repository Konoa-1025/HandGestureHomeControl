import cv2

def debug(_frame):

    cv2.imshow("Debug", _frame)

    cv2.waitKey(1)

cv2.destroyAllWindows()