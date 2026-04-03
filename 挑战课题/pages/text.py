import streamlit as st
from deepseek_fb2 import create_exercise_generator, generate_questions, check_user_answer

st.set_page_config(page_title="习题生成", page_icon="✍️")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.switch_page("log_in.py")

st.title("✍️ 习题生成")

subject = st.selectbox("科目", ["高数", "英语", "计算机"])
difficulty = st.selectbox("难度", ["简单", "中等", "困难"])
question_type = st.selectbox("题型", ["选择题", "填空题", "简答题"])

diff_map = {"简单": "EASY", "中等": "MEDIUM", "困难": "HARD"}
type_map = {"选择题": "MULTIPLE_CHOICE", "填空题": "FILL_BLANK", "简答题": "SHORT_ANSWER"}

if st.button("生成题目"):
    with st.spinner("正在呼叫AI生成题目..."):
        generator = create_exercise_generator()
        raw_questions = generate_questions(
            generator,
            subject=subject,
            difficulty=diff_map[difficulty],
            question_type=type_map[question_type],
            count=2
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
        for i, q in enumerate(st.session_state.questions):
            user_ans = st.session_state.get(f"ans_{i}", "")
            is_correct = check_user_answer(q["raw_obj"], user_ans)

            if is_correct:
                st.success(f"第 {i + 1} 题：回答正确！✅")
            else:
                st.error(f"第 {i + 1} 题：回答错误 ❌ (你的答案: {user_ans})")

    if st.button("查看答案"):
        st.write("---")
        for i, q in enumerate(st.session_state.questions):
            st.info(f"**第 {i + 1} 题 正确答案**：{q['a']}")
            st.write(f"**解析**：{q['explanation']}")
