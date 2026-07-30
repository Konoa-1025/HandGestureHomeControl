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
# 実験状態管理クラス (ExperimentState)
# --------------------------------------------------

class ExperimentState:
    """
    計測の状態、受信済みCSV/設定、保存用ファイルハンドラを保持・管理するクラス
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.is_measuring = False
        self.prepared_data = None      # experiment_prepare で保存したデータ (CSV等)
        self.current_experiment_id = None
        self.current_trial_id = None
        self.log_file = None           # JSONL書き込み用ファイルハンドラ

    def prepare(self, data):
        """実験準備データの保存"""
        with self._lock:
            self.prepared_data = data
            p.info(f"実験準備完了: experiment_id={data.get('experiment_id')}", "ExperimentState")

    def start(self, experiment_id, trial_id):
        """計測開始"""
        with self._lock:
            if self.is_measuring:
                raise RuntimeError("すでに計測が開始されています。")

            if not self.prepared_data:
                raise RuntimeError("計測準備(experiment_prepare)が完了していません。")

            self.is_measuring = True
            self.current_experiment_id = experiment_id
            self.current_trial_id = trial_id

            # 保存先ディレクトリの作成
            if not os.path.exists(DATA_DIRECTORY):
                os.makedirs(DATA_DIRECTORY, exist_ok=True)

            # JSONLログファイルのオープン (例: research_logs/EXP_1_trial_1_timestamp.jsonl)
            timestamp_str = time.strftime("%Y%m%d_%H%M%S")
            file_name = f"exp_{experiment_id}_trial_{trial_id}_{timestamp_str}.jsonl"
            file_path = os.path.join(DATA_DIRECTORY, file_name)

            self.log_file = open(file_path, "a", encoding="utf-8")

            # ヘッダー情報（実験条件等）を1行目として書き込み
            init_header = {
                "type": "experiment_header",
                "timestamp": time.time(),
                "experiment_id": experiment_id,
                "trial_id": trial_id,
                "prepared_data": self.prepared_data
            }
            self.log_file.write(json.dumps(init_header, ensure_ascii=False) + "\n")
            self.log_file.flush()
            
            p.success(f"計測開始: {file_name}", "ExperimentState")

    def abort(self):
        """計測中止・安全なクローズ"""
        with self._lock:
            if not self.is_measuring and self.log_file is None:
                p.warning("計測中ではありませんが、破棄処理を実行しました。", "ExperimentState")

            self.is_measuring = False

            # ファイルハンドラの安全なクローズ
            if self.log_file:
                try:
                    abort_record = {
                        "type": "experiment_aborted",
                        "timestamp": time.time()
                    }
                    self.log_file.write(json.dumps(abort_record, ensure_ascii=False) + "\n")
                    self.log_file.flush()
                    self.log_file.close()
                except Exception as e:
                    p.error(f"ログファイルクローズ時のエラー: {e}", "ExperimentState")
                finally:
                    self.log_file = None

            self.current_experiment_id = None
            self.current_trial_id = None
            p.info("計測を安全に停止・破棄しました。", "ExperimentState")

    def write_measurement_frame(self, record_dict):
        """計測中にフレームデータ等を書き込む外部用関数"""
        with self._lock:
            if self.is_measuring and self.log_file:
                record_dict["timestamp"] = time.time()
                self.log_file.write(json.dumps(record_dict, ensure_ascii=False) + "\n")
                self.log_file.flush()


# シングルトンインスタンス化
experiment_state = ExperimentState()


# --------------------------------------------------
# ヘルパー関数: JSON / JSONL ファイルの取得・解析
# --------------------------------------------------

def _get_json_file_names():
    if not os.path.isdir(DATA_DIRECTORY):
        return []

    file_names = []
    for file_name in os.listdir(DATA_DIRECTORY):
        ext = os.path.splitext(file_name)[1].lower()
        if ext in [".jsonl", ".json"]:
            file_names.append(file_name)

    file_names.sort(reverse=True)
    return file_names


def _get_json_file_info(file_name):
    safe_file_name = os.path.basename(file_name)

    if safe_file_name != file_name:
        raise ValueError("不正なファイル名です。")

    file_path = os.path.join(DATA_DIRECTORY, safe_file_name)

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"ファイルが見つかりません: {safe_file_name}")

    json_data = {}

    with open(file_path, "r", encoding="utf-8") as file:
        first_line = file.readline().strip()
        if first_line:
            try:
                json_data = json.loads(first_line)
            except json.JSONDecodeError:
                file.seek(0)
                json_data = json.load(file)

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
    file_name = os.path.basename(file_path)
    original_size = os.path.getsize(file_path)

    sock = None
    try:
        p.info(f"転送用ソケット接続中: {windows_ip}:{transfer_port}", "tcpResponse")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        sock.connect((windows_ip, transfer_port))
        sock.settimeout(None)

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

        sock_file = sock.makefile("wb")

        try:
            with open(file_path, "rb") as source:
                with lz4.frame.open(sock_file, mode="wb") as compressed:
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        compressed.write(chunk) #type:ignore

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

    # ③ エクスポート要求 (data_export_request)
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

        if not os.path.isfile(file_path):
            p.error(f"転送対象ファイルが存在しません: {safe_file_name}", "tcpResponse")
            return {
                "type": "data_export_failed",
                "transfer_id": transfer_id,
                "message": f"ファイルが存在しません: {safe_file_name}"
            }

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

        return {
            "type": "data_export_started",
            "transfer_id": transfer_id,
            "message": "ファイル転送を開始しました。"
        }

    # ④ 実験準備要求 (experiment_prepare)
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

        # 実験状態オブジェクトへセット
        experiment_state.prepare(data)

        return _make_response(
            True,
            "CSVを受信し、計測準備が完了しました。"
        )

    # ⑤ 実験開始要求 (experiment_start) - 【新規追加】
    if request_type == "experiment_start":
        experiment_id = request.get("experiment_id")
        trial_id = request.get("trial_id", 1)

        try:
            experiment_state.start(experiment_id, trial_id)
            return {
                "type": "experiment_start_result",
                "success": True,
                "message": "計測を開始しました"
            }
        except Exception as e:
            p.error(f"計測開始失敗: {e}", "tcpResponse")
            return {
                "type": "experiment_start_result",
                "success": False,
                "message": f"計測開始失敗: {e}"
            }

    # ⑥ 実験中止要求 (experiment_abort) - 【新規追加】
    if request_type == "experiment_abort":
        try:
            experiment_state.abort()
            return {
                "type": "experiment_abort_result",
                "success": True,
                "message": "計測を中止しました"
            }
        except Exception as e:
            p.error(f"計測中止処理エラー: {e}", "tcpResponse")
            return {
                "type": "experiment_abort_result",
                "success": False,
                "message": f"計測中止エラー: {e}"
            }

    # 未対応タイプ
    return {
        "type": "error",
        "success": False,
        "message": f"未対応のtypeです: {request_type}"
    }


def _send_json(sock, data):
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
            # 万が一通信が切断された場合、安全のため計測も停止・クローズする
            if experiment_state.is_measuring:
                p.warning("通信切断のため、計測を強制停止します。", "tcpResponse")
                experiment_state.abort()

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
    global _is_running
    global _client_socket
    global _client_file

    _is_running = False

    # プログラム停止時にも安全にログファイルをクローズ
    if experiment_state.is_measuring:
        experiment_state.abort()

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