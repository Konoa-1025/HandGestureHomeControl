# tcpResponse.py
# Mac / Jetson 側で動作するTCPクライアント
# Windows側のTCPサーバーへ接続し、同じ接続で受信・返信する

import json
import os
import socket
import threading
import time
import lz4.frame

import utils.logPrint as p

# ログ/データファイルの保存・参照先ディレクトリ
DATA_DIRECTORY = "research_logs"

_client_socket = None
_client_file = None
_client_thread = None
_is_running = False

_SOCKET_LOCK = threading.Lock()


# --------------------------------------------------
# ヘルパー関数: JSON / JSONL ファイルの取得・解析
# --------------------------------------------------

def _get_json_file_names():
    """
    DATA_DIRECTORY 内の .jsonl (.json) ファイル名一覧を取得し、降順で返す。
    """
    if not os.path.isdir(DATA_DIRECTORY):
        return []

    file_names = []

    for file_name in os.listdir(DATA_DIRECTORY):
        ext = os.path.splitext(file_name)[1].lower()
        if ext in [".jsonl", ".json"]:
            file_names.append(file_name)

    # 降順ソート（新しいファイルが上に来るように）
    file_names.sort(reverse=True)

    return file_names


def _get_json_file_info(file_name):
    """
    指定された JSONL / JSON ファイルを開き、ファイル名・実験ID・タイムスタンプを抽出して返す。
    """
    # ディレクトリトラバーサル防止（パス指定を除外してファイル名のみ使用）
    safe_file_name = os.path.basename(file_name)

    if safe_file_name != file_name:
        raise ValueError("不正なファイル名です。")

    file_path = os.path.join(DATA_DIRECTORY, safe_file_name)

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"ファイルが見つかりません: {safe_file_name}")

    json_data = {}

    with open(file_path, "r", encoding="utf-8") as file:
        # JSONLファイル対応：1行目を読み込んでパースを試みる
        first_line = file.readline().strip()
        if first_line:
            try:
                json_data = json.loads(first_line)
            except json.JSONDecodeError:
                # 1行目で読み込めない場合はファイル全体でのロードを試行
                file.seek(0)
                json_data = json.load(file)

    # JSON構造のネストの違いを吸収
    data = json_data.get("data", json_data)
    experiment = data.get("experiment", {})

    experiment_id = (
        data.get("experiment_id")
        or experiment.get("experiment_id")
        or experiment.get("id")
        or json_data.get("experiment_id")
        or ""
    )

    timestamp = (
        data.get("timestamp")
        or json_data.get("timestamp")
        or ""
    )

    return {
        "file_name": safe_file_name,
        "experiment_id": experiment_id,
        "timestamp": timestamp
    }


def _send_file_lz4_stream(windows_ip, transfer_port, transfer_id, file_path):
    """
    【追加箇所】
    Port 6005 (transfer_port) に接続し、
    [1行JSONヘッダー + \n] -> [LZ4Frameバイナリデータ] をストリーミング送信する。
    """
    file_name = os.path.basename(file_path)
    original_size = os.path.getsize(file_path)

    sock = None
    try:
        p.info(f"転送用ソケット接続中: {windows_ip}:{transfer_port}", "tcpResponse")

        # 1. Port 6005 へ接続
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        sock.connect((windows_ip, transfer_port))
        sock.settimeout(None)

        # 2. ヘッダー送信 (1行JSON + \n)
        header = {
            "type": "file_transfer",
            "transfer_id": transfer_id,
            "file_name": file_name,
            "compression": "lz4",
            "original_size": original_size
        }
        header_text = json.dumps(header, ensure_ascii=False, separators=(",", ":")) + "\n"
        sock.sendall(header_text.encode("utf-8"))

        p.info(f"ファイル転送開始 (LZ4ストリーム): {file_name} ({original_size} bytes)", "tcpResponse")

        # 3. 1MBずつ読み込みながら LZ4 圧縮ストリームで送信
        sock_file = sock.makefile("wb")

        try:
            with open(file_path, "rb") as source:
                # lz4.frame でソケットの書き込みストリームを包む
                with lz4.frame.open(sock_file, mode="wb") as compressed:
                    while True:
                        chunk = source.read(1024 * 1024)  # 1MB単位
                        if not chunk:
                            break
                        compressed.write(chunk)

            # LZ4 フッターを確定させてバッファを吐き出す
            sock_file.flush()
        finally:
            sock_file.close()

        p.success(f"ファイル転送完了: {file_name}", "tcpResponse")

    except Exception as e:
        p.error(f"ファイル転送エラー ({file_name}): {e}", "tcpResponse")
        raise e
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass


def _make_response(success=True, message="OK"):
    return {
        "type": "experiment_prepare_result",
        "success": success,
        "message": message
    }


# --------------------------------------------------
# リクエスト振り分け処理
# --------------------------------------------------

def _process_request(request, server_host):
    """
    Windowsから受信したJSONを処理・振り分けを行う。
    """
    request_type = request.get("type")

    # ① ファイル一覧要求 (data_list_request)
    if request_type == "data_list_request":
        file_names = _get_json_file_names()

        return {
            "type": "data_list_result",
            "success": True,
            "count": len(file_names),
            "files": file_names
        }

    # ② ファイル情報要求 (data_info_request)
    if request_type == "data_info_request":
        file_name = request.get("file_name")

        if not file_name:
            return {
                "type": "data_info_result",
                "success": False,
                "message": "file_nameが指定されていません。"
            }

        try:
            file_info = _get_json_file_info(file_name)

            return {
                "type": "data_info_result",
                "success": True,
                "data": file_info
            }

        except Exception as e:
            return {
                "type": "data_info_result",
                "success": False,
                "message": str(e)
            }

    # ③ エクスポート要求 (data_export_request) - 【追加箇所】
    if request_type == "data_export_request":
        transfer_id = request.get("transfer_id")
        file_name = request.get("file_name")
        transfer_port = request.get("transfer_port", 6005)

        if not file_name or not transfer_id:
            return {
                "type": "data_export_failed",
                "transfer_id": transfer_id or "",
                "message": "file_name または transfer_id が指定されていません。"
            }

        safe_file_name = os.path.basename(file_name)
        file_path = os.path.join(DATA_DIRECTORY, safe_file_name)

        # ファイルが存在しない場合は Port 6005 へ接続せず 6004 でエラー返信
        if not os.path.isfile(file_path):
            p.error(f"転送対象ファイルが存在しません: {safe_file_name}", "tcpResponse")
            return {
                "type": "data_export_failed",
                "transfer_id": transfer_id,
                "message": f"ファイルが存在しません: {safe_file_name}"
            }

        # 別スレッドで Port 6005 への転送を開始
        def run_export():
            try:
                _send_file_lz4_stream(
                    windows_ip=server_host,
                    transfer_port=int(transfer_port),
                    transfer_id=transfer_id,
                    file_path=file_path
                )
            except Exception as e:
                p.error(f"転送処理失敗: {e}", "tcpResponse")

        threading.Thread(target=run_export, daemon=True).start()

        # Port 6004 への即時レスポンス
        return {
            "type": "data_export_started",
            "transfer_id": transfer_id,
            "message": "ファイル転送を開始しました。"
        }

    # ④ 実験準備要求 (experiment_prepare) - 既存処理
    if request_type == "experiment_prepare":
        data = request.get("data")

        if not isinstance(data, dict):
            return _make_response(
                False,
                "dataが存在しないか、形式が不正です。"
            )

        experiment_id = data.get("experiment_id")
        csv_content = data.get("csv_content")

        if not experiment_id:
            return _make_response(
                False,
                "experiment_idが空です。"
            )

        if not csv_content:
            return _make_response(
                False,
                "csv_contentが空です。"
            )

        return _make_response(
            True,
            "CSVを受信し、計測準備が完了しました。"
        )

    # 未対応タイプ
    return {
        "type": "error",
        "success": False,
        "message": f"未対応のtypeです: {request_type}"
    }


def _send_json(sock, data):
    """
    JSONを1行形式で送信する。
    Windows側のReadLineAsyncに合わせて末尾へ改行を付ける。
    """
    json_text = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":")
    ) + "\n"

    sock.sendall(json_text.encode("utf-8"))


# --------------------------------------------------
# ソケット通信 ワーカースレッド
# --------------------------------------------------

def _client_worker(host, port, reconnect_seconds):
    global _client_socket
    global _client_file
    global _is_running

    while _is_running:
        sock = None
        file_reader = None

        try:
            p.info(
                f"Windowsへ接続中: {host}:{port}",
                "tcpResponse"
            )

            sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            sock.settimeout(10.0)
            sock.connect((host, port))
            sock.settimeout(None)

            file_reader = sock.makefile(
                "r",
                encoding="utf-8",
                newline="\n"
            )

            with _SOCKET_LOCK:
                _client_socket = sock
                _client_file = file_reader

            p.success(
                f"Windowsへ接続成功: {host}:{port}",
                "tcpResponse"
            )

            while _is_running:
                line = file_reader.readline()

                if line == "":
                    raise ConnectionError(
                        "Windows側との接続が切断されました。"
                    )

                line = line.strip()

                if not line:
                    continue

                p.info(
                    f"受信: {line}",
                    "tcpResponse"
                )

                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    response = {
                        "type": "error",
                        "success": False,
                        "message": f"JSON解析失敗: {e}"
                    }
                else:
                    try:
                        # host(接続先IP) を一緒に渡すよう修正
                        response = _process_request(request, host)
                    except Exception as e:
                        response = {
                            "type": "error",
                            "success": False,
                            "message": f"受信データ処理失敗: {e}"
                        }

                _send_json(sock, response)

                p.success(
                    f"返信完了: {response}",
                    "tcpResponse"
                )

        except Exception as e:
            if _is_running:
                p.error(
                    f"TCP通信エラー: {e}",
                    "tcpResponse"
                )

        finally:
            with _SOCKET_LOCK:
                _client_socket = None
                _client_file = None

            if file_reader is not None:
                try:
                    file_reader.close()
                except Exception:
                    pass

            if sock is not None:
                try:
                    sock.close()
                except Exception:
                    pass

        if _is_running:
            p.info(
                f"{reconnect_seconds}秒後に再接続します。",
                "tcpResponse"
            )
            time.sleep(reconnect_seconds)

    p.info(
        "TCPクライアントを停止しました。",
        "tcpResponse"
    )


# --------------------------------------------------
# 外部公開 API
# --------------------------------------------------

def start_client(config, host=None):
    """
    Windows側TCPサーバーへ接続する。
    """
    global _client_thread
    global _is_running

    if _is_running:
        p.info(
            "TCPクライアントは既に起動しています。",
            "tcpResponse"
        )
        return True

    tcp_config = config.get("tcp", {})
    ports = tcp_config.get("ports", {})

    hosts_list = tcp_config.get("hosts", [])
    default_host_from_list = hosts_list[0] if isinstance(hosts_list, list) and len(hosts_list) > 0 else None

    server_host = (
        host
        or default_host_from_list
        or tcp_config.get("server_ip")
        or tcp_config.get("host")
    )

    port = ports.get("experiment", 6004)
    reconnect_seconds = tcp_config.get(
        "reconnect_seconds",
        3
    )

    if not server_host or server_host == "0.0.0.0":
        p.error(
            f"無効な接続先IPアドレスです: {server_host}",
            "tcpResponse"
        )
        return False

    _is_running = True

    _client_thread = threading.Thread(
        target=_client_worker,
        args=(
            server_host,
            int(port),
            float(reconnect_seconds)
        ),
        daemon=True
    )

    _client_thread.start()

    return True


def close_client():
    """
    TCPクライアントを安全に停止する。
    """
    global _is_running
    global _client_socket
    global _client_file

    _is_running = False

    with _SOCKET_LOCK:
        file_reader = _client_file
        sock = _client_socket

        _client_file = None
        _client_socket = None

    if file_reader is not None:
        try:
            file_reader.close()
        except Exception:
            pass

    if sock is not None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass

        try:
            sock.close()
        except Exception:
            pass

    p.info(
        "TCPクライアント停止処理を実行しました。",
        "tcpResponse"
    )


def start_server(config, host=None):
    return start_client(config, host)


def close_server():
    close_client()