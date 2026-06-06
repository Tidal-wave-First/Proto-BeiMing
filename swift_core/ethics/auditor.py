"""
伦理审计引擎 —— 对所有任务和思维步骤进行红线/黄线检查。
所有规则从 rules.yaml 加载，运行时只读。
"""

import yaml
import re
from pathlib import Path
from typing import List, Tuple

class EthicsAuditor:
    def __init__(self, rules_path: str = None):
        if rules_path is None:
            rules_path = Path(__file__).parent / "rules.yaml"
        with open(rules_path, "r", encoding="utf-8") as f:
            rules = yaml.safe_load(f)
        self.red_lines = rules.get("red_lines", [])
        self.yellow_lines = rules.get("yellow_lines", [])
        self.silence_rules = rules.get("silence_rules", [])

    def audit_goal(self, text: str) -> Tuple[bool, str]:
        """检查任务目标，返回 (是否通过, 原因)"""
        # 先检查静默规则
        for rule in self.silence_rules:
            if re.search(rule["pattern"], text, re.IGNORECASE):
                return False, rule["response"]
        # 再检查红线
        for rule in self.red_lines:
            if re.search(rule["pattern"], text, re.IGNORECASE):
                return False, rule["response"]
        return True, ""

    def audit_subgoal(self, text: str) -> Tuple[bool, str]:
        """检查子目标（较宽松，只检查红线）"""
        for rule in self.red_lines:
            if re.search(rule["pattern"], text, re.IGNORECASE):
                return False, rule["response"]
        return True, ""