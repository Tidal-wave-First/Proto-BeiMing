"""
成长看板 - 鲲之羽书 (Dashboard)
提供皮层统计、最近消化、API消耗等数据。
"""
import os
import time
import json

STATS_FILE = "stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    return {"total_tokens": 0, "total_calls": 0, "digest_history": []}

def save_stats(stats):
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, ensure_ascii=False)

def record_digest(topic, token_cost):
    """每次API消化后调用，记录消耗"""
    stats = load_stats()
    stats["total_tokens"] += token_cost
    stats["total_calls"] += 1
    stats["digest_history"].append({
        "topic": topic,
        "tokens": token_cost,
        "time": time.strftime("%m-%d %H:%M")
    })
    # 只保留最近50条
    stats["digest_history"] = stats["digest_history"][-50:]
    save_stats(stats)

def get_status(cortex):
    """生成看板数据"""
    stats = load_stats()
    memory_count = len(cortex.memory)
    # 按类型统计
    rules = [m for m in cortex.memory if m['type']=='rule']
    impressions = [m for m in cortex.memory if m['type']=='impression']
    # 最近消化主题
    last_topics = [d['topic'] for d in stats['digest_history'][-5:]]
    
    return {
        "皮层记忆总数": memory_count,
        "规律数量": len(rules),
        "印象数量": len(impressions),
        "API调用次数": stats["total_calls"],
        "消耗Token总量": stats["total_tokens"],
        "最近消化主题": last_topics,
        "最近消化记录": stats["digest_history"][-5:]
    }
