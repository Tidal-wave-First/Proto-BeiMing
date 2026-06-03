import time, threading

class BackgroundDigestor:
    def __init__(self, engine, socketio=None, interval_seconds=20):
        self.engine = engine
        self.socketio = socketio
        self.interval = interval_seconds
        self.running = False
        self.thread = None

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread: self.thread.join()

    def _loop(self):
        while self.running:
            if self.engine.has_fresh_material():
                materials = self.engine.imagination.get_recent(10)
                novelty = self.engine.compute_novelty(materials)
                if novelty > 0.3:
                    conclusions = self.engine.digest()
                    if conclusions and self.socketio:
                        self.socketio.emit('digest_log', {'message': f'后台消化完成，产生 {len(conclusions)} 条认知。'})
            time.sleep(self.interval)
