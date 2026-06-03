"""
工具模块 - 鲲之鳞爪
提供容量估算、安全校验等基础能力。
"""
import os
import sys

def estimate_size(obj, seen=None):
    """递归估算Python对象的内存占用（字节），用于容量控制"""
    seen = seen or set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        size += sum(estimate_size(k, seen) + estimate_size(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(estimate_size(i, seen) for i in obj)
    return size

def dir_size(path):
    """估算目录内所有文件的总大小（字节）"""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total
