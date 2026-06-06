"""
目的导向推理引擎。
不进行自由探索，所有推理步骤必须绑定到 Task.goal。
"""

from common.types import Task, ThoughtChain, ThoughtStep

class PurposeDrivenReasoner:
    MAX_STEPS = 100
    MAX_HYPOTHESES = 3  # 最多生成3个候选方案

    def reason(self, task: Task, world_state) -> ThoughtChain:
        chain = ThoughtChain(task=task, steps=[], max_steps=self.MAX_STEPS)

        # 步骤1：查询可用零件/原语（从 sim_lab）
        # 步骤2：生成候选假设（每个假设都必须标注如何服务于 goal）
        # 步骤3：选最优假设，生成执行步骤
        # 步骤4：为每一步标注 purpose

        # 占位实现：返回一个空链
        return chain