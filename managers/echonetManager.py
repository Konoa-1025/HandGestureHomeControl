# echonetManager.py
# Norifumi Konndo

import threading
import time

import utils.logPrint as p
from EchonetLite.EchonetLite import EchonetLite, PDCEDT


_initialized = False
_el = None
_devices = {}


def _on_set(ip, tid, seoj, deoj, esv, opc, epc, pdcedt):
    return True


def _on_get(ip, tid, seoj, deoj, esv, opc, epc, pdcedt):
    return True


def _request_property_maps(ip, eoj_list):
    for eoj in eoj_list:
        if _el is None:
            return

        eoj_text = _el.getHexString(eoj)

        p.info(
            f"プロパティマップ取得要求: "
            f"IP={ip} EOJ={eoj_text}"
        )

        try:
            _el.sendGetPropertyMap(ip, eoj)

        except Exception as error:
            p.error(
                f"プロパティマップ取得要求に失敗: "
                f"IP={ip} EOJ={eoj_text} "
                f"エラー={error}"
            )

        # 連続送信によるパケット欠落を避ける
        time.sleep(0.2)


def _on_inf(
    ip,
    tid,
    seoj,
    deoj,
    esv,
    opc,
    epc,
    pdcedt
):
    global _devices

    seoj_text = _el.getHexString(seoj)
    epc_text = _el.getHexString(epc)
    edt_text = _el.getHexString(pdcedt.edt)

    if ip not in _devices:
        _devices[ip] = {}

    if seoj_text not in _devices[ip]:
        _devices[ip][seoj_text] = {}

    _devices[ip][seoj_text][epc_text] = edt_text

    p.info(
        f"ECHONET Lite受信: "
        f"IP={ip} EOJ={seoj_text} "
        f"EPC={epc_text} EDT={edt_text}"
    )

    # D5 / D6 = インスタンスリスト
    if epc in (0xD5, 0xD6) and pdcedt.edt:
        count = pdcedt.edt[0]
        index = 1
        eoj_list = []

        p.info(
            f"ECHONET Liteオブジェクト一覧を受信: "
            f"IP={ip} 件数={count}"
        )

        for _ in range(count):
            eoj = pdcedt.edt[index:index + 3]
            index += 3

            if len(eoj) != 3:
                p.warning(
                    f"不正なEOJを受信しました: {eoj}"
                )
                continue

            eoj_list.append(eoj)

            p.info(
                f"ECHONET Lite機器検出: "
                f"IP={ip} EOJ={_el.getHexString(eoj)}"
            )

        threading.Thread(
            target=_request_property_maps,
            args=(ip, eoj_list),
            daemon=True
        ).start()

    return True


def Initialization(settings=None):
    global _initialized
    global _el
    global _devices

    if _initialized:
        p.info("echonetManagerは既に初期化されています")
        return True

    p.info("echonetManagerを初期化中")

    _devices = {}

    try:
        _el = EchonetLite([
            [0x05, 0xFF, 0x01]
        ])

        _el.begin(
            _on_set,
            _on_get,
            _on_inf
        )

        _el.sendMultiOPC1(
            _el.EOJ_NodeProfile,
            _el.EOJ_NodeProfile,
            _el.GET,
            0xD6,
            PDCEDT([0])
        )

    except Exception as error:
        p.error(
            f"echonetManagerの初期化に失敗しました: "
            f"{error}"
        )

        _el = None
        _initialized = False
        return False

    _initialized = True

    p.success("echonetManagerの初期化成功")
    p.info("ECHONET Lite機器探索を開始しました")

    return True


def get_devices():
    return _devices.copy()