"""
自主探索引擎 - 怒飞（好奇心驱动版）
优先使用皮层概念网络找出知识缺口，生成高质量探索主题。
"""
import time
import threading
import ollama
import random
from .curiosity import CuriosityEngine

class AutonomousExplorer:
    def __init__(self, wings, imagination, engine, cortex, socketio=None,
                 interval_minutes=30, max_per_cycle=3):
        self.wings = wings
        self.imagination = imagination
        self.engine = engine
        self.cortex = cortex
        self.socketio = socketio
        self.interval = interval_minutes * 60
        self.max_per_cycle = max_per_cycle
        self.running = False
        self.thread = None
        self.explored_topics = set()
        self.lock = threading.Lock()
        self.curiosity = CuriosityEngine(cortex)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        self._emit("怒飞已启动，鲲将以好奇心探索未知。")

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
        time.sleep(10)
        while self.running:
            try:
                self._explore_cycle()
            except Exception as e:
                self._emit(f"探索周期异常: {e}")
            time.sleep(self.interval)

    def _explore_cycle(self):
        # 优先使用好奇心引擎生成主题
        topics = self.curiosity.generate_topics(self.max_per_cycle)
        if not topics:
            topics = self._fallback_topics()
            self._emit("好奇心引擎未产生主题，使用备用方案。")
        else:
            self._emit(f"好奇心驱动主题: {', '.join(topics)}")

        for topic in topics[:self.max_per_cycle]:
            if topic in self.explored_topics:
                continue
            self.explored_topics.add(topic)
            self._emit(f"自主探索: {topic}")
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
            time.sleep(5)

    def _fallback_topics(self):
        """好奇心引擎失败时的备用方案：LLM生成或随机种子"""
        # 尝试用LLM根据皮层最近记忆生成
        memory_summaries = [m.get('content', '')[:100] for m in self.cortex.memory[-20:]]
        if memory_summaries:
            joined = "\n".join(memory_summaries)
            prompt = f"""你已知的知识片段：
{joined}
请提出 2 个值得探索的新主题，每行一个："""
            try:
                resp = ollama.generate(model="qwen2.5:7b", prompt=prompt)
                lines = resp['response'].strip().split('\n')
                topics = [line.strip('- ').strip() for line in lines if line.strip()]
                if topics:
                    return topics[:2]
            except:
                pass
        # 最终随机种子
        seeds = ["人工智能伦理", "认知科学", "系统动力学", "信息熵", "自组织临界性"]
        random.shuffle(seeds)
        return seeds[:2]
