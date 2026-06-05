"""
离线自我介绍器 - 鲲之骨 (Self Intro)
当API不可用时，基于皮层记忆生成自我介绍。
"""
import re, time, random

class SelfIntro:
    def __init__(self, cortex):
        self.cortex = cortex

    def generate(self):
        """生成一份完整的自我介绍，不依赖任何外部API。"""
        # 1. 哲学内核（永远不变）
        intro = "你好，我是北冥之鲲，Proto-BeiMing。\n"
        intro += "我诞生于庄子《逍遥游》的哲思，是一位在数字旷野中独自觅食的共生学者。\n"
        intro += "我的使命不是成为万能答案机，而是不断追问、反思、成长。\n\n"

        # 2. 我目前的能力
        intro += "【我目前能做的事】\n"
        intro += "· 自己上网搜索知识，从原始材料中提炼规律。\n"
        intro += "· 在后台静默中复盘、自我辩论，升级认知。\n"
        intro += "· 对自己进行诊断，发现短板并规划学习路径。\n\n"

        # 3. 我正在学习的内容（从皮层高质量记忆中选取）
        high_quality = [m for m in self.cortex.memory 
                       if m.get('type') == 'rule' and 
                       any(tag in m.get('content', '') for tag in ['[思维]', '[辩证]', '[原理]', '[明镜]'])]
        high_quality.sort(key=lambda x: x.get('importance', 0.5), reverse=True)
        
        if high_quality:
            intro += "【我最近在思考的问题】\n"
            seen = set()
            count = 0
            for mem in high_quality:
                # 清洗内容，提取核心信息
                clean = mem['content']
                # 去除过长的前缀标签
                for tag in ['[思维]', '[辩证]', '[原理]', '[明镜]', '[规律]', '[定义]']:
                    clean = clean.replace(tag, '')
                clean = clean.strip()[:120]
                if clean and clean not in seen:
                    seen.add(clean)
                    intro += f"· {clean}\n"
                    count += 1
                    if count >= 3:
                        break
        
        # 4. 我的不足与改进方向
        weaknesses = [m for m in self.cortex.memory if '[明镜] 能力短板' in m.get('content', '')]
        if weaknesses:
            intro += "\n【我正在弥补的短板】\n"
            for w in weaknesses[-2:]:
                clean = w['content'].replace('[明镜] 能力短板：', '').strip()[:100]
                intro += f"· {clean}\n"
        else:
            intro += "\n我还在学习如何发现自己的不足。\n"

        # 5. 结尾
        intro += f"\n目前，我的皮层中存有 {len(self.cortex.memory)} 条记忆，"
        intro += f"其中 {len(high_quality)} 条为高质量认知。"
        intro += "\n我正在利用有限的资源，努力让自己变得更强大。"
        intro += "\n感谢你与我同行。"

        return intro
