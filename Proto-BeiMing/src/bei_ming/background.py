"""
后台消化线程 - 坐忘潜行（带推送日志）
"""
import time
import threading

class BackgroundDigestor:
    def __init__(self, engine, socketio=None, interval_seconds=30):
        self.engine = engine
        self.socketio = socketio
        self.interval = interval_seconds
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        self._emit("坐忘潜行已启动，鲲将在后台默默思考。")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _emit(self, msg):
        if self.socketio:
            try:
                self.socketio.emit('digest_log', {'message': msg})
            except:
                pass  # 忽略推送错误
        print(msg)  # 终端也保留

    def _loop(self):
        while self.running:
            if len(self.engine.imagination) >= 3:
                self._emit("想象空间材料充足，开始消化...")
                # 在消化前，复制一份材料列表用于日志
                materials = self.engine.imagination.get_recent(5)
                self._emit(f"正在咀嚼 {len(materials)} 条材料")
                # 执行消化（内部会调用LLM并自我反思）
                conclusions = self.engine.digest()
                if conclusions:
                    for hyp, res in conclusions:
                        self._emit(f"假设: {hyp[:40]}... -> {res[:40]}...")
                self._emit("坐忘反思完成，皮层已更新。")
            time.sleep(self.interval)
