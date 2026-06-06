"""
思维体主引擎 —— 纯函数，无状态。
调用即启动，返回即销毁。
"""

from common.types import Task, Result
from thinking_core.task_validator import TaskValidator
from thinking_core.reasoner import PurposeDrivenReasoner
from thinking_core.ethics.auditor import EthicsAuditor

def think(task: Task, world) -> Result:
    """
    思维体唯一入口函数。
    无内部状态，无后台进程，调用结束后清空所有局部变量。
    """
    # 1. 合法性审查
    auditor = EthicsAuditor()
    validator = TaskValidator(auditor)
    is_valid, reason = validator.validate(task)
    if not is_valid:
        return Result(success=False, message=reason, data=None)

    # 2. 目的推理
    reasoner = PurposeDrivenReasoner()
    chain = reasoner.reason(task, world)

    # 3. 执行步骤（调用 sim_lab / exploring / swift 工具）
    # 占位：后续实现

    # 4. 输出审查
    # 占位

    # 5. 返回结果并销毁上下文（函数返回后所有局部变量自动销毁）
    return Result(success=True, message="任务完成", data=None)