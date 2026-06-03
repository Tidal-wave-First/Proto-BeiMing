"""
梦境引擎 - 北冥之梦 (Dreamer)
在系统空闲时对皮层记忆进行深度抽象、矛盾检测、错误修正。
"""
import time
import threading
import ollama
import random

class Dreamer:
    def __init__(self, cortex, imagination, engine, socketio=None,
                 idle_threshold=600, interval=300):
        """
        idle_threshold: 用户空闲多久（秒）后允许做梦，默认10分钟
        interval: 梦境检查周期（秒），默认5分钟
        """
        self.cortex = cortex
        self.imagination = imagination
        self.engine = engine  # 需要用到其中的LLM调用方法
        self.socketio = socketio
        self.idle_threshold = idle_threshold
        self.interval = interval
        self.last_user_activity = time.time()
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

    def update_activity(self):
        """用户有交互时调用，重置空闲计时"""
        self.last_user_activity = time.time()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        self._emit("梦境引擎已启动，鲲将在静默中思索。")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _emit(self, msg):
        if self.socketio:
            try:
                self.socketio.emit('digest_log', {'message': f'[梦] {msg}'})
            except:
                pass
        print(f"[梦] {msg}")

    def _loop(self):
        time.sleep(30)  # 启动后等待30秒再开始检测
        while self.running:
            idle_time = time.time() - self.last_user_activity
            # 条件：空闲超时，且想象空间为空（没有急待处理的新材料）
            if idle_time >= self.idle_threshold and len(self.imagination) == 0:
                self._dream()
            time.sleep(self.interval)

    def _dream(self):
        """执行一次梦境处理"""
        # 获取最近24小时内的皮层记忆
        recent_memories = self._get_recent_memories(hours=24)
        if len(recent_memories) < 3:
            return  # 记忆太少，无法做梦

        self._emit(f"进入梦境，回放 {len(recent_memories)} 段记忆...")

        # 1. 矛盾检测
        contradictions = self._detect_contradictions(recent_memories)
        if contradictions:
            self._emit(f"发现 {len(contradictions)} 处潜在矛盾，进行辩证扬弃。")
            for old, new in contradictions:
                # 调用引擎的扬弃方法（会调用LLM融合）
                self.engine._dialectical_sublation(
                    new['content'], "梦境矛盾检测", [old]
                )

        # 2. 抽象升华：随机抽取3条规律，尝试归纳为更高原则
        rules = [m for m in recent_memories if m.get('type') == 'rule']
        if len(rules) >= 3:
            sample = random.sample(rules, min(3, len(rules)))
            self._abstract_upgrade(sample)

        # 3. 错误修正：对低重要性、待验证的结论重新审查
        uncertain = [m for m in recent_memories 
                     if m.get('type') in ('history', 'impression') 
                     and m.get('importance', 0) < 0.5]
        for mem in uncertain[:3]:
            self._re_evaluate(mem)

        self._emit("梦境结束，认知已巩固。")

    def _get_recent_memories(self, hours=24):
        cutoff = time.time() - hours * 3600
        return [m for m in self.cortex.memory 
                if m.get('last_accessed', m.get('created_at', 0)) > cutoff]

    def _detect_contradictions(self, memories):
        """让LLM寻找记忆间的矛盾"""
        # 简化为：随机配对，让LLM判断是否矛盾
        if len(memories) < 2:
            return []
        pairs = []
        contents = [m.get('content', '') for m in memories]
        for i in range(min(3, len(memories)//2)):
            a = random.choice(memories)
            b = random.choice(memories)
            if a['id'] != b['id']:
                pairs.append((a, b))
        contradictions = []
        for a, b in pairs[:2]:  # 最多检查2对
            prompt = f"""判断以下两条知识是否存在逻辑矛盾。如果存在，请指出矛盾点；如果不存在，回复“无矛盾”。
知识A: {a.get('content', '')}
知识B: {b.get('content', '')}
请直接回复“矛盾：...”或“无矛盾”。"""
            try:
                resp = ollama.generate(model="qwen2.5:7b", prompt=prompt)
                result = resp['response'].strip()
                if result.startswith("矛盾"):
                    contradictions.append((a, b))
                    self._emit(f"矛盾对: {a['content'][:30]}... <-> {b['content'][:30]}...")
            except:
                pass
        return contradictions

    def _abstract_upgrade(self, rules):
        contents = "; ".join([r.get('content', '') for r in rules])
        prompt = f"""将以下几条认知规律归纳成一个更通用的底层原则。用一句精炼的话表述。
规律：{contents}
原则："""
        try:
            resp = ollama.generate(model="qwen2.5:7b", prompt=prompt)
            principle = resp['response'].strip()
            if principle and len(principle) > 5:
                self.cortex.store(
                    content=f"[梦境升华] {principle}",
                    ktype="rule",
                    importance=0.95
                )
                self._emit(f"抽象升华：{principle}")
                # 降低原规律的重要性
                for r in rules:
                    r['importance'] *= 0.7
                self.cortex._save()
        except Exception as e:
            self._emit(f"抽象升华失败: {e}")

    def _re_evaluate(self, memory):
        """对单个不确定记忆进行二次验证"""
        prompt = f"""请评估以下认知的可靠性和普适性。如果它可能错误或过于片面，请指出问题；如果正确，回复“可靠”。
认知：{memory.get('content', '')}
评估："""
        try:
            resp = ollama.generate(model="qwen2.5:7b", prompt=prompt)
            eval_result = resp['response'].strip()
            if "可靠" not in eval_result:
                # 标记为有疑问，降低重要性
                memory['importance'] *= 0.3
                self.cortex._save()
                self._emit(f"修正记忆: {memory['content'][:30]}... -> 存疑")
        except:
            pass
