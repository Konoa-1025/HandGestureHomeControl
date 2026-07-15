# appliancesManager.py
# Norifumi Konndo

import csv
from pathlib import Path

import utils.logPrint as p


_initialized = False
_appliances = []
_selected_appliance = None


def Initialization(_settings=None):
    global _initialized
    global _appliances
    global _selected_appliance

    p.info("初期化中")

    _settings = _settings or {}
    _appliance_settings = _settings.get("appliances", _settings)
    _combo_path = Path(
        _appliance_settings.get("combo_csv_path", "homeAppliances/combos.csv")
    )

    if not _combo_path.exists():
        raise FileNotFoundError(
            f"家電コンボCSVが見つかりません: {_combo_path}"
        )

    _appliances = _load_appliances(_combo_path)
    _selected_appliance = None

    p.info(
        f"家電を読み込みました: {len(_appliances)}件"
    )

    _initialized = True

    p.success("初期化成功")

    return True


def _load_appliances(_combo_path):
    _loaded_appliances = []
    _seen = set()

    with _combo_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as _file:

        _reader = csv.DictReader(_file)

        if _reader.fieldnames is None:
            return _loaded_appliances

        for _row in _reader:
            _device = (
                _row.get("device") or ""
            ).strip().upper()

            if not _device or _device in _seen:
                continue

            _seen.add(_device)
            _loaded_appliances.append(_device)

    return _loaded_appliances


def get_appliances():
    return _appliances.copy()


def get_selected_appliance():
    return _selected_appliance


def select_appliance(_appliance):
    global _selected_appliance

    if _appliance is None:
        _selected_appliance = None
        return True

    _normalized = str(_appliance).strip().upper()

    if _normalized not in _appliances:
        return False

    _selected_appliance = _normalized
    return True