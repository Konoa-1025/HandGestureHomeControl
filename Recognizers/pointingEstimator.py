
#? Recognizers/pointingEstimator.py
#? Norifumi Konndo

import Utils.logger as p
import math

min_vector_length = 0.5

def Initialization(settings):
    global min_vector_length

    p.info("pointingEstimatorを初期化中")

    min_vector_length = settings["recognition"]["direction_estimator"]["minimum_vector_length"]

    if min_vector_length is None:
        p.error("minimum_vector_lengthが正しくありません。")
        return False

    p.success("pointingEstimatorの初期化完了")
    return True

def abstract_abstract(angle): #!使用するならこっちの方が安定してます。
    if -22.5 <= angle < 22.5:
        return "RIGHT"
    elif 22.5 <= angle < 67.5:
        return "UP_RIGHT"
    elif 67.5 <= angle < 112.5:
        return "UP"
    elif 112.5 <= angle < 157.5:
        return "UP_LEFT"
    elif angle >= 157.5 or angle < -157.5:
        return "LEFT"
    elif -157.5 <= angle < -112.5:
        return "DOWN_LEFT"
    elif -112.5 <= angle < -67.5:
        return "DOWN"
    else:
        return "DOWN_RIGHT"

def specific_direction(hand_landmark):#!具体的な角度で正確性に欠けてます。
    mcp = hand_landmark[5]
    tip = hand_landmark[8]
    
    dx = tip["x"] - mcp["x"]
    dy = tip["y"] - mcp["y"]
    
    length = math.hypot(dx, dy)

    p.debug(
            f"人差し指ベクトル長: {length}, "
            f"最低値: {min_vector_length}"
        )
    
    if length < min_vector_length:
        return "UNKNOWN"
    
    # 画像ではyが下向きに増えるので、符号を反転
    angle = math.degrees(math.atan2(-dy, dx))
    return angle

def get_direction(hand_landmarks):
    hand_landmark = hand_landmarks["hands"][0]["landmarks"]

    angle = specific_direction(hand_landmark)

    if angle == "UNKNOWN":
        return {
            "angle": angle,
            "direction": "UNKNOWN"
        }

    direction = abstract_abstract(angle)

    return {
        "angle": angle,
        "direction": direction
    }