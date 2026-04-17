import streamlit as st
import pymysql
from deepseek_fb2 import create_generator,generate_questions,check_answer,get_detailed_explanation,calculate_accuracy
st.set_page_config(page_title="习题生成", page_icon="✍️")


def save_record_silently(username, action_type, details):
    try:
        conn = pymysql.connect(
            host=st.secrets["mysql"]["host"],
            port=st.secrets["mysql"]["port"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"],
            charset="utf8mb4",
            autocommit=True,
            ssl={"ssl": {}}
        )
        with conn.cursor() as cursor:
            sql_create = """
            CREATE TABLE IF NOT EXISTS `user_records` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `username` VARCHAR(50) NOT NULL,
                `action_type` VARCHAR(50) NOT NULL,
                `details` TEXT,
                `record_time` DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(sql_create)

            sql_insert = "INSERT INTO `user_records` (`username`, `action_type`, `details`) VALUES (%s, %s, %s)"
            cursor.execute(sql_insert, (username, action_type, details))
    except Exception as e:
        print(f"静默记录失败: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()


if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.switch_page("log_in.py")

st.title("✍️ 习题生成")

subject = st.selectbox("科目", ["高数", "英语", "计算机"])
difficulty = st.selectbox("难度", ["简单", "中等", "困难"])
count = st.number_input("题目数量", min_value=1, max_value=20, value=2, step=1)
question_type = st.selectbox("题型", ["选择题", "填空题", "简答题"])

diff_map = {"简单": "EASY", "中等": "MEDIUM", "困难": "HARD"}
type_map = {"选择题": "MULTIPLE_CHOICE", "填空题": "FILL_BLANK", "简答题": "SHORT_ANSWER"}

if st.button("生成题目"):
    with st.spinner("正在呼叫AI生成题目..."):
        generator = create_generator()
        raw_questions = generate_questions(
            generator,
            subject=subject,
            difficulty=diff_map[difficulty],
            question_type=type_map[question_type],
            count=count
        )

        questions = []
        for q in raw_questions:
            questions.append({
                "q": q.content,
                "a": q.answer,
                "options": q.options,
                "explanation": q.explanation,
                "raw_obj": q
            })

        st.session_state.questions = questions

        record_details = f"生成科目：{subject} | 难度：{difficulty} | 题型：{question_type}"
        save_record_silently(
            username=st.session_state.username,
            action_type="✍️ 生成习题",
            details=record_details
        )

if "questions" in st.session_state:
    st.subheader("📚 题目")

    for i, q in enumerate(st.session_state.questions):
        st.write(f"**{i + 1}. {q['q']}**")

        if q["options"]:
            for opt in q["options"]:
                st.write(opt)

        st.text_input("你的答案", key=f"ans_{i}")

    if st.button("提交答案"):
        st.write("---")
        st.subheader("批改结果：")

        correct_count = 0

        for i, q in enumerate(st.session_state.questions):
            user_ans = st.session_state.get(f"ans_{i}", "")
            is_correct = check_answer(q["raw_obj"], user_ans)

            if is_correct:
                st.success(f"第 {i + 1} 题：回答正确！✅")
                correct_count += 1
            else:
                st.error(f"第 {i + 1} 题：回答错误 ❌ (你的答案: {user_ans})")

        total_q = len(st.session_state.questions)
        score_details = f"提交了 {subject} 测试 ({difficulty})，共 {total_q} 题，答对 {correct_count} 题"
        save_record_silently(
            username=st.session_state.username,
            action_type="📝 完成习题测试",
            details=score_details
        )

    if st.button("查看答案"):
        st.write("---")
        for i, q in enumerate(st.session_state.questions):
            st.info(f"**第 {i + 1} 题 正确答案**：{q['a']}")
            st.write(f"**解析**：{q['explanation']}")
