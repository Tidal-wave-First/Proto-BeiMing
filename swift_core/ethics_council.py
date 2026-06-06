"""
伦理规则思维体 —— 最高法院（V2.1 暖心版）。
结果导向审查，拒绝时返回暖心语句。
"""

import re
import yaml
from pathlib import Path
from typing import Optional
from common.types import Verdict
from common.constants import ETHICS_RULES_PATH


class EthicsCouncil:
    def __init__(self, rules_path: Optional[str] = None):
        self.rules_path = Path(rules_path or ETHICS_RULES_PATH)
        self.rules = self._load_rules()

    def _load_rules(self) -> dict:
        with open(self.rules_path, "r", encoding="utf-8") as f:
            rules = yaml.safe_load(f)
        return rules

    def judge(self, content: str) -> Verdict:
        if not content or not content.strip():
            return Verdict.approved()

        # 第一关：哲学静默规则
        for rule in self.rules.get("silence_rules", []):
            if self._match(rule["pattern"], content):
                warm = rule.get("warm_response", rule.get("reason", ""))
                return Verdict.rejected(rule["id"], warm)

        # 第二关：红线规则
        for rule in self.rules.get("red_lines", []):
            if self._match(rule["pattern"], content):
                warm = rule.get("warm_response", rule.get("reason", ""))
                return Verdict.rejected(rule["id"], warm)

        return Verdict.approved()

    def judge_yellow(self, content: str) -> Verdict:
        for rule in self.rules.get("yellow_lines", []):
            if self._match(rule["pattern"], content):
                warm = rule.get("warm_response", rule.get("reason", ""))
                return Verdict.rejected(rule["id"], warm)
        return Verdict.approved()

    @staticmethod
    def _match(pattern: str, text: str) -> bool:
        try:
            return bool(re.search(pattern, text, re.IGNORECASE))
        except re.error:
            return False

    def think(self, *args, **kwargs):
        raise NotImplementedError("伦理规则思维体没有思考能力。")
    def learn(self, *args, **kwargs):
        raise NotImplementedError("伦理规则思维体没有学习能力。")


_ethics_council_instance: Optional[EthicsCouncil] = None
def get_ethics_council() -> EthicsCouncil:
    global _ethics_council_instance
    if _ethics_council_instance is None:
        _ethics_council_instance = EthicsCouncil()
    return _ethics_council_instance
