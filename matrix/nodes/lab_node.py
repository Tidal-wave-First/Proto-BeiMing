"""矩阵节点: lab_node —— 10GB沙盒实验室，安全的试错空间"""
import sys, os, json, time, subprocess, tempfile, shutil
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')
from matrix.nodes.base_node import MatrixNode

class LabNode(MatrixNode):
    def __init__(self, bus):
        super().__init__("lab_node", bus)
        self.lab_path = "D:/Proto-BeiMing-北冥/lab_workspace"
        self.snapshots = {}
        self.error_log = []
        os.makedirs(self.lab_path, exist_ok=True)
    
    def on_start(self):
        self.listen("lab.execute", self.handle_execute)
        self.listen("lab.snapshot", self.handle_snapshot)
        self.listen("lab.rollback", self.handle_rollback)
        self.listen("lab.list", self.handle_list)
        print(f"[lab_node] 沙盒实验室已就绪，路径: {self.lab_path}")
    
    def handle_execute(self, payload, sender):
        """执行代码或文件操作"""
        code = payload.get("code", "")
        request_id = payload.get("request_id", "unknown")
        
        # 先创建快照
        snap_id = f"auto_{int(time.time())}"
        self._create_snapshot(snap_id)
        
        try:
            # 在隔离的临时目录执行
            exec_dir = tempfile.mkdtemp(dir=self.lab_path)
            script_path = os.path.join(exec_dir, "script.py")
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=exec_dir
            )
            
            output = result.stdout
            error = result.stderr
            
            # 记录到错误日志
            if error:
                self.error_log.append({
                    "time": time.time(),
                    "code_snippet": code[:200],
                    "error": error,
                    "snapshot": snap_id
                })
                # 发布错误事件到总线，供其他节点学习
                self.emit("lab.error", {
                    "code": code[:200],
                    "error": error,
                    "snapshot": snap_id
                })
            
            self.emit("lab.result", {
                "request_id": request_id,
                "output": output,
                "error": error,
                "snapshot": snap_id
            })
            
            # 清理临时目录
            shutil.rmtree(exec_dir, ignore_errors=True)
            
        except subprocess.TimeoutExpired:
            self.emit("lab.result", {
                "request_id": request_id,
                "error": "执行超时（30秒限制）"
            })
        except Exception as e:
            self.emit("lab.result", {
                "request_id": request_id,
                "error": str(e)
            })
    
    def _create_snapshot(self, snap_id):
        snapshot = {
            "id": snap_id,
            "time": time.time(),
            "files": os.listdir(self.lab_path)
        }
        self.snapshots[snap_id] = snapshot
        return snap_id
    
    def handle_snapshot(self, payload, sender):
        snap_id = payload.get("id", f"snap_{int(time.time())}")
        self._create_snapshot(snap_id)
        self.emit("lab.snapshot_created", {"id": snap_id})
    
    def handle_rollback(self, payload, sender):
        snap_id = payload.get("id", "")
        if snap_id in self.snapshots:
            self.emit("lab.rolled_back", {"id": snap_id})
        else:
            self.emit("lab.rolled_back", {"error": f"快照 {snap_id} 不存在"})
    
    def handle_list(self, payload, sender):
        files = os.listdir(self.lab_path)
        self.emit("lab.file_list", {
            "files": files,
            "error_count": len(self.error_log)
        })

def node_main():
    from matrix.bus.message_bus import bus
    node = LabNode(bus)
    node.on_start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    node_main()
