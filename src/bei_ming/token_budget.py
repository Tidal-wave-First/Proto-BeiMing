"""
Token 预算管理器 - 鲲之度支
"""
import os, json, time, threading

DAILY_BUDGET_TOKENS = 6000
BUDGET_FILE = "token_budget.json"

class TokenBudget:
    def __init__(self):
        self.lock = threading.Lock()
        self.today = time.strftime("%Y%m%d")
        self.budget_remaining = self._load_budget()

    def _load_budget(self):
        if os.path.exists(BUDGET_FILE):
            try:
                with open(BUDGET_FILE, 'r') as f:
                    data = json.load(f)
                if data.get("date") == self.today:
                    return data.get("remaining", DAILY_BUDGET_TOKENS)
            except:
                pass
        return DAILY_BUDGET_TOKENS

    def _save_budget(self):
        with open(BUDGET_FILE, 'w') as f:
            json.dump({"date": self.today, "remaining": self.budget_remaining}, f)

    def can_consume(self, tokens):
        with self.lock:
            today = time.strftime("%Y%m%d")
            if today != self.today:
                self.today = today
                self.budget_remaining = DAILY_BUDGET_TOKENS
            return self.budget_remaining >= tokens

    def consume(self, tokens):
        with self.lock:
            self.budget_remaining = max(0, self.budget_remaining - tokens)
            self._save_budget()

    def get_remaining(self):
        with self.lock:
            return self.budget_remaining

budget = TokenBudget()
