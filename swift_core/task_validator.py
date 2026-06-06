"""
任务合法性二次审查。
在所有任务进入推理引擎前调用。
"""

from common.types import Task
from thinking_core.ethics.auditor import EthicsAuditor

class TaskValidator:
    def __init__(self, auditor: EthicsAuditor = None):
        self.auditor = auditor or EthicsAuditor()

    def validate(self, task: Task) -> tuple:
        """
        返回 (is_valid, reject_reason)
        """
        if not task.goal:
            return False, "任务目标为空"
        if not task.id:
            return False, "任务ID缺失"
        return self.auditor.audit_goal(task.goal)