#? Models/gpu/highModel.py
#? Norifumi Kondo

import pipetrt
import Utils.logger as p


initialized = False
hands_model = None


def Initialization(settings):
    global initialized
    global hands_model

    p.info("PipeTRT highModelを初期化中")

    try:
        high_settings = settings["model"]["profiles"]["high"]

        # 現在のPipeTRTでは主にこの2つを指定
        model = high_settings.get("model", "full")
        precision = high_settings.get("precision", "fp16")

        hands_model = pipetrt.HandLandmarker(
            model=model,
            precision=precision
        )

        initialized = True

        p.success("PipeTRT highModelの初期化完了")
        return True

    except KeyError as error:
        p.error(
            f"PipeTRT highModelの設定が不足しています: {error}"
        )
        return False

    except Exception as error:
        p.error(
            f"PipeTRT highModelの初期化に失敗しました: {error}"
        )
        return False


def run(frame):
    global hands_model

    if not initialized or hands_model is None:
        p.error("PipeTRT highModelが初期化されていません")

        return {
            "is_hand": False,
            "hands": []
        }

    if frame is None:
        p.error("PipeTRT highModelに空の画像が渡されました")

        return {
            "is_hand": False,
            "hands": []
        }

    try:
        result = hands_model.detect(frame)

        hands = []

        if (
            result.hand_landmarks is None
            or len(result.hand_landmarks) == 0
        ):
            return {
                "is_hand": False,
                "hands": []
            }

        frame_height, frame_width = frame.shape[:2]

        landmarks = []

        for landmark_index, landmark in enumerate(
            result.hand_landmarks
        ):
            x = float(landmark[0]) / frame_width
            y = float(landmark[1]) / frame_height
            z = float(landmark[2])

            landmarks.append({
                "id": landmark_index,
                "x": x,
                "y": y,
                "z": z
            })

        hands.append({
            "hand_index": 0,

            # PipeTRT v0.1.2では
            # handedness判定はまだ無い
            "handedness": None,
            "handedness_score": None,

            "landmarks": landmarks
        })

        return {
            "is_hand": True,
            "hands": hands
        }

    except Exception as error:
        p.error(
            f"PipeTRT highModelの推論中にエラーが発生しました: {error}"
        )

        return {
            "is_hand": False,
            "hands": []
        }


def close():
    global hands_model
    global initialized

    if hands_model is not None:
        try:
            hands_model.close()

        except Exception as error:
            p.warning(
                f"PipeTRT highModelの終了処理中にエラー: {error}"
            )

    hands_model = None
    initialized = False