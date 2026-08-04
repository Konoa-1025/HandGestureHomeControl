
#? Feedback/sound.py
#? Norifumi Konndo

from pathlib import Path

import pygame

import Utils.logger as p


sound_type = "silent"
sound_volume = 1.0
sound_enabled = True

loaded_sounds = {}


def Initialization(settings):
    """
    サウンドシステムを初期化する。

    settings:
        config.jsonを読み込んだ辞書
    """

    global sound_type
    global sound_volume
    global sound_enabled
    global loaded_sounds

    p.info("サウンドシステムを初期化中")

    try:
        sound_config = settings["feedback"]["sound"]

        sound_enabled = sound_config.get("enabled", True)
        sound_type = sound_config.get("type", "silent")
        sound_volume = sound_config.get("volume", 1.0)

        if not sound_enabled:
            p.info("サウンドシステムは無効に設定されています")
            return True

        # silentにも音声ファイルがあるため、通常タイプとして扱う
        supported_sound_types = (
            "magic",
            "normal",
            "silent"
        )

        if sound_type not in supported_sound_types:
            p.error(
                f"未対応のサウンドタイプです: {sound_type}"
            )
            return False

        pygame.mixer.init()

        # Feedback/sound.pyからプロジェクト直下へ戻り、
        # Assets/sounds/{sound_type}を参照する
        sound_directory = (
            Path(__file__).resolve().parent.parent
            / "Assets"
            / "sounds"
            / sound_type
        )

        sound_files = sound_config["files"]

        loaded_sounds = {}

        for sound_name, file_name in sound_files.items():
            file_path = sound_directory / file_name

            if not file_path.exists():
                p.error(
                    f"サウンドファイルが見つかりません: "
                    f"{file_path}"
                )
                return False

            loaded_sound = pygame.mixer.Sound(
                str(file_path)
            )

            loaded_sound.set_volume(sound_volume)
            loaded_sounds[sound_name] = loaded_sound

        p.success(
            f"サウンドシステムの初期化完了: "
            f"{sound_type}"
        )

        return True

    except KeyError as error:
        p.error(
            f"サウンド設定が不足しています: {error}"
        )
        return False

    except pygame.error as error:
        p.error(
            f"pygameのサウンド初期化に失敗しました: "
            f"{error}"
        )
        return False

    except Exception as error:
        p.error(
            f"サウンドシステムの初期化中にエラー: "
            f"{error}"
        )
        return False


def sound(sound_name):
    """
    指定された種類の効果音を再生する。

    使用例:
        sound("start")
        sound("beep")
        sound("go")
        sound("cancel")
        sound("open")
    """

    if not sound_enabled:
        return True

    if not pygame.mixer.get_init():
        return False

    if sound_name == "start":
        return start()

    if sound_name == "beep":
        return beep()

    if sound_name == "go":
        return go()

    if sound_name == "cancel":
        return cancel()

    if sound_name == "open":
        return app_open()

    p.error(
        f"存在しないサウンドです: {sound_name}"
    )
    return False


def start():
    """
    指差しによって家電が選択されたときの音。
    """

    return play_sound("start")


def beep():
    """
    コンボ入力が継続したときの音。
    """

    return play_sound("beep")


def go():
    """
    コンボが確定したときの音。
    """

    return play_sound("go")


def cancel():
    """
    認識失敗や操作キャンセル時の音。
    """

    return play_sound("cancel")

def app_open():
    """
    アプリケーションが起動したときの音。
    """

    return play_sound("open")


def play_sound(sound_name):
    """
    読み込み済みの効果音を再生する。
    """

    loaded_sound = loaded_sounds.get(sound_name)

    if loaded_sound is None:
        p.error(
            f"サウンドが読み込まれていません: "
            f"{sound_name}"
        )
        return False

    try:
        loaded_sound.play()
        return True

    except pygame.error as error:
        p.error(
            f"サウンドの再生に失敗しました: "
            f"{sound_name} / {error}"
        )
        return False


def stop():
    """
    現在再生中のすべての効果音を停止する。
    """

    if not pygame.mixer.get_init():
        return True

    pygame.mixer.stop()
    return True


def shutdown():
    """
    pygameのサウンドシステムを終了する。
    """

    if pygame.mixer.get_init():
        pygame.mixer.stop()
        pygame.mixer.quit()

    p.info("サウンドシステムを終了しました")

    return True