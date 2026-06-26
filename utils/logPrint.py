# logPrint.py
# Norifumi Kondo

from datetime import datetime
import inspect
import os
import threading

_print_lock = threading.Lock()

def now():
    return datetime.now().strftime("%H:%M:%S")


class Color:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    CYAN = '\033[36m'

    BLACK = '\033[30m'
    WHITE = '\033[97m'

    BG_RED = '\033[48;5;106m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_CYAN = '\033[46m'

    RESET = '\033[0m'


def _get_source():
    frame = inspect.stack()[3]
    filename = os.path.basename(frame.filename)
    return os.path.splitext(filename)[0]


def _use_bg(source):
    return source in [
        "standbyModel",
        "lowModel",
        "highModel",
        "highLevel",
        "lowLevel"
    ]


def _display_name(source):
    names = {
        "main": "main",
        "tcpSender": "tcp",
        "echonetSender": "echo",
        "standbyModel": "standby",
        "lowModel": "low",
        "highModel": "high",
        "cameraManager": "camera",
        "highLevel":"cas-hi",
        "lowLevel":"cas-Lo"
    }

    return names.get(source, source)


def _label(level, source):
    use_bg = _use_bg(source)

    if level == "INFO":
        return f"{Color.BLACK}{Color.BG_CYAN}[ INFO  ]{Color.RESET}" if use_bg else f"{Color.CYAN}[ INFO  ]{Color.RESET}"

    if level == "SUCCESS":
        return f"{Color.BLACK}{Color.BG_GREEN}[SUCCESS]{Color.RESET}" if use_bg else f"{Color.GREEN}[SUCCESS]{Color.RESET}"

    if level == "WARNING":
        return f"{Color.BLACK}{Color.BG_YELLOW}[WARNING]{Color.RESET}" if use_bg else f"{Color.YELLOW}[WARNING]{Color.RESET}"

    if level == "ERROR":
        return f"{Color.WHITE}{Color.BG_RED}[ ERROR ]{Color.RESET}" if use_bg else f"{Color.RED}[ ERROR ]{Color.RESET}"

    return "[UNKNOWN]"


def _plain_label(level):
    return f"[{level:^7}]"


def _send_tcp_log(message):
    try:
        import senders.tcpSender as tcpSender
        tcpSender.send_log(message)
    except:
        pass


def _send_tcp_research_log(message):
    try:
        import senders.tcpSender as tcpSender
        tcpSender.send_research_log(message)
    except:
        pass


def _log(level, text, source=None, research=False):
    if source is None:
        source = _get_source()

    name = _display_name(source)

    console_message = (
        f"[{now()}] "
        f"{_label(level, source)} "
        f"[{name:<7}] "
        f"{text}"
    )

    tcp_message = (
        f"[{now()}] "
        f"{_plain_label(level)} "
        f"[{name:<7}] "
        f"{text}"
    )

    with _print_lock:
        print(console_message)

    if research:
        _send_tcp_research_log(tcp_message)
    else:
        _send_tcp_log(tcp_message)



def info(text, source=None):
    _log("INFO", text, source)


def success(text, source=None):
    _log("SUCCESS", text, source)


def warning(text, source=None):
    _log("WARNING", text, source)


def error(text, source=None):
    _log("ERROR", text, source)


def research(text, source=None):
    _log("INFO", text, source, research=True)


def research_success(text, source=None):
    _log("SUCCESS", text, source, research=True)


def research_warning(text, source=None):
    _log("WARNING", text, source, research=True)


def research_error(text, source=None):
    _log("ERROR", text, source, research=True)