from collections import deque
import time
import hashlib
import logging
import colorlog


# 配置彩色日志
def setup_logger():
    """配置彩色日志输出"""
    # 创建日志处理器
    file_handler = logging.FileHandler("spam_detection.log", encoding="utf-8")
    console_handler = colorlog.StreamHandler()

    # 设置文件日志格式
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)

    # 设置控制台日志格式（带颜色）
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
    console_handler.setFormatter(console_formatter)

    # 创建并配置日志记录器
    logger = colorlog.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# 初始化日志记录器
logger = setup_logger()


class SpamDetector:
    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id
        # 消息队列，存储最近的消息记录 (timestamp, message_hash)
        self.message_queue = deque(maxlen=50)
        # 默认检测参数
        self.time_window = 60  # 检测时间窗口(秒)
        self.message_threshold = 10  # 时间窗口内消息数量阈值
        self.similarity_threshold = 0.7  # 相似消息比例阈值
        self.min_message_length = 5  # 参与相似性检测的最小消息长度
        # 新增参数：消息频率刷屏检测
        self.frequency_window = 10  # 频率检测的时间窗口(秒)
        self.frequency_threshold = 5  # 短时间内消息数量阈值
        logger.info(f"🎯 初始化刷屏检测器 - 用户ID: {user_id}, 群组ID: {group_id}")

    def add_message(self, message):
        """添加新消息到检测队列"""
        current_time = time.time()
        message_hash = self._hash_message(message)
        self.message_queue.append((current_time, message_hash))

        # 记录消息队列状态
        queue_size = len(self.message_queue)
        time_window_messages = len(
            [t for t, _ in self.message_queue if current_time - t <= self.time_window]
        )

        logger.info(f"📩 新消息处理 - 用户: {self.user_id}")
        logger.info(f"💬 消息内容: {message}")
        logger.info(f"🔑 消息哈希: {message_hash}")
        logger.info(
            f"⏰ 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))}"
        )
        logger.info(
            f"📊 消息队列状态 - 总消息数: {queue_size}, 时间窗口内消息数: {time_window_messages}"
        )

        # 检查是否可能构成刷屏
        if time_window_messages >= self.message_threshold:
            logger.warning(
                f"⚠️ 消息数量达到阈值 - 当前数量: {time_window_messages}, 阈值: {self.message_threshold}"
            )

    def check_spam(self):
        """检查是否构成刷屏行为"""
        current_time = time.time()

        # 1. 检查时间窗口内的消息数量
        recent_messages = [
            (t, h)
            for t, h in self.message_queue
            if current_time - t <= self.time_window
        ]

        if len(recent_messages) < self.message_threshold:
            logger.debug(
                f"📈 消息数量未达到阈值 - 当前数量: {len(recent_messages)}, 阈值: {self.message_threshold}"
            )
            return False

        # 1.5 新增：检查短时间内发送消息的频率（不管内容）
        # 统计较短时间窗口内的消息数量
        freq_window_messages = [
            (t, h)
            for t, h in self.message_queue
            if current_time - t <= self.frequency_window
        ]

        # 如果短时间内消息数量超过阈值，判定为刷屏
        if len(freq_window_messages) >= self.frequency_threshold:
            logger.warning(
                f"🚨 检测到消息频率过高 - 用户: {self.user_id}, {self.frequency_window}秒内发送了{len(freq_window_messages)}条消息"
            )
            return True

        # 2. 检查相似消息比例（全局窗口）
        hash_counts = {}
        for _, message_hash in recent_messages:
            hash_counts[message_hash] = hash_counts.get(message_hash, 0) + 1

        max_count = max(hash_counts.values())
        similarity_ratio = max_count / len(recent_messages)

        # 3. 短时间窗口检测（检测最近的消息模式）
        # 如果消息总数超过阈值，再检查最近的N条消息
        if len(recent_messages) >= self.message_threshold:
            # 获取最近N条消息（N等于message_threshold）
            recent_n_messages = recent_messages[-self.message_threshold :]

            # 计算最近N条消息的相似度
            recent_hash_counts = {}
            for _, message_hash in recent_n_messages:
                recent_hash_counts[message_hash] = (
                    recent_hash_counts.get(message_hash, 0) + 1
                )

            # 如果有哈希值，计算最近消息的相似度
            if recent_hash_counts:
                recent_max_count = max(recent_hash_counts.values())
                recent_similarity_ratio = recent_max_count / len(recent_n_messages)

                # 使用更严格的相似度阈值检测最近的消息
                # 这样即使前面有大量不同消息，最近的刷屏行为也能被检测出来
                recent_threshold = (
                    self.similarity_threshold * 0.9
                )  # 比全局窗口低10%的阈值

                if recent_similarity_ratio >= recent_threshold:
                    logger.warning(
                        f"🚨 检测到最近消息刷屏 - 用户: {self.user_id}, 最近{self.message_threshold}条消息相似度: {recent_similarity_ratio:.2f}"
                    )
                    return True

                logger.debug(
                    f"📊 最近{self.message_threshold}条消息相似度: {recent_similarity_ratio:.2f}"
                )

        # 全局窗口检测结果
        if similarity_ratio >= self.similarity_threshold:
            logger.warning(
                f"🚨 检测到刷屏行为 - 用户: {self.user_id}, 相似度: {similarity_ratio:.2f}"
            )
            return True
        else:
            logger.debug(
                f"✅ 未检测到刷屏 - 相似度: {similarity_ratio:.2f}, 阈值: {self.similarity_threshold}"
            )
            return False

    def _hash_message(self, message):
        """生成消息的简化哈希，用于相似性比较"""
        # 对长消息取前中后部分组合后再哈希，提高相似性检测效果
        if len(message) > 20:
            part1 = message[:10]
            part2 = message[len(message) // 2 - 5 : len(message) // 2 + 5]
            part3 = message[-10:] if len(message) >= 10 else message
            combined = part1 + part2 + part3
        else:
            combined = message

        # 标准化处理：去除空格和标点，转为小写
        normalized = "".join(c.lower() for c in combined if c.isalnum())
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def adjust_parameters(
        self,
        time_window=None,
        message_threshold=None,
        similarity_threshold=None,
        frequency_window=None,
        frequency_threshold=None,
    ):
        """调整检测参数"""
        if time_window is not None:
            self.time_window = time_window
        if message_threshold is not None:
            self.message_threshold = message_threshold
        if similarity_threshold is not None:
            self.similarity_threshold = similarity_threshold
        # 新增参数调整
        if frequency_window is not None:
            self.frequency_window = frequency_window
        if frequency_threshold is not None:
            self.frequency_threshold = frequency_threshold


# 初始化检测器
detector = SpamDetector(user_id="123456", group_id="7890")

# 模拟添加消息
messages = [
    "大家好！",
    "大家好！",
    "大家好！",
    "刷屏测试",
    "大家好！",
    "大家好！",
    "大家好！",
    "大家好！",
    "大家好！",
    "大家好！",
    "大家好！",
    "大家好！",
]

for msg in messages:
    detector.add_message(msg)
    if detector.check_spam():
        logger.warning("检测到刷屏行为！")
        break


def test_spam_detection():
    """测试不同场景下的刷屏检测"""
    logger.info("🔍 开始测试刷屏检测...")

    # 场景1：正常聊天
    logger.info("\n📝 场景1：正常聊天")
    detector1 = SpamDetector(user_id="user1", group_id="group1")
    normal_messages = [
        "早上好！",
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
    for msg in normal_messages:
        detector1.add_message(msg)
        if detector1.check_spam():
            logger.warning("❌ 错误：正常聊天被误判为刷屏！")
        time.sleep(1)

    # 场景2：快速重复消息（刷屏）
    logger.info("\n🚫 场景2：快速重复消息")
    detector2 = SpamDetector(user_id="user2", group_id="group1")
    spam_messages = ["刷屏测试！"] * 15
    for msg in spam_messages:
        detector2.add_message(msg)
        if detector2.check_spam():
            logger.warning("🚨 检测到刷屏行为！")
            break
        time.sleep(0.1)

    # 场景3：相似但不完全相同的内容
    logger.info("\n🔄 场景3：相似内容")
    detector3 = SpamDetector(user_id="user3", group_id="group1")
    similar_messages = [
        "这个游戏真好玩",
        "这个游戏太好玩了",
        "这个游戏真的很好玩",
        "这个游戏超级好玩",
        "这个游戏特别好玩",
        "这个游戏非常有趣",
        "这个游戏太有趣了",
        "这个游戏真的很有趣",
        "这个游戏超级有趣",
        "这个游戏特别有趣",
    ]
    for msg in similar_messages:
        detector3.add_message(msg)
        if detector3.check_spam():
            logger.warning("🚨 检测到相似内容刷屏！")
            break
        time.sleep(0.5)

    # 场景4：长文本刷屏
    logger.info("\n📜 场景4：长文本刷屏")
    detector4 = SpamDetector(user_id="user4", group_id="group1")
    long_text = "这是一段很长的文本，用于测试长文本的刷屏检测效果。这段文本包含了很多内容，但是核心意思都是一样的，只是表达方式略有不同。"
    for i in range(10):
        detector4.add_message(long_text + f" 第{i+1}次")
        if detector4.check_spam():
            logger.warning("🚨 检测到长文本刷屏！")
            break
        time.sleep(0.3)

    # 场景5：多用户交替发言
    logger.info("\n👥 场景5：多用户交替发言")
    detector5 = SpamDetector(user_id="user5", group_id="group1")
    detector6 = SpamDetector(user_id="user6", group_id="group1")
    multi_user_messages = [
        ("user5", "你们在聊什么？"),
        ("user6", "我们在讨论游戏"),
        ("user5", "什么游戏？"),
        ("user6", "最近很火的那个"),
        ("user5", "好玩吗？"),
        ("user6", "还不错"),
        ("user5", "我也要玩"),
        ("user6", "一起来啊"),
        ("user5", "好的"),
        ("user6", "等你"),
    ]
    for user_id, msg in multi_user_messages:
        if user_id == "user5":
            detector5.add_message(msg)
            detector5.check_spam()
        else:
            detector6.add_message(msg)
            detector6.check_spam()
        time.sleep(0.5)

    # 场景6：正常聊天中突然刷屏
    logger.info("\n🎭 场景6：正常聊天中突然刷屏")
    detector7 = SpamDetector(user_id="user7", group_id="group1")
    mixed_messages = [
        "大家好！",
        "今天天气真不错",
        "是啊，适合出去玩",
        "你们准备去哪玩？",
        "我打算去公园",
        "公园人太多了",
        "那去爬山怎么样？",
        "爬山不错，空气好",
        "刷屏测试！",  # 开始刷屏
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
        "刷屏测试！",
    ]

    logger.info("💬 开始正常聊天...")
    for i, msg in enumerate(mixed_messages):
        detector7.add_message(msg)
        if i == 7:  # 在正常聊天后
            logger.info("⚠️ 用户开始刷屏...")
            time.sleep(0.1)  # 快速发送刷屏消息
        elif i < 8:  # 正常聊天时
            time.sleep(1)  # 正常聊天间隔
        else:  # 刷屏时
            time.sleep(0.1)  # 快速发送
        if detector7.check_spam():
            logger.warning("🚨 检测到刷屏行为！")
            break

    logger.info("✅ 测试完成！")


if __name__ == "__main__":
    test_spam_detection()
