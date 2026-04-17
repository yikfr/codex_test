import json
from typing import List, Dict, Any, Optional
from enum import Enum
import logging
from openai import OpenAI


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



class DifficultyLevel(Enum):

    EASY = "简单"
    MEDIUM = "中等"
    HARD = "困难"


class QuestionType(Enum):

    MULTIPLE_CHOICE = "选择题"
    FILL_BLANK = "填空题"
    SHORT_ANSWER = "解答题"


class Question:

    def __init__(self, content: str, answer: str, explanation: str,
                 options: Optional[List[str]] = None):
        self.content = content
        self.options = options
        self.answer = answer
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:

        return {
            'content': self.content,
            'options': self.options,
            'answer': self.answer,
            'explanation': self.explanation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Question':

        return cls(
            content=data.get('content', ''),
            options=data.get('options'),
            answer=data.get('answer', ''),
            explanation=data.get('explanation', '')
        )


class DeepSeekClient:


    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-chat"

        self.recent_topics = []

    def generate_questions(self, subject: str, difficulty: DifficultyLevel,
                           question_type: QuestionType, count: int) -> List[Question]:

        prompt = self._build_prompt(subject, difficulty, question_type, count)

        try:

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.85,
                max_tokens=2500
            )

            content = response.choices[0].message.content
            questions_data = self._parse_response(content, count)

            questions = []
            for q_data in questions_data:
                question = Question(
                    content=q_data.get('content', ''),
                    options=q_data.get('options'),
                    answer=q_data.get('answer', ''),
                    explanation=q_data.get('explanation', '')
                )
                questions.append(question)


                self._record_topic(question.content)

            return questions

        except Exception as e:
            logger.error(f"生成习题失败: {e}")
            return []

    def _get_system_prompt(self) -> str:

        return """你是一个专业的教育专家，擅长出题。你的核心要求：
1. 每次出题必须保证题目多样化，绝不重复
2. 覆盖不同的知识点和角度
3. 题目要有创意和新意
4. 严格按JSON格式返回
5. 避免使用常见的、老套的题目模板"""

    def _build_prompt(self, subject: str, difficulty: DifficultyLevel,
                      question_type: QuestionType, count: int) -> str:

        type_requirements = self._get_type_requirements(question_type)

        diversity_strategy = self._get_diversity_strategy(question_type, count)

        avoid_topics = self._get_topics_to_avoid()

        prompt = f"""请生成{count}道{difficulty.value}难度的{question_type.value}，关于{subject}学科。

## 🚨 最重要的要求：避免重复
{avoid_topics}

## 📋 多样性策略
{diversity_strategy}

## ✅ 题目具体要求
{type_requirements}

## 📊 知识点覆盖要求
请确保这{count}道题目覆盖以下不同类型的知识点（每道题选择不同的侧重点）：
1. **基础概念题** - 考察核心定义和基本原理
2. **应用题** - 考察知识在实际场景中的运用
3. **分析题** - 考察理解和分析能力
4. **综合题** - 考察多个知识点的综合运用
5. **易错题** - 考察常见的误区和陷阱

**重要**: 每道题必须选择不同的侧重点，避免重复！

## 🎯 题目创新要求
- 避免使用教科书上的标准例题
- 尽量结合现实场景和实际应用
- 可以加入一些趣味性和故事性
- 使用新颖的提问方式

## 输出格式
请以JSON格式返回：
{{
    "questions": [
        {{
            "content": "题目内容",
            "options": ["选项A", "选项B", "选项C", "选项D"],  // 仅选择题需要
            "answer": "正确答案",
            "explanation": "详细解析（包含解题思路、关键步骤、知识点说明）"
        }}
    ]
}}

注意：确保每道题目都是独特的，考察不同的知识点和角度！
"""
        return prompt

    def _get_type_requirements(self, question_type: QuestionType) -> str:
        requirements = {
            QuestionType.MULTIPLE_CHOICE: """
- 每个题目提供4个选项（A、B、C、D）
- 答案使用选项字母（如：A）
- 选项设计要有区分度，避免明显错误选项
- 可以设计一些需要思考的干扰项
- 避免使用"以上都对"、"以上都错"等模板化选项
""",
            QuestionType.FILL_BLANK: """
- 在题目中使用____表示填空位置
- 可以有一个或多个填空
- 答案用分号分隔多个填空（如：答案1;答案2）
- 填空位置要有意义，考察关键知识点
- 避免填空过多或过少
""",
            QuestionType.SHORT_ANSWER: """
- 题目需要有一定深度，考察理解和应用能力
- 答案要详细完整，包含关键步骤
- 可以设计开放性问题，允许多种解法
- 鼓励学生展示思考过程
"""
        }
        return requirements.get(question_type, "")

    def _get_diversity_strategy(self, question_type: QuestionType, count: int) -> str:

        strategies = {
            QuestionType.MULTIPLE_CHOICE: f"""
请按照以下维度分散出题（{count}道题各选不同维度）：
- 概念理解类：考察定义、分类、特征
- 代码分析类：分析代码输出、找错误
- 场景应用类：在具体场景中选择正确做法
- 比较辨析类：区分相似概念
- 计算推理类：需要进行计算或逻辑推理
""",
            QuestionType.FILL_BLANK: f"""
请按照以下类型分散出题（{count}道题各选不同类型）：
- 关键术语填空：填写核心概念或术语
- 代码补全填空：填写代码的关键部分
- 原理阐述填空：填写重要原理或规则
- 结果预测填空：根据代码预测输出
- 对比分析填空：填写对比分析的关键点
""",
            QuestionType.SHORT_ANSWER: f"""
请按照以下难度层次分散出题（{count}道题各选不同层次）：
- 复述层次：考察基本概念的记忆和理解
- 应用层次：考察知识在简单场景的应用
- 分析层次：考察分析和比较能力
- 评价层次：考察判断和评估能力
- 创造层次：考察创新和综合能力
"""
        }
        return strategies.get(question_type, "")

    def _get_topics_to_avoid(self) -> str:

        if not self.recent_topics:
            return "（首次生成，无需要避免的主题）"

        recent = self.recent_topics[-5:]
        topics_text = "\n".join([f"  {i + 1}. {topic}" for i, topic in enumerate(recent)])

        return f"""
请避免生成与以下最近题目相似或重复的题目：
{topics_text}

要求：
- 考察不同的知识点
- 使用不同的题目角度
- 避免相似的题目结构和提问方式
- 如果某个知识点已经考过，请选择其他知识点
"""

    def _record_topic(self, content: str):

        topic = content[:80] + "..." if len(content) > 80 else content
        self.recent_topics.append(topic)

        if len(self.recent_topics) > 20:
            self.recent_topics = self.recent_topics[-20:]

    def _parse_response(self, content: str, expected_count: int) -> List[Dict[str, Any]]:

        try:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                data = json.loads(json_str)
                questions = data.get('questions', [])

                if len(questions) != expected_count:
                    logger.warning(f"期望{expected_count}道题，实际得到{len(questions)}道")

                return questions[:expected_count]
            else:
                logger.error("无法从响应中提取JSON")
                logger.debug(f"原始响应前500字符: {content[:500]}")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.debug(f"原始响应前500字符: {content[:500]}")
            return []
        except Exception as e:
            logger.error(f"解析响应时发生未知错误: {e}")
            return []

    def get_detailed_explanation(self, question: Question, user_answer: str,
                                 is_correct: bool) -> str:
        status = "正确" if is_correct else "错误"
        prompt = f"""请对以下题目进行详细解析：

题目：{question.content}

你的答案：{user_answer}
答案是否正确：{status}
正确答案：{question.answer}

请提供：
1. 完全的解题思路和步骤
2. 关键知识点讲解
3. 常见错误分析
4. 相关知识点扩展
5. 对用户答案的针对性点评

请用中文回答，语言清晰易懂，帮助学生真正理解知识点。
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个耐心的教育辅导老师，擅长详细解析题目并给出针对性指导。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1500
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"获取详细解析失败: {e}")
            return question.explanation

    def clear_history(self):

        self.recent_topics = []
        logger.info("已清空题目历史记录")


class ExerciseGenerator:

    def __init__(self, api_key: str):
        self.client = DeepSeekClient(api_key)
        self.current_questions: List[Question] = []

    def generate(self, subject: str, difficulty: DifficultyLevel,
                 question_type: QuestionType, count: int) -> List[Question]:

        self.current_questions = self.client.generate_questions(
            subject, difficulty, question_type, count
        )
        return self.current_questions

    def check_answer(self, question: Question, user_answer: str) -> bool:
        correct = question.answer.strip().lower()
        user = user_answer.strip().lower()

        if question.options:
            return correct == user
        return correct in user or user in correct or correct == user

    def get_practice_session_results(self, questions: List[Question],
                                     user_answers: List[str]) -> Dict[str, Any]:

        results = {
            'total': len(questions),
            'correct': 0,
            'details': []
        }

        for i, (question, user_answer) in enumerate(zip(questions, user_answers)):
            is_correct = self.check_answer(question, user_answer)

            if is_correct:
                results['correct'] += 1

            results['details'].append({
                'question_index': i,
                'question': question.to_dict(),
                'user_answer': user_answer,
                'is_correct': is_correct
            })

        return results

    def clear_history(self):

        self.client.clear_history()


"""---------------接口-------------------"""
def create_generator(api_key: os.getenv("DEEPSEEK_API_KEY")) -> ExerciseGenerator:
    """

    参数:
        api_key: DeepSeek API密钥

    返回:
        ExerciseGenerator实例
    """
    return ExerciseGenerator(api_key)


def generate_questions(generator: ExerciseGenerator, subject: str,
                       difficulty: str, question_type: str, count: int) -> Dict[str, Any]:
    """

    参数:
        generator: 习题生成器实例
        subject: 科目名称
        difficulty: 难度等级（"EASY", "MEDIUM", "HARD"）
        question_type: 题目类型（"MULTIPLE_CHOICE", "FILL_BLANK", "SHORT_ANSWER"）
        count: 题目数量（1-20）

    返回:
        {
            'success': bool,
            'questions': List[Dict],
            'error': str,
            'count': int
        }
    """
    if count < 1 or count > 20:
        return {
            'success': False,
            'error': '题目数量必须在1-20之间',
            'questions': [],
            'count': 0
        }

    try:
        difficulty_enum = getattr(DifficultyLevel, difficulty.upper(), DifficultyLevel.MEDIUM)
        type_enum = getattr(QuestionType, question_type.upper(), QuestionType.MULTIPLE_CHOICE)

        questions = generator.generate(subject, difficulty_enum, type_enum, count)

        if not questions:
            return {
                'success': False,
                'error': '生成题目失败，请检查API密钥或网络连接',
                'questions': [],
                'count': 0
            }

        questions_dict = [q.to_dict() for q in questions]

        return {
            'success': True,
            'questions': questions_dict,
            'count': len(questions_dict),
            'error': None
        }

    except Exception as e:
        logger.error(f"生成题目异常: {e}")
        return {
            'success': False,
            'error': str(e),
            'questions': [],
            'count': 0
        }


def check_answer(question: Dict[str, Any], user_answer: str) -> Dict[str, Any]:
    """
    检查答案是否正确

    参数:
        question: 题目字典
        user_answer: 用户答案

    返回:
        {
            'is_correct': bool,
            'correct_answer': str,
            'explanation': str
        }
    """
    correct = question.get('answer', '').strip().lower()
    user = user_answer.strip().lower()
    options = question.get('options')

    if options:
        is_correct = correct == user
    else:
        is_correct = correct in user or user in correct or correct == user

    return {
        'is_correct': is_correct,
        'correct_answer': question.get('answer', ''),
        'explanation': question.get('explanation', '')
    }


def get_detailed_explanation(generator: ExerciseGenerator, question: Dict[str, Any],
                             user_answer: str, is_correct: bool) -> str:
    """
    获取详细解析

    参数:
        generator: 习题生成器实例
        question: 题目字典
        user_answer: 用户答案
        is_correct: 答案是否正确

    返回:
        详细解析文本
    """
    question_obj = Question.from_dict(question)
    return generator.client.get_detailed_explanation(question_obj, user_answer, is_correct)


def calculate_accuracy(results: Dict[str, Any]) -> float:
    """
    计算准确率

    参数:
        results: get_practice_session_results返回的结果字典

    返回:
        准确率百分比（0-100）
    """
    total = results.get('total', 0)
    correct = results.get('correct', 0)
    return (correct / total * 100) if total > 0 else 0


def batch_check_answers(generator: ExerciseGenerator, questions: List[Dict[str, Any]],
                        user_answers: List[str]) -> Dict[str, Any]:
    """
    批量检查答案

    参数:
        generator: 习题生成器实例
        questions: 题目列表
        user_answers: 用户答案列表

    返回:
        {
            'total': int,
            'correct': int,
            'accuracy': float,
            'details': List[Dict]
        }
    """
    question_objs = [Question.from_dict(q) for q in questions]
    results = generator.get_practice_session_results(question_objs, user_answers)
    results['accuracy'] = calculate_accuracy(results)

    return results
