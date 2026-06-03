"""
鲲核 - 北冥之心 (Kun Core)
后台常驻进程，无需浏览器，静默思考。
"""
import sys, os, yaml, time, signal, atexit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.bei_ming.chat import ChatSession
from src.bei_ming.background import BackgroundDigestor
from src.bei_ming.autonomous_explorer import AutonomousExplorer
from src.bei_ming.dreamer import Dreamer
import src.bei_ming.senses as senses_mod

class KunCore:
    def __init__(self):
        with open('config.yaml', 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.session = ChatSession(self.config)
        self.bg_digestor = BackgroundDigestor(self.session.engine, socketio=None, interval_seconds=20)
        self.wings = senses_mod._wings
        self.explorer = None
        if self.wings:
            self.explorer = AutonomousExplorer(
                wings=self.wings,
                imagination=self.session.imagination,
                engine=self.session.engine,
                cortex=self.session.cortex,
                socketio=None,
                interval_minutes=30
            )
        self.dreamer = Dreamer(
            cortex=self.session.cortex,
            imagination=self.session.imagination,
            engine=self.session.engine,
            socketio=None,
            idle_threshold=600,
            interval=300
        )
        self.running = False

    def start(self):
        self.running = True
        self.bg_digestor.start()
        if self.explorer:
            self.explorer.start()
        self.dreamer.start()
        print(">> 鲲核已启动，开始静默思考。")
        # 主循环，保持进程存活
        while self.running:
            time.sleep(10)

    def stop(self, *args):
        print(">> 正在关闭鲲核...")
        self.running = False
        self.bg_digestor.stop()
        if self.explorer:
            self.explorer.stop()
        self.dreamer.stop()
        # 保存皮层快照
        self.session.cortex._save()
        print(">> 鲲核已休眠。")

if __name__ == "__main__":
    core = KunCore()
    atexit.register(core.stop)
    signal.signal(signal.SIGINT, core.stop)
    signal.signal(signal.SIGTERM, core.stop)
    core.start()
