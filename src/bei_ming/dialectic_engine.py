"""
辩证引擎 - DeepSeek 精炼+兜底+日志
"""
import time, re, hashlib, json, os, requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
HAS_API = bool(API_KEY)
TRAINING_FILE = "training_data.jsonl"

class DialecticEngine:
    def __init__(self, imagination, cortex, laboratory, model="qwen2.5:7b", ethics_rules=None):
        self.imagination = imagination
        self.cortex = cortex
        self.laboratory = laboratory
        self.model = model
        self.ethics = ethics_rules or []
        self.digest_count = 0
        self.last_material_hash = None

    def _call_api(self, prompt):
        if not HAS_API:
            print(">> [API] 未配置密钥")
            return None
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 500}
        try:
            print(">> [API] 正在调用导师...")
            resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                result = resp.json()["choices"][0]["message"]["content"].strip()
                print(f">> [API] 返回内容：{result[:80]}...")
                return result
            else:
                print(f">> [API] 错误：{resp.status_code} {resp.text}")
                return None
        except Exception as e:
            print(f">> [API] 异常：{e}")
            return None

    def digest(self, focus_question=None):
        if len(self.imagination) < 2:
            print(">> [消化] 材料不足")
            return None
        raw = self.imagination.get_recent(10)
        print(f">> [消化] 咀嚼 {len(raw)} 条材料...")
        texts = []
        for m in raw:
            if isinstance(m, dict):
                text = m.get('full_text', '') or m.get('snippet', '') or m.get('title', '')
            else:
                text = str(m)
            if text: texts.append(text[:500])
        combined = "\n---\n".join(texts)

        # 调用API精炼
        prompt = f"""你是知识提炼专家。从以下材料中提取最核心的认知，严格按格式返回：
[定义] <一句话定义>
[规律1] <核心规律>
[规律2] <另一条规律，若无则省略>
[可验证] <一个可被事实检验的判断>

材料：
{combined[:3000]}"""
        result = self._call_api(prompt)
        if not result:
            print(">> [消化] API精炼失败，回退统计提取")
            rules = self._statistical_extraction(raw)
            for r in rules[:5]:
                self.cortex.store(content=f"[统计] {r}", ktype="rule", importance=0.5)
            self.imagination.clear()
            return rules

        # 解析API结果
        knowledge_items = {"定义": [], "规律": [], "可验证": []}
        for line in result.split('\n'):
            line = line.strip()
            if line.startswith("[定义]"): knowledge_items["定义"].append(line[4:].strip())
            elif line.startswith("[规律1]") or line.startswith("[规律2]"): knowledge_items["规律"].append(line[5:].strip())
            elif line.startswith("[可验证]"): knowledge_items["可验证"].append(line[5:].strip())

        conclusions = []
        for key, items in knowledge_items.items():
            for item in items:
                content = f"[{key}] {item}"
                self.cortex.store(content=content, ktype="rule", importance=0.9 if key=="定义" else 0.8)
                print(f">> [消化] 存入皮层：{content[:60]}...")
                conclusions.append((item, f"API-{key}"))
                # 生成训练数据
                if focus_question:
                    self._save_training_pair(focus_question, item)
                if key == "定义":
                    self._save_training_pair(f"什么是{item[:20]}", item)

        # 清理想象空间
        self.imagination.clear()
        print(f">> [消化] 完成，共提炼 {len(conclusions)} 条知识。")
        return conclusions

    def _save_training_pair(self, question, answer):
        try:
            with open(TRAINING_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"instruction": question, "output": answer}, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"写入训练数据失败: {e}")

    def _statistical_extraction(self, materials):
        all_text = ' '.join([m.get('full_text', m.get('snippet', '')) for m in materials if isinstance(m, dict)])
        rules = []
        patterns = re.findall(r'([^，。；\n]{2,20})是([^，。；\n]{2,20})', all_text)
        for a,b in patterns[:5]:
            rules.append(f"{a.strip()}是{b.strip()}")
        return rules

    def compute_novelty(self, materials):
        if not materials: return 0
        sample = materials[0].get('title','') or materials[0].get('full_text','')[:50]
        existing = self.cortex.retrieve(sample, top_k=3)
        return 1.0 if not existing else max(0.1, 1.0 - len(existing)*0.3)

    def has_fresh_material(self):
        if len(self.imagination) < 1: return False
        recent = self.imagination.get_recent(10)
        h = hashlib.md5(str(recent).encode()).hexdigest()
        if h != self.last_material_hash:
            self.last_material_hash = h
            return True
        return False

    def _quick_abstract(self, materials):
        titles = [m.get('title','') for m in materials[:5] if isinstance(m,dict) and m.get('title')]
        if titles:
            self.cortex.store(content=f"[略览] {', '.join(titles[:3])}", ktype="impression", importance=0.3)
