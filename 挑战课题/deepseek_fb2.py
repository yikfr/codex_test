import json
import os
from typing import List, Dict, Any, Optional
from enum import Enum
import logging
from openai import OpenAI


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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


class DeepSeekClient:
    def __init__(self):

        api__key = os.getenv("DEEPSEEK_API_KEY")

        self.api_key = api__key

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-chat"

    def generate_questions(self, subject: str, difficulty: DifficultyLevel,
                           question_type: QuestionType, count: int) -> List[Question]:
        prompt = self._build_prompt(subject, difficulty, question_type, count)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的教育专家，擅长出题。请严格按照JSON格式返回结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            questions_data = self._parse_response(content, count)

            # 转换为Question对象
            questions = []
            for q_data in questions_data:
                question = Question(
                    content=q_data.get('content', ''),
                    options=q_data.get('options'),
                    answer=q_data.get('answer', ''),
                    explanation=q_data.get('explanation', '')
                )
                questions.append(question)

            return questions

        except Exception as e:
            logger.error(f"生成习题失败: {e}")
            return []

    def _build_prompt(self, subject: str, difficulty: DifficultyLevel,
                      question_type: QuestionType, count: int) -> str:
        type_specific = ""

        if question_type == QuestionType.MULTIPLE_CHOICE:
            type_specific = """
- 每个题目提供4个选项（A、B、C、D）
- 答案使用选项字母（如：A）
- 难度适中，考察核心知识点
"""
        elif question_type == QuestionType.FILL_BLANK:
            type_specific = """
- 在题目中使用____表示填空位置
- 可以有一个或多个填空
- 答案用分号分隔多个填空（如：答案1;答案2）
"""
        else:
            type_specific = """
- 题目需要有一定深度，考察理解和应用能力
- 答案要详细完整，包含关键步骤
- 适合做简答或计算题
"""

        prompt = f"""请生成{count}道{difficulty.value}难度的{question_type.value}，关于{subject}学科。

要求：
1. 题目要有教育意义，考察关键知识点
2. 难度要符合{difficulty.value}级别的标准
3. 答案要准确，解析要详细
{type_specific}

请以JSON格式返回，格式如下：
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

注意：
- 对于填空题，在content中使用____表示填空位置
- 对于解答题，answer要包含完整的解答过程
- explanation要详细，帮助学生理解
- 请确保返回有效的JSON格式
"""
        return prompt

    def _parse_response(self, content: str, expected_count: int) -> List[Dict[str, Any]]:
        """解析API返回的数据"""
        try:
            # 提取JSON部分
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
                return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.debug(f"原始响应: {content}")
            return []

    def get_detailed_explanation(self, question: Question, user_answer: str,
                                 is_correct: bool) -> str:
        """获取详细解析"""
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


class ExerciseGenerator:

    def __init__(self):
        self.client = DeepSeekClient()
        self.current_questions: List[Question] = []

    def generate(self, subject: str, difficulty: DifficultyLevel,
                 question_type: QuestionType, count: int) -> List[Question]:
        """生成习题"""
        self.current_questions = self.client.generate_questions(
            subject, difficulty, question_type, count
        )
        return self.current_questions

    def check_answer(self, question: Question, user_answer: str) -> bool:
        """检查答案是否正确"""
        correct = question.answer.strip().lower()
        user = user_answer.strip().lower()

        if question.options:
            return correct == user

        return correct in user or user in correct or correct == user

    def get_practice_session_results(self, questions: List[Question],
                                     user_answers: List[str]) -> Dict[str, Any]:
        """获取练习会话结果"""
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
                'question': question,
                'user_answer': user_answer,
                'is_correct': is_correct
            })

        return results


def create_exercise_generator() -> ExerciseGenerator:
    """
    创建练习生成器实例
    返回: ExerciseGenerator实例
    """
    return ExerciseGenerator()


def generate_questions(generator: ExerciseGenerator, subject: str,
                       difficulty: str, question_type: str, count: int) -> List[Question]:
    """
    生成问题
    参数:
        generator - 练习生成器实例
        subject - 科目名称（如："Python编程"）
        difficulty - 难度等级（"EASY", "MEDIUM", "HARD"）
        question_type - 题目类型（"MULTIPLE_CHOICE", "FILL_BLANK", "SHORT_ANSWER"）
        count - 题目数量
    返回: Question对象列表
    """
    difficulty_enum = getattr(DifficultyLevel, difficulty.upper(), DifficultyLevel.MEDIUM)
    type_enum = getattr(QuestionType, question_type.upper(), QuestionType.MULTIPLE_CHOICE)
    return generator.generate(subject, difficulty_enum, type_enum, count)


def check_user_answer(question: Question, user_answer: str) -> bool:
    """
    检查用户答案
    参数:
        question - Question对象
        user_answer - 用户的答案字符串
    返回: 布尔值，True表示正确，False表示错误
    """
    correct = question.answer.strip().lower()
    user = user_answer.strip().lower()

    if question.options:
        return correct == user
    return correct in user or user in correct or correct == user


def get_explanation(question: Question,
                    user_answer: str, is_correct: bool) -> str:
    """
    获取解释
    参数:
        question - Question对象
        user_answer - 用户的答案
        is_correct - 答案是否正确
    返回: 解释文本
    """
    client = DeepSeekClient()
    return client.get_detailed_explanation(question, user_answer, is_correct)


def calculate_accuracy(results: Dict[str, Any]) -> float:
    """
    计算准确率
    参数: results - 包含练习结果的字典
    返回: 准确率百分比
    """
    total = results.get('total', 0)
    correct = results.get('correct', 0)
    return (correct / total * 100) if total > 0 else 0
