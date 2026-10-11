# -*- coding: utf-8 -*-
"""入口：启动本地服务并自动打开浏览器。"""

import socket
import sys
import threading
import time
import webbrowser

sys.stdout.reconfigure(encoding="utf-8")

from backend.config import PORT_CANDIDATES


def pick_port() -> int:
    for port in PORT_CANDIDATES:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    print("[错误] 候选端口均被占用，请运行 stop.bat 清理后重试")
    sys.exit(1)


def main():
    import uvicorn

    port = pick_port()
    url = f"http://127.0.0.1:{port}"
    print(f"[启动] 搜绎 → {url}")
    print("[提示] 按 Ctrl+C 停止服务")

    def open_browser():
        time.sleep(1.2)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.app:app", host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
