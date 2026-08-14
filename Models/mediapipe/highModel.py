
#? Models/cpu/highModel.py
#? Norifumi Kondo

import mediapipe as mp
import Utils.logger as p


initialized = False
hands_model = None


def Initialization(settings):
    global initialized
    global hands_model

    p.info("highModelを初期化中")

    try:
        high_settings = settings["model"]["profiles"]["high"]

        max_hands = high_settings["max_hands"]
        detection_confidence = high_settings["detection_confidence"]
        tracking_confidence = high_settings["tracking_confidence"]

        hands_model = mp.solutions.hands.Hands( # type: ignore #!pylanceのエラーは無視
            static_image_mode=False,
            max_num_hands=max_hands,
            model_complexity=1,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )

        initialized = True

        p.success("highModelの初期化完了")
        return True

    except KeyError as error:
        p.error(
            f"highModelの設定が不足しています: {error}"
        )
        return False

    except Exception as error:
        p.error(
            f"highModelの初期化に失敗しました: {error}"
        )
        return False


def run(frame):
    global hands_model

    if not initialized or hands_model is None:
        p.error("highModelが初期化されていません")

        return {
            "is_hand": False,
            "hands": []
        }

    if frame is None:
        p.error("highModelに空の画像が渡されました")

        return {
            "is_hand": False,
            "hands": []
        }

    try:
        result = hands_model.process(frame)

        hands = []

        if not result.multi_hand_landmarks:
            return {
                "is_hand": False,
                "hands": []
            }

        for hand_index, hand_landmarks in enumerate(
            result.multi_hand_landmarks
        ):
            landmarks = []

            for landmark_index, landmark in enumerate(
                hand_landmarks.landmark
            ):
                landmarks.append({
                    "id": landmark_index,
                    "x": landmark.x,
                    "y": landmark.y,
                    "z": landmark.z
                })

            handedness = None
            handedness_score = None

            if (
                result.multi_handedness
                and hand_index < len(result.multi_handedness)
            ):
                classification = (
                    result
                    .multi_handedness[hand_index]
                    .classification[0]
                )

                handedness = classification.label
                handedness_score = classification.score

            hands.append({
                "hand_index": hand_index,
                "handedness": handedness,
                "handedness_score": handedness_score,
                "landmarks": landmarks
            })

        return {
            "is_hand": len(hands) > 0,
            "hands": hands
        }

    except Exception as error:
        p.error(
            f"highModelの推論中にエラーが発生しました: {error}"
        )

        return {
            "is_hand": False,
            "hands": []
        }