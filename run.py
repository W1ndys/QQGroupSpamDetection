#!/usr/bin/env python
"""
刷屏检测系统可视化演示启动脚本
"""
import os
import webbrowser
import time
import threading
from app import app


def open_browser():
    """在浏览器中打开应用"""
    time.sleep(1.5)
    webbrowser.open("http://localhost:5000")


if __name__ == "__main__":
    print("=" * 60)
    print("刷屏检测系统可视化演示")
    print("=" * 60)
    print("正在启动Web服务器...")

    # 使用环境变量判断是否为主进程
    # Flask在debug模式下会启动一个reloader进程和一个worker进程
    # 这会导致open_browser被调用两次，打开两个标签页
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        # 只在主进程中打开浏览器
        threading.Thread(target=open_browser).start()

    # 启动Flask应用
    print("服务器已启动，请访问 http://localhost:5000")
    app.run(debug=True, port=5000)
