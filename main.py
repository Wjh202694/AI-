# -*- coding: utf-8 -*-
"""入口：启动服务。

本地：绑 127.0.0.1（默认）
云端：绑 0.0.0.0，由环境变量 HOST=0.0.0.0 启用
"""

import os
import socket
import sys
import threading
import time
import webbrowser

sys.stdout.reconfigure(encoding="utf-8")

from backend.config import PORT_CANDIDATES


def pick_port() -> int:
    host = os.getenv("SOUYI_HOST", "127.0.0.1")
    for port in PORT_CANDIDATES:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    print("[错误] 候选端口均被占用，请运行 stop.bat 清理后重试")
    sys.exit(1)


def main():
    import uvicorn

    # 云端用 0.0.0.0；本地默认 127.0.0.1
    host = os.getenv("SOUYI_HOST", "127.0.0.1")
    # 云端的端口通常由平台指定（Railway 注入 PORT），优先用环境变量
    port = int(os.getenv("PORT", "0")) or pick_port()

    url = f"http://{host}:{port}"
    print(f"[启动] 搜绎 → {url}")
    print("[提示] 按 Ctrl+C 停止服务")

    # 仅本机模式自动开浏览器；云端不开
    if host == "127.0.0.1":
        def open_browser():
            time.sleep(1.2)
            webbrowser.open(url)
        threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run("backend.app:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
