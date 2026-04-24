import json
import os
from typing import List, Dict, Any
from openai import OpenAI

class ExamGenerator:

    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        self.api_key = api_key
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )

    def generate_questions(
            self,
            subject: str,
            difficulty: str = "中等",
            question_types: List[str] = None,
            num_questions: int = 5,
            knowledge_points: List[str] = None
    ) -> Dict[str, Any]:
        if question_types is None:
            question_types = ["选择题", "填空题", "简答题"]

        if knowledge_points is None:
            knowledge_points = ["基础知识"]

        prompt = self._build_question_prompt(
            subject=subject,
            difficulty=difficulty,
            question_types=question_types,
            num_questions=num_questions,
            knowledge_points=knowledge_points
        )

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的教育工作者，擅长出题。请严格按照JSON格式返回试题。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=5000
            )

            content = response.choices[0].message.content
            questions = self._parse_response(content)

            return {
                "success": True,
                "data": questions,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "data": [],
                "error": str(e)
            }

    def generate_exam_paper(
            self,
            subject: str,
            title: str = None,
            duration: int = 120,
            total_score: int = 100,
            sections: List[Dict] = None
    ) -> Dict[str, Any]:

        if title is None:
            title = f"{subject}期末考试试卷"

        if sections is None:
            sections = [
                {"type": "选择题", "count": 10, "score_per_question": 3, "difficulty": "中等"},
                {"type": "填空题", "count": 5, "score_per_question": 4, "difficulty": "中等"},
                {"type": "简答题", "count": 3, "score_per_question": 10, "difficulty": "困难"}
            ]

        exam_paper = {
            "title": title,
            "subject": subject,
            "duration": duration,
            "total_score": total_score,
            "sections": []
        }

        question_counter = 1
        for idx, section in enumerate(sections, 1):
            result = self.generate_questions(
                subject=subject,
                difficulty=section.get("difficulty", "中等"),
                question_types=[section["type"]],
                num_questions=section["count"]
            )

            if not result["success"]:
                return {
                    "success": False,
                    "data": None,
                    "error": f"生成{section['type']}时出错: {result['error']}"
                }

            questions = result["data"]

            for q in questions:
                q["id"] = question_counter
                question_counter += 1

            exam_paper["sections"].append({
                "section_id": idx,
                "section_name": self._get_section_name(section["type"]),
                "question_type": section["type"],
                "questions": questions,
                "score_per_question": section["score_per_question"],
                "total_section_score": section["count"] * section["score_per_question"]
            })

        return {
            "success": True,
            "data": exam_paper,
            "error": None
        }

    def export_paper_to_markdown(
            self,
            exam_paper: Dict,
            include_answers: bool = False
    ) -> Dict[str, Any]:

        try:
            markdown_content = self._generate_markdown_content(exam_paper, include_answers)

            return {
                "success": True,
                "data": markdown_content,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }

    def get_paper_statistics(self, exam_paper: Dict) -> Dict[str, Any]:

        try:
            total_questions = 0
            type_distribution = {}
            difficulty_distribution = {}
            score_distribution = {}

            for section in exam_paper["sections"]:
                section_type = section["question_type"]
                section_score = section["total_section_score"]
                question_count = len(section["questions"])

                total_questions += question_count
                type_distribution[section_type] = question_count
                score_distribution[section_type] = section_score

                for q in section["questions"]:
                    difficulty = q.get("difficulty", "未知")
                    difficulty_distribution[difficulty] = difficulty_distribution.get(difficulty, 0) + 1

            return {
                "success": True,
                "data": {
                    "total_questions": total_questions,
                    "question_type_distribution": type_distribution,
                    "difficulty_distribution": difficulty_distribution,
                    "score_distribution": score_distribution
                },
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }

    def _build_question_prompt(
            self,
            subject: str,
            difficulty: str,
            question_types: List[str],
            num_questions: int,
            knowledge_points: List[str]
    ) -> str:
        prompt = f"""
请为{subject}科目生成{num_questions}道试题，具体要求如下：
- 难度：{difficulty}
- 题型：{', '.join(question_types)}
- 涉及知识点：{', '.join(knowledge_points)}

请严格按照以下JSON格式返回试题（只返回JSON，不要其他说明）：

{{
    "questions": [
        {{
            "id": 1,
            "type": "题型",
            "difficulty": "{difficulty}",
            "knowledge_point": "知识点",
            "question": "题目内容",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "answer": "答案",
            "explanation": "解析"
        }}
    ]
}}

注意：
1. 选择题必须包含4个选项，options字段是必须的
2. 填空题、简答题不需要options字段
3. 答案要准确清晰
4. 解析要详细易懂
5. 确保题目质量
"""
        return prompt

    def _parse_response(self, content: str) -> List[Dict]:

        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())
            return data.get("questions", [])
        except json.JSONDecodeError:
            return []

    def _get_section_name(self, question_type: str) -> str:

        names = {
            "选择题": "一、选择题",
            "填空题": "二、填空题",
            "判断题": "三、判断题",
            "简答题": "四、简答题",
            "计算题": "五、计算题",
            "论述题": "六、论述题"
        }
        return names.get(question_type, f"{question_type}部分")

    def _generate_markdown_content(self, exam_paper: Dict, include_answers: bool) -> str:

        lines = []

        lines.append(f"# {exam_paper['title']}\n")
        lines.append(f"**科目**：{exam_paper['subject']}  ")
        lines.append(f"**考试时间**：{exam_paper['duration']}分钟  ")
        lines.append(f"**总分**：{exam_paper['total_score']}分  \n")
        lines.append("---\n")

        for section in exam_paper['sections']:
            lines.append(f"## {section['section_name']}\n")
            lines.append(
                f"*（共{len(section['questions'])}题，每题{section['score_per_question']}分，共{section['total_section_score']}分）*\n")

            for q in section['questions']:
                lines.append(f"**{q['id']}. {q['question']}**\n")

                if 'options' in q and q['options']:
                    for option in q['options']:
                        lines.append(f"- {option}")
                    lines.append("")

                if include_answers:
                    lines.append(f"**答案**：{q['answer']}  ")
                    lines.append(f"**解析**：{q['explanation']}\n")

                lines.append("<br>\n")

        return "\n".join(lines)


def create_exam_generator() -> ExamGenerator:
    return ExamGenerator()


def generate_questions_api(
        generator: ExamGenerator,
        subject: str,
        difficulty: str,
        question_types: List[str],
        num_questions: int = 5,
        knowledge_points: List[str] = None
) -> Dict[str, Any]:
    return generator.generate_questions(
        subject=subject,
        difficulty=difficulty,
        question_types=question_types,
        num_questions=num_questions,
        knowledge_points=knowledge_points
    )


def generate_exam_paper_api(
        generator: ExamGenerator,
        subject: str,
        title: str,
        duration: int,
        total_score: int,
        sections: List[Dict] = None
) -> Dict[str, Any]:
    return generator.generate_exam_paper(
        subject=subject,
        title=title,
        duration=duration,
        total_score=total_score,
        sections=sections
    )


def export_to_markdown_api(
        generator: ExamGenerator,
        exam_paper: Dict,
        include_answers: bool = False
) -> Dict[str, Any]:
    return generator.export_paper_to_markdown(exam_paper, include_answers)


def get_statistics_api(
        generator: ExamGenerator,
        exam_paper: Dict
) -> Dict[str, Any]:
    return generator.get_paper_statistics(exam_paper)