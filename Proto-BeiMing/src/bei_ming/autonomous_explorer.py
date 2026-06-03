"""
自主探索引擎 - 怒飞 (Autonomous Explorer)
在无用户交互时，根据皮层知识缺口主动搜索互联网，消化并成长。
"""
import time
import threading
import ollama

class AutonomousExplorer:
    def __init__(self, wings, imagination, engine, cortex, socketio=None,
                 interval_minutes=30, max_per_cycle=3):
        self.wings = wings
        self.imagination = imagination
        self.engine = engine
        self.cortex = cortex
        self.socketio = socketio
        self.interval = interval_minutes * 60  # 转换为秒
        self.max_per_cycle = max_per_cycle
        self.running = False
        self.thread = None
        self.explored_topics = set()  # 防止重复探索
        self.lock = threading.Lock()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        self._emit("怒飞已启动，鲲将自主探索未知领域。")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _emit(self, msg):
        if self.socketio:
            try:
                self.socketio.emit('digest_log', {'message': f'[怒飞] {msg}'})
            except:
                pass
        print(f"[怒飞] {msg}")

    def _loop(self):
        # 初次等待 10 秒，让系统稳定
        time.sleep(10)
        while self.running:
            try:
                self._explore_cycle()
            except Exception as e:
                self._emit(f"探索周期异常: {e}")
            time.sleep(self.interval)

    def _explore_cycle(self):
        topics = self._generate_exploration_topics()
        if not topics:
            self._emit("皮层尚浅，暂无明确探索方向，继续守望。")
            return

        for topic in topics[:self.max_per_cycle]:
            if topic in self.explored_topics:
                continue
            self.explored_topics.add(topic)
            self._emit(f"自主探索主题: {topic}")
            try:
                count = self.wings.explore(topic, max_results=3)
                if count > 0:
                    self._emit(f"捕获 {count} 条材料，开始消化...")
                    with self.lock:
                        conclusions = self.engine.digest(focus_question=topic)
                    if conclusions:
                        self._emit(f"消化完成，产生 {len(conclusions)} 条认知。")
                else:
                    self._emit("未捕获到材料。")
            except Exception as e:
                self._emit(f"探索 '{topic}' 失败: {e}")
            # 每次探索后短暂休息，避免请求过快
            time.sleep(5)

    def _generate_exploration_topics(self):
        """根据皮层已有知识，利用LLM生成值得探索的主题"""
        # 收集皮层中的记忆摘要
        memory_summaries = []
        for mem in self.cortex.memory[-20:]:  # 最近20条记忆
            memory_summaries.append(mem.get('content', '')[:100])
        if not memory_summaries:
            # 皮层空空，从本地后备知识或预设种子开始
            return ["人工智能", "哲学", "认知科学"]

        joined = "\n".join(memory_summaries)
        prompt = f"""你是一个自主学习者，需要决定下一步学习什么。
你目前已知的知识片段：
{joined}

请根据这些已有知识，提出 2 个你尚不了解但值得探索的主题。主题应简明扼要，适合网络搜索。
直接输出主题，每行一个，不要编号。"""
        try:
            resp = ollama.generate(model="qwen2.5:7b", prompt=prompt)
            lines = resp['response'].strip().split('\n')
            topics = [line.strip('- ').strip() for line in lines if line.strip()]
            return topics[:2]
        except Exception as e:
            self._emit(f"生成探索主题失败: {e}")
            # 回退：随机选择一个基础主题
            fallback = ["认知偏差", "逻辑谬误", "科学方法", "系统思维", "博弈论"]
            import random
            return random.sample(fallback, min(2, len(fallback)))
