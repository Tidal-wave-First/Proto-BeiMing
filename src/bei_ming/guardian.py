import time

class Guardian:
    def __init__(self, cortex, dialectic_engine=None):
        self.cortex = cortex
        self.engine = dialectic_engine

    def enforce_capacity(self):
        current = self.cortex.current_size()
        if current <= self.cortex.max_bytes:
            return False, "容量正常"
        print(f">> 坐忘之守：皮层容量 {current/1e9:.2f}GB，启动遗忘...")
        mem = sorted(self.cortex.memory, key=self._score, reverse=False)
        target = current - self.cortex.max_bytes
        freed = 0
        removed = 0
        for m in mem[:]:
            if freed >= target: break
            if m['type'] == 'impression' and self._score(m) < 0.1:
                self.cortex.memory.remove(m)
                freed += m['size_estimate']
                removed += 1
            elif m['type'] == 'rule' and self.engine:
                m['importance'] *= 0.5
                freed += m['size_estimate'] * 0.5
            elif m['type'] == 'history' and time.time() - m['created_at'] > 7 * 86400:
                self.cortex.memory.remove(m)
                freed += m['size_estimate']
                removed += 1
        self.cortex._save()
        print(f">> 坐忘完成：遗忘 {removed} 条。")
        return True, f"遗忘 {removed} 条"

    def _score(self, item):
        age_days = (time.time() - item.get('last_accessed', item['created_at'])) / 86400
        recency = max(0, 1 - age_days / 30)
        freq = min(1.0, item.get('access_count', 0) / 10)
        importance = item.get('importance', 0.5)
        return 0.4 * recency + 0.3 * freq + 0.3 * importance
