"""
梦境引擎 - 无 LLM 回退版
"""
import time
import threading
import random

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

class Dreamer:
    def __init__(self, cortex, imagination, engine, socketio=None, idle_threshold=600, interval=300):
        self.cortex = cortex
        self.imagination = imagination
        self.engine = engine
        self.socketio = socketio
        self.idle_threshold = idle_threshold
        self.interval = interval
        self.last_user_activity = time.time()
        self.running = False
        self.thread = None

    def update_activity(self):
        self.last_user_activity = time.time()

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread: self.thread.join()

    def _emit(self, msg):
        if self.socketio:
            self.socketio.emit('digest_log', {'message': f'[梦] {msg}'})

    def _loop(self):
        time.sleep(30)
        while self.running:
            if time.time() - self.last_user_activity >= self.idle_threshold and len(self.imagination) == 0:
                self._dream()
            time.sleep(self.interval)

    def _dream(self):
        recent = [m for m in self.cortex.memory if m.get('last_accessed', m.get('created_at', 0)) > time.time() - 86400]
        if len(recent) < 3: return
        rules = [m for m in recent if m['type'] == 'rule']
        if len(rules) >= 3:
            sample = random.sample(rules, 3)
            contents = "; ".join([r['content'] for r in sample])
            if HAS_OLLAMA:
                try:
                    prompt = f"将以下规律归纳为一句通用原则：\n{contents}\n原则："
                    resp = ollama.generate(model="qwen2.5:7b", prompt=prompt)
                    principle = resp['response'].strip()
                    if principle:
                        self.cortex.store(content=f"[梦境升华] {principle}", ktype="rule", importance=0.95)
                        self._emit(f"抽象升华：{principle}")
                except:
                    pass
            else:
                combined = " + ".join([r['content'][:50] for r in sample])
                self.cortex.store(content=f"[梦境归纳] {combined}", ktype="rule", importance=0.6)
                self._emit("梦境归纳完成（无LLM模式）")
