
#? Managers/systemManager.py
#? Norifumi Kondo

import platform
import re
import subprocess
from typing import Optional

import psutil

import Utils.logger as p


last_cpu: Optional[float] = None
reed_gpu = True
reed_power = True



def Initialization():
    global last_cpu,reed_gpu,reed_power

    initialization = True
    os_name = get_platform()

    p.info(f"実行OS: {os_name}")

    psutil.cpu_percent(interval=None)

    cpu_value = get_cpu()
    mem_value = get_mem()

    if cpu_value is None:
        p.error("取得できないデータ: CPU使用率")
        initialization = False
    else:
        last_cpu = cpu_value

    if mem_value is None:
        p.error("取得できないデータ: メモリ使用率")
        initialization = False

    if not initialization:
        p.error("主要データを取得できないため終了します。")
        return False

    gpu_value = get_gpu()

    if gpu_value is None:
        reed_gpu = False
        p.warning("取得できないデータ: GPU使用率")
        p.info("GPU使用率を使わずに実行を続けます。")

    gpu_power = get_gpu_power()

    if gpu_power is None:
        reed_power = False
        p.warning("取得できないデータ: GPU消費電力")
        p.info("GPU消費電力を使わずに実行を続けます。")

    p.info("systemManagerの初期化が完了しました。")

    return True


def get_platform():
    """実行中のOS名を返す。"""
    return platform.system()


def get_cpu():
    """
    CPU使用率を返す。

    取得値が0.0の場合は、前回の有効な値を返す。
    """
    global last_cpu

    try:
        usage = round(
            psutil.cpu_percent(interval=None),
            2
        )

        if usage > 0.0:
            last_cpu = usage
            return usage

        if last_cpu is not None:
            return last_cpu

        return 0.0

    except Exception as error:
        p.error(f"CPU使用率取得エラー: {error}")

        return last_cpu


def get_mem():
    """メモリ使用率を返す。"""

    try:
        return round(
            psutil.virtual_memory().percent,
            2
        )

    except Exception as error:
        p.error(f"メモリ使用率取得エラー: {error}")
        return None


def get_gpu():
    """GPU使用率を返す。取得できない場合はNone。"""
    if reed_gpu == False:
        return None
    os_name = get_platform()

    if os_name == "Windows":
        return gpu_windows()

    if os_name == "Darwin":
        return gpu_mac()

    return None


def gpu_windows():
    """WindowsのGPU使用率を取得する。"""

    command = (
        "$values = "
        "(Get-Counter "
        "'\\GPU Engine(*)\\Utilization Percentage' "
        "-ErrorAction SilentlyContinue)"
        ".CounterSamples.CookedValue; "
        "if ($values) { "
        "($values | Measure-Object -Maximum).Maximum "
        "}"
    )

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                command
            ],
            capture_output=True,
            text=True,
            timeout=3,
            check=False
        )

        value = result.stdout.strip()

        if not value:
            return None

        usage = float(value)

        return round(
            min(max(usage, 0.0), 100.0),
            2
        )

    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        ValueError
    ):
        return None


def gpu_mac():
    """MacのGPU使用率を取得する。"""

    try:
        result = subprocess.run(
            [
                "sudo",
                "-n",
                "powermetrics",
                "--samplers",
                "gpu_power",
                "-n",
                "1",
                "-i",
                "200"
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )

        if result.returncode != 0:
            p.error(
                f"powermetrics error: "
                f"{result.stderr.strip()}"
            )
            return None

        match = re.search(
            r"GPU HW active residency:\s*([\d.]+)%",
            result.stdout
        )

        if match is None:
            p.error("GPU使用率が出力内に見つかりません")
            return None

        return round(
            float(match.group(1)),
            2
        )

    except subprocess.TimeoutExpired:
        p.error("powermetricsがタイムアウトしました")
        return None

    except Exception as error:
        p.error(f"GPU取得エラー: {error}")
        return None


def get_gpu_power():
    if reed_power == False:
            return None

    if get_platform() != "Darwin":
        return None

    try:
        result = subprocess.run(
            [
                "sudo",
                "-n",
                "powermetrics",
                "--samplers",
                "gpu_power",
                "-n",
                "1",
                "-i",
                "100"
            ],
            capture_output=True,
            text=True,
            timeout=3,
            check=False
        )

        if result.returncode != 0:
            return None

        match = re.search(
            r"GPU Power:\s*([\d.]+)\s*mW",
            result.stdout
        )

        if match is None:
            return None

        return round(
            float(match.group(1)),
            2
        )

    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        ValueError
    ):
        return None