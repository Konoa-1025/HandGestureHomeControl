#? Managers/modelManager.py
#? Norifumi Kondo

import Utils.logger as p

import Models.mediapipe.highModel as mediapipeHighModel
import Models.mediapipe.lowModel as mediapipeLowModel

import Models.pipetrt.highmodel as pipetrtHighModel


low = 70
high = 90

backend = "mediapipe"

current_mode = "high"
old_mode = "high"


def Initialization(settings):
    global low
    global high
    global backend

    p.info("modelManagerを初期化中")

    try:
        backend = settings["model"]["backend"]

    except KeyError:
        p.error("model.backendの設定がありません")
        return False

    # =====================================
    # MediaPipe
    # =====================================

    if backend == "mediapipe":

        p.info("MediaPipe backendを使用します")

        low = settings["model"]["switch_threshold"]["cpu_percent"]["low"]

        high = settings["model"]["switch_threshold"]["cpu_percent"]["high"]

        # lowとhighの順番チェック
        if low >= high:
            p.error("model設定エラー")
            p.error("lowはhighより小さくしてください")
            return False

        # ヒステリシス幅チェック
        if high - low < 10:
            p.error("model設定エラー")
            p.error("ヒステリシス幅は10%以上必要です")
            p.error(
                f"現在 : {high - low}%"
            )
            return False

        p.info(
            "MediaPipe highModelを初期化中"
        )

        if not mediapipeHighModel.Initialization(
            settings
        ):
            p.error(
                "MediaPipe highModelの初期化に失敗しました"
            )
            return False

        p.info(
            "MediaPipe lowModelを初期化中"
        )

        if not mediapipeLowModel.Initialization(
            settings
        ):
            p.error(
                "MediaPipe lowModelの初期化に失敗しました"
            )
            return False

    # =====================================
    # PipeTRT
    # =====================================

    elif backend == "pipetrt":

        p.info("PipeTRT backendを使用します")

        p.info(
            "PipeTRT highModelを初期化中"
        )

        if not pipetrtHighModel.Initialization(
            settings
        ):
            p.error(
                "PipeTRT highModelの初期化に失敗しました"
            )
            return False

    # =====================================
    # 不明なbackend
    # =====================================

    else:
        p.error(
            f"不明なmodel backendです: {backend}"
        )
        return False

    p.success("modelManagerの初期化完了")

    return True


def model_selection(
    frame,
    select_mode="high"
):

    # =====================================
    # MediaPipe
    # =====================================

    if backend == "mediapipe":

        if select_mode == "low":
            return mediapipeLowModel.run(
                frame
            )

        return mediapipeHighModel.run(
            frame
        )

    # =====================================
    # PipeTRT
    # =====================================

    elif backend == "pipetrt":

        return pipetrtHighModel.run(
            frame
        )

    p.error(
        f"不明なmodel backendです: {backend}"
    )

    return {
        "is_hand": False,
        "hands": []
    }


def model_process(
    frame,
    cpu_usage_rate,
    gpu_usage_rate=None
):

    global current_mode
    global old_mode

    if frame is None:
        p.error("フレームがNoneです")

        return {
            "is_hand": False,
            "hands": []
        }

    # =====================================
    # MediaPipe
    # CPU負荷によってhigh / low切替
    # =====================================

    if backend == "mediapipe":

        if cpu_usage_rate >= high:

            current_mode = "low"

            if old_mode != current_mode:
                p.change(
                    "MediaPipe lowModel"
                )

                old_mode = current_mode

        elif cpu_usage_rate <= low:

            current_mode = "high"

            if old_mode != current_mode:
                p.change(
                    "MediaPipe highModel"
                )

                old_mode = current_mode

        return model_selection(
            frame,
            current_mode
        )

    # =====================================
    # PipeTRT
    # 現在はhighModel固定
    # =====================================

    elif backend == "pipetrt":

        return model_selection(
            frame,
            "high"
        )

    return {
        "is_hand": False,
        "hands": []
    }