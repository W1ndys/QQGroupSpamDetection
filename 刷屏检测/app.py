from flask import Flask, render_template, request, jsonify
import time
import json
from main import SpamDetector

app = Flask(__name__)

# 存储聊天记录和检测器字典
chat_history = []
detectors = {}


@app.route("/")
def index():
    """渲染聊天界面"""
    return render_template("index.html")


@app.route("/send_message", methods=["POST"])
def send_message():
    """接收并处理消息"""
    data = request.get_json()
    user_id = data.get("user_id")
    group_id = data.get("group_id", "default_group")
    message = data.get("message")

    # 创建或获取用户的检测器
    if user_id not in detectors:
        detectors[user_id] = SpamDetector(user_id, group_id)

    detector = detectors[user_id]
    detector.add_message(message)
    is_spam = detector.check_spam()

    # 记录消息
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    chat_item = {
        "user_id": user_id,
        "message": message,
        "timestamp": timestamp,
        "is_spam": is_spam,
    }
    chat_history.append(chat_item)

    # 获取检测器状态
    detector_status = {
        "message_count": len(detector.message_queue),
        "recent_messages": len(
            [
                t
                for t, _ in detector.message_queue
                if time.time() - t <= detector.time_window
            ]
        ),
        "time_window": detector.time_window,
        "message_threshold": detector.message_threshold,
        "similarity_threshold": detector.similarity_threshold,
    }

    return jsonify(
        {
            "success": True,
            "is_spam": is_spam,
            "chat_item": chat_item,
            "detector_status": detector_status,
        }
    )


@app.route("/get_history")
def get_history():
    """获取聊天历史"""
    return jsonify(chat_history)


@app.route("/clear_history", methods=["POST"])
def clear_history():
    """清空聊天历史和检测器"""
    global chat_history, detectors
    chat_history = []
    detectors = {}
    return jsonify({"success": True})


@app.route("/run_demo", methods=["POST"])
def run_demo():
    """运行预定义的演示场景"""
    data = request.get_json()
    scenario = data.get("scenario")

    # 清空当前状态
    global chat_history, detectors
    chat_history = []
    detectors = {}

    # 场景1: 正常聊天
    if scenario == "normal":
        user_id = "user1"
        group_id = "demo_group"
        detector = SpamDetector(user_id, group_id)
        detectors[user_id] = detector

        messages = [
            "大家好！",
            "今天天气不错",
            "大家吃午饭了吗？",
            "我刚刚吃完饭",
            "下午有什么安排？",
            "我准备去图书馆",
            "好的，注意安全",
            "谢谢关心",
            "晚上见",
            "拜拜",
        ]

        for msg in messages:
            detector.add_message(msg)
            is_spam = detector.check_spam()
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            chat_item = {
                "user_id": user_id,
                "message": msg,
                "timestamp": timestamp,
                "is_spam": is_spam,
            }
            chat_history.append(chat_item)

    # 场景2: 刷屏行为
    elif scenario == "spam":
        user_id = "user2"
        group_id = "demo_group"
        detector = SpamDetector(user_id, group_id)
        detectors[user_id] = detector

        messages = ["刷屏测试！"] * 15

        for msg in messages:
            detector.add_message(msg)
            is_spam = detector.check_spam()
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            chat_item = {
                "user_id": user_id,
                "message": msg,
                "timestamp": timestamp,
                "is_spam": is_spam,
            }
            chat_history.append(chat_item)
            if is_spam:
                break

    # 场景3: 正常聊天突然刷屏
    elif scenario == "mixed":
        user_id = "user3"
        group_id = "demo_group"
        detector = SpamDetector(user_id, group_id)
        detectors[user_id] = detector

        messages = [
            "大家好！",
            "今天天气真不错",
            "是啊，适合出去玩",
            "你们准备去哪玩？",
            "我打算去公园",
            "公园人太多了",
            "那去爬山怎么样？",
            "爬山不错，空气好",
        ]

        spam_messages = ["刷屏测试！"] * 15

        # 正常聊天部分
        for msg in messages:
            detector.add_message(msg)
            is_spam = detector.check_spam()
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            chat_item = {
                "user_id": user_id,
                "message": msg,
                "timestamp": timestamp,
                "is_spam": is_spam,
            }
            chat_history.append(chat_item)

        # 刷屏部分
        for msg in spam_messages:
            detector.add_message(msg)
            is_spam = detector.check_spam()
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            chat_item = {
                "user_id": user_id,
                "message": msg,
                "timestamp": timestamp,
                "is_spam": is_spam,
            }
            chat_history.append(chat_item)
            if is_spam:
                break

    # 场景4: 多用户交替发言
    elif scenario == "multi_user":
        user1_id = "user4"
        user2_id = "user5"
        group_id = "demo_group"

        detector1 = SpamDetector(user1_id, group_id)
        detector2 = SpamDetector(user2_id, group_id)

        detectors[user1_id] = detector1
        detectors[user2_id] = detector2

        messages = [
            (user1_id, "你们在聊什么？"),
            (user2_id, "我们在讨论游戏"),
            (user1_id, "什么游戏？"),
            (user2_id, "最近很火的那个"),
            (user1_id, "好玩吗？"),
            (user2_id, "还不错"),
            (user1_id, "我也要玩"),
            (user2_id, "一起来啊"),
            (user1_id, "好的"),
            (user2_id, "等你"),
        ]

        for user_id, msg in messages:
            if user_id == user1_id:
                detector = detector1
            else:
                detector = detector2

            detector.add_message(msg)
            is_spam = detector.check_spam()

            timestamp = time.strftime("%H:%M:%S", time.localtime())
            chat_item = {
                "user_id": user_id,
                "message": msg,
                "timestamp": timestamp,
                "is_spam": is_spam,
            }
            chat_history.append(chat_item)

    return jsonify({"success": True, "history": chat_history})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
