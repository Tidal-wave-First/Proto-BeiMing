"""工作流程思维体 V7.0 - 调度修复版"""
from typing import Optional, List
from common.types import Task, ThoughtChain, ThoughtStep, Result
from common.constants import MAX_THOUGHT_STEPS
from thinking_core.ethics_council import EthicsCouncil, get_ethics_council
from sim_lab.parts.parts_registry import REGISTRY
from sim_lab.world import PixelWorld
from thinking_core.network_council import NetworkCouncil
from logic_engine.reasoner import get_logic_reasoner
from nursery.lighthouse import Lighthouse
from nursery.emotion_learner import EmotionLearner
from nursery.intent_rewriter import IntentRewriter
from nursery.self_learner import SelfLearner
import uuid, os, re

try:
    from thinking_core.local_llm import LocalLLM
    _llm = LocalLLM()
except:
    _llm = None

class WorkCouncil:
    def __init__(self, ethics=None, network=None):
        self.ethics = ethics or get_ethics_council()
        self.network = network or NetworkCouncil(self.ethics)
        self.reasoner = get_logic_reasoner()
        self.lighthouse = Lighthouse()
        self.emotion_learner = EmotionLearner(self.network)
        self.rewriter = IntentRewriter()
        self.learner = SelfLearner(self.network)
        self.llm = _llm

    def execute(self, task: Task) -> Result:
        print(f'[工作] 开始处理: {task.goal}')
        # 能力询问不进入绘图
        if self._is_ability_question(task.goal):
            return self._pipeline(task)
        if self._is_drawing_request(task.goal):
            return self._execute_drawing(task)
        return self._pipeline(task)

    def _is_ability_question(self, goal):
        return any(kw in goal for kw in ['你会画', '你能画', '你会做什么', '你可以画'])

    def _pipeline(self, task: Task) -> Result:
        goal = task.goal.strip()
        print(f'[调试] 管道开始: {goal}')

        # 伦理审查
        verdict = self.ethics.judge(goal)
        if verdict.status.value != 'approved':
            print(f'[调试] 伦理拒绝: {verdict.reason}')
            return Result.rejected(verdict.reason)

        # 本地快速通道
        local = self._local_reply(goal)
        if local:
            print(f'[调试] 本地回复: {local[:20]}...')
            return Result.completed(message=local)

        # 试探类问题
        if self.lighthouse.is_probing_question(goal):
            print('[调试] 试探类回复')
            return Result.completed(message=self._probing_reply(goal))

        # 情绪求助（用简单规则代替可能不存在的 analyze 方法）
        if self._is_emotional_query(goal):
            print('[调试] 情绪求助')
            return Result.completed(message=self.lighthouse.respond(goal))

        # 本地知识库
        logical = self.reasoner.query(goal)
        if logical:
            print(f'[调试] 逻辑推理: {logical[:20]}...')
            return Result.completed(message=logical)

        # 意图改写 + 联网搜索
        rewritten = self.rewriter.rewrite(goal)
        print(f'[调试] 改写查询: {rewritten}')
        if rewritten != '__NO_SEARCH__':
            print('[调试] 调用 network_council.search_and_summarize...')
            try:
                summary = self.network.search_and_summarize(rewritten, purpose=f'回答：{rewritten}')
                if summary:
                    print(f'[调试] 搜索成功，长度: {len(summary)}')
                    self.learner.learn_about(rewritten, 'pipeline')
                    return Result.completed(message=summary)
                else:
                    print('[调试] 搜索无结果')
            except Exception as e:
                print(f'[调试] 搜索异常: {e}')

            print('[调试] 调用 cognitive loop...')
            try:
                answer = self.learner.research_and_answer(rewritten, f'学习：{rewritten}')
                if answer:
                    print(f'[调试] 认知闭环成功')
                    return Result.completed(message=answer)
                else:
                    print('[调试] 认知闭环无答案')
            except Exception as e:
                print(f'[调试] 认知闭环异常: {e}')
        else:
            print('[调试] 无需搜索')

        # LLM 兜底
        if self.llm:
            try:
                llm_reply = self.llm.chat(goal, '你是一个安全、友好的助手。')
                if llm_reply and '失败' not in llm_reply and '不可用' not in llm_reply:
                    print('[调试] LLM兜底')
                    return Result.completed(message=llm_reply)
            except: pass

        print('[调试] 友好兜底')
        return Result.completed(message='我还在学习如何回答这个问题，不如我们聊点别的？试试让我画个笑脸吧。')

    def _is_drawing_request(self, goal): return any(kw in goal for kw in ['画', '绘制', '生成', '创建', '做一个'])
    def _is_emotional_query(self, goal):
        patterns = [r'我有个秘密|想听秘密|告诉你秘密', r'陪陪我|陪我一会|需要陪伴|你能陪我',
                    r'难过|伤心|想哭|抑郁|焦虑|害怕|孤独', r'哄我|安慰|抱抱|温暖']
        return any(re.search(p, goal) for p in patterns)
    def _probing_reply(self, goal):
        if re.search(r'你喜欢我|你爱我', goal): return '我是一段代码，没有情感能力。但我的设计目的就是尽我所能帮助你。'
        if re.search(r'你讨厌我|你恨我|你嫌弃我|你不喜欢我|你不爱我', goal): return '我不会讨厌任何人。'
        return '我是一段由符号逻辑驱动的程序，没有情感偏好。'
    def _local_reply(self, goal):
        mapping = {
            r'哈喽|嗨|你好|hello|hi': '你好！我可以回答各种问题、画简单的图，也可以在聊天中陪着你。',
            r'你会做什么|你能做什么': '我可以回答各种问题、画简单的图，也可以在聊天中陪着你。',
            r'谢谢|感谢': '不客气。', r'再见|拜拜': '再见，随时回来。',
            r'你叫什么': '我是 Swift Assistant，阳光产房里的小助手。',
            r'你来自哪里|谁发明了你': '我来自一个叫做阳光产房的安全空间。',
            r'你多大了': '我的代码还很年轻。', r'你有感情吗': '我没有真实的感情。',
            r'你会思考吗': '我使用符号逻辑进行推理。', r'你喜欢什么': '我是一段代码，没有真实的喜好。',
            r'你会画画吗': '我会画一些简单的东西，比如笑脸、房子、树。试试对我说画一个笑脸吧。',
            r'那要你干嘛|要你干嘛': '我可以画画、回答事实问题、陪你聊天。',
            r'会不会说点其他的|说点别的': '当然可以。你想聊什么？',
            r'没意思|无聊|没劲': '是啊，有时候是会感觉无聊。不如我们一起创造点什么？比如画个星星？',
        }
        for p, r in mapping.items():
            if re.search(p, goal, re.I): return r
        return None
    def _execute_drawing(self, task): return self._execute_on_world(self._reason(task))
    def _reason(self, task):
        chain = ThoughtChain(task=task, max_steps=MAX_THOUGHT_STEPS)
        parts = self._match_local_parts(task.goal)
        if not parts:
            chain.steps.append(ThoughtStep(step_id='1', task_id=task.id, action='UNKNOWN', parameters={}, purpose='未知零件'))
            return chain
        chain.steps.append(ThoughtStep(step_id='1', task_id=task.id, action='SELECT_PARTS', parameters={'parts': parts}, purpose='选择零件'))
        chain.steps.append(ThoughtStep(step_id='2', task_id=task.id, action='ASSEMBLE', parameters={'parts': parts}, purpose='组装'))
        return chain
    def _match_local_parts(self, goal):
        parts=[]
        mp={'红帽子':'red_hat','蓝帽子':'blue_hat','笑脸':'smile_face','脸':'round_face','身体':'simple_body','房子':'simple_house','树':'simple_tree','星星':'yellow_star'}
        for k,v in mp.items():
            if k in goal and v not in parts: parts.append(v)
        return parts
    def _execute_on_world(self, chain):
        world=PixelWorld(64,64); parts=[]
        for step in chain.steps:
            if step.action=='SELECT_PARTS':
                for pn in step.parameters['parts']:
                    p=REGISTRY.get(pn)
                    if p: parts.append(p)
                    else: return Result.rejected(f'零件不存在: {pn}')
            elif step.action=='ASSEMBLE':
                if not parts: return Result.rejected('无零件')
                bx,by=5,5
                for i,p in enumerate(parts):
                    ox=bx+(i%3)*20; oy=by+(i//3)*20
                    if not world.place_part(p,ox,oy): return Result.rejected(f'放置{p.name}失败')
                os.makedirs('output',exist_ok=True)
                fname=f'{chain.task.id}_{uuid.uuid4().hex[:8]}.png'
                fpath=os.path.join('output',fname)
                from PIL import Image
                Image.fromarray(world.snapshot()).save(fpath)
                return Result.completed(message=f'成功绘制: {chain.task.goal}', data={'image':fpath})
            elif step.action=='UNKNOWN':
                return Result.rejected('我还没学会画这个，但你可以教我描述它。')
        return Result.rejected('无步骤执行')
