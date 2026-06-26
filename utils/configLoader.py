#utils/configLoader.py
#Norifumi Konndo
import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def load_config():
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"設定ファイルが見つかりません: {_CONFIG_PATH}"
        )

    with open(_CONFIG_PATH, "r", encoding="utf-8") as _file:
        return json.load(_file)