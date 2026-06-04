"""
Token 预算管理器 - 鲲之度支 (Token Budget)
每天精确控制API调用，确保消耗接近每日免费额度（约0.01元）
"""
import os
import time
import threading
import requests

# DeepSeek 定价：输入2元/百万tokens，输出8元/百万tokens
# 按平均每次输入500+输出200 tokens估算，单次消耗约 (500/1e6*2 + 200/1e6*8) ≈ 0.0026元
# 1分钱 ≈ 3.8次调用。为留余量，设定每日预算总 tokens = 6000
DAILY_BUDGET_TOKENS = 6000  # 对应约0.01元

BUDGET_FILE = "token_budget.json"

class TokenBudget:
    def __init__(self):
        self.lock = threading.Lock()
        self.today = time.strftime("%Y%m%d")
        self.budget_remaining = self._load_budget()

    def _load_budget(self):
        """从文件加载当日剩余预算，若日期变更则重置"""
        if os.path.exists(BUDGET_FILE):
            try:
                with open(BUDGET_FILE, 'r') as f:
                    data = json.load(f)
                if data.get("date") == self.today:
                    return data.get("remaining", DAILY_BUDGET_TOKENS)
            except:
                pass
        # 新的一天，重置预算
        return DAILY_BUDGET_TOKENS

    def _save_budget(self):
        with open(BUDGET_FILE, 'w') as f:
            json.dump({"date": self.today, "remaining": self.budget_remaining}, f)

    def can_consume(self, tokens):
        """检查是否有足够预算，tokens为预估消耗"""
        with self.lock:
            # 检查日期是否变更，若变更则重置
            today = time.strftime("%Y%m%d")
            if today != self.today:
                self.today = today
                self.budget_remaining = DAILY_BUDGET_TOKENS

            if self.budget_remaining >= tokens:
                return True
            return False

    def consume(self, tokens):
        """实际消耗tokens，需在调用成功后才调用此方法"""
        with self.lock:
            self.budget_remaining = max(0, self.budget_remaining - tokens)
            self._save_budget()

    def get_remaining(self):
        with self.lock:
            return self.budget_remaining

# 全局单例
budget = TokenBudget()
