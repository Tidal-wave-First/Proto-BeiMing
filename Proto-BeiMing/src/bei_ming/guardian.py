"""
守护进程 - 坐忘之守（取自“堕肢体，黜聪明，离形去知，同于大通”）
监控北冥之渊容量，过限则忘，忘不是毁灭，是扬弃。
遗忘策略：低重要度淘汰、同类印象合并、过时规则升华。
"""
import time
from .dialectic_engine import DialecticEngine  # 需要扬弃时调用

class Guardian:
    def __init__(self, cortex, dialectic_engine=None):
        self.cortex = cortex
        self.engine = dialectic_engine

    def enforce_capacity(self):
        """检查皮层容量，若超10GB则触发遗忘流程"""
        current = self.cortex.current_size()
        if current <= self.cortex.max_bytes:
            return False, "容量正常"
        
        print(f">> 坐忘之守：皮层容量 {current/1e9:.2f}GB，已过限，启动遗忘...")
        # 获取所有记忆并排序
        mem = sorted(self.cortex.memory, key=self._score, reverse=False)  # 升序，分低的在前
        removed_count = 0
        # 目标：至少释放超限部分的空间
        target = current - self.cortex.max_bytes
        freed = 0

        for m in mem[:]:
            if freed >= target:
                break
            # 直接移除重要性极低且很久未访问的印象
            if m['type'] == 'impression' and self._score(m) < 0.1:
                self.cortex.memory.remove(m)
                freed += m['size_estimate']
                removed_count += 1
                continue
            # 对于规律，尝试请求辩证引擎合并（若引擎可用）
            if m['type'] == 'rule' and self.engine is not None:
                # 寻找其他相似规律尝试扬弃（伪逻辑：这里实际可调用LLM进行抽象）
                # 简化：直接降低重要性，下次再忘
                m['importance'] *= 0.5
                freed += m['size_estimate'] * 0.5  # 估算释放（重要性降低后可能被后续淘汰）
            # 实验历史：保留最近N条，删除旧的
            if m['type'] == 'history' and time.time() - m['created_at'] > 7 * 86400:
                self.cortex.memory.remove(m)
                freed += m['size_estimate']
                removed_count += 1

        # 保存改变后的皮层
        self.cortex._save()
        new_size = self.cortex.current_size()
        print(f">> 坐忘完成：移除了 {removed_count} 条低分记忆，当前容量 {new_size/1e9:.2f}GB")
        return True, f"遗忘 {removed_count} 条，释放约 {freed/1e6:.1f}MB"

    def _score(self, memory_item):
        """计算记忆的重要性分数（0-1），用于遗忘排序"""
        age_days = (time.time() - memory_item.get('last_accessed', memory_item['created_at'])) / 86400
        recency = max(0, 1 - age_days / 30)  # 30天后归零
        freq = min(1.0, memory_item.get('access_count', 0) / 10)
        importance = memory_item.get('importance', 0.5)
        # 加权得分，越高越不容易被遗忘
        return 0.4 * recency + 0.3 * freq + 0.3 * importance
