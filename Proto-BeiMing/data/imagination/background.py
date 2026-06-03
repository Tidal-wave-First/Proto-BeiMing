"""
后台消化线程 - 坐忘潜行
定期检查想象空间，自动进行辩证消化，让鲲在静默中成长。
"""
import time
import threading

class BackgroundDigestor:
    def __init__(self, engine, interval_seconds=30):
        self.engine = engine
        self.interval = interval_seconds
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(">> 坐忘潜行已启动，鲲将在后台默默思考。")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _loop(self):
        while self.running:
            if len(self.engine.imagination) >= 3:
                print("\n>> 后台消化触发...")
                self.engine.digest()
            time.sleep(self.interval)