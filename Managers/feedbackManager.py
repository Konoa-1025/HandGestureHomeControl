
#? Managers/feedbackManager.py
#? Norifumi Konndo

import Utils.logger as p
import Feedback.sound as sound


last_combo_status = None
last_sound_type = None


def Initialization(settings):
    """
    feedbackManagerを初期化する。
    """

    global last_combo_status
    global last_sound_type

    p.info("feedbackManagerを初期化中")
    p.info("フィードバックファイル読み込み中")

    last_combo_status = None
    last_sound_type = None

    if not sound.Initialization(settings):
        p.error("サウンドシステムの初期化に失敗しました")
        return False

    sound.sound("open")

    p.success("feedbackManagerの初期化完了")
    return True


def feedback(sound_type, combo_status=None):
    """
    指定されたフィードバック音を再生する。

    combo_statusが指定されている場合、
    同じ音と同じ状態が続いている間は再生しない。

    使用例:
        feedback("start")
        feedback("beep", "combo_1")
        feedback("go", "completed")
        feedback("cancel", "failed")
    """

    global last_combo_status
    global last_sound_type

    # combo_statusがない場合は、通常どおり毎回再生する
    if combo_status is None:
        return play_feedback(sound_type)

    # 前回と音・コンボ状態が同じなら再生しない
    if (
        sound_type == last_sound_type
        and combo_status == last_combo_status
    ):
        return True

    result = play_feedback(sound_type)

    # 再生に成功した場合だけ、前回状態を更新する
    if result:
        last_sound_type = sound_type
        last_combo_status = combo_status

    return result


def play_feedback(sound_type):
    """
    サウンドを再生し、失敗時に警告を表示する。
    """

    if not sound.sound(sound_type):
        p.warning(
            f"フィードバック音を再生できませんでした: "
            f"{sound_type}"
        )
        return False

    return True


def reset():
    """
    重複再生防止用の状態をリセットする。

    新しいコンボを開始するときなどに使用する。
    """

    global last_combo_status
    global last_sound_type

    last_combo_status = None
    last_sound_type = None

    return True