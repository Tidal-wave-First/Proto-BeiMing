"""
意图分类器 - 鲲之辨 (Intent Parser)
不依赖外部模型，仅用规则判断用户输入的类型。
"""
import re

SELF_META_PATTERNS = [
    r"你是谁", r"你叫什么", r"你的身份", r"你是什么",
    r"你学到了什么", r"你学会了什么", r"你知道了什么",
    r"你会做什么", r"你能做什么", r"你的能力",
    r"你是AI|你是人工智能|你是机器人|你是程序",
    r"你喜欢什么", r"你的爱好",
    r"你来自哪里", r"你哪里来的",
    r"你.*谁更.*厉害", r"你.*强大",
    r"你.*怎么样", r"你.*还好吗",
]

SEARCH_COMMAND_PREFIX = ["搜索", "查", "找", "帮我找", "搜一下", "查一下"]

FEEDBACK_KEYWORDS = ["学得怎么样", "你的成长", "你最近在做什么", "自我报告", "你的认知"]

def classify(user_input: str) -> str:
    """
    返回: 'self_meta' | 'feedback' | 'search_command' | 'normal'
    """
    text = user_input.strip()
    # 1. 反馈请求
    for kw in FEEDBACK_KEYWORDS:
        if kw in text:
            return "feedback"
    # 2. 搜索指令
    for prefix in SEARCH_COMMAND_PREFIX:
        if text.startswith(prefix):
            return "search_command"
    # 3. 自我元问题
    for pattern in SELF_META_PATTERNS:
        if re.search(pattern, text):
            return "self_meta"
    # 4. 其余为普通问题
    return "normal"
