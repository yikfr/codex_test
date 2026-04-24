import streamlit as st
import pymysql
import json
from deepseek_fb2 import create_exercise_generator, generate_questions, check_user_answer
from exam import create_exam_generator, generate_exam_paper_api, export_to_markdown_api, get_statistics_api
from utils import render_sidebar

st.set_page_config(page_title="习题生成与试卷生成", page_icon="✍️")

render_sidebar()
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

st.title("✍️ 学习助手")

tab1, tab2 = st.tabs(["📝 习题练习", "📋 智能试卷生成"])

with tab1:
    st.header("习题练习")

    col1, col2 = st.columns(2)
    with col1:
        subject = st.selectbox("科目", ["高数", "英语", "计算机"], key="subject_exercise")
        difficulty = st.selectbox("难度", ["简单", "中等", "困难"], key="difficulty_exercise")
    with col2:
        question_type = st.selectbox("题型", ["选择题", "填空题", "简答题"], key="type_exercise")
        question_count = st.slider(
            "题目数量",
            min_value=1,
            max_value=20,
            value=1,
            step=1,
            help="选择要生成的题目数量（1-20题）",
            key="count_exercise"
        )

    diff_map = {"简单": "EASY", "中等": "MEDIUM", "困难": "HARD"}
    type_map = {"选择题": "MULTIPLE_CHOICE", "填空题": "FILL_BLANK", "简答题": "SHORT_ANSWER"}

    if st.button("生成题目", key="gen_exercise"):
        with st.spinner("正在呼叫AI生成题目..."):
            generator = create_exercise_generator()
            result = generate_questions(
                generator,
                subject=subject,
                difficulty=diff_map[difficulty],
                question_type=type_map[question_type],
                count=question_count
            )

            if result['success']:
                questions = []
                for q_data in result['questions']:
                    questions.append({
                        "q": q_data['content'],
                        "a": q_data['answer'],
                        "options": q_data.get('options', []),
                        "explanation": q_data.get('explanation', ''),
                        "raw_obj": q_data
                    })
                st.session_state.questions = questions
                record_details = f"生成科目：{subject} | 难度：{difficulty} | 题型：{question_type}"
                save_record_silently(
                    username=st.session_state.username,
                    action_type="✍️ 生成习题",
                    details=record_details
                )
                st.success(f"成功生成 {len(questions)} 道题目！")
            else:
                st.error(f"生成失败：{result['error']}")

    if "questions" in st.session_state:
        st.subheader("📚 题目")
        for i, q in enumerate(st.session_state.questions):
            st.write(f"**{i + 1}. {q['q']}**")
            if q["options"]:
                for opt in q["options"]:
                    st.write(opt)
            st.text_input("你的答案", key=f"ans_{i}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("提交答案", key="submit_exercise"):
                st.write("---")
                st.subheader("批改结果：")
                correct_count = 0
                for i, q in enumerate(st.session_state.questions):
                    user_ans = st.session_state.get(f"ans_{i}", "")
                    result = check_user_answer(q["raw_obj"], user_ans)
                    if result['is_correct']:
                        st.success(f"第 {i + 1} 题：回答正确！✅")
                        correct_count += 1
                    else:
                        st.error(f"第 {i + 1} 题：回答错误 ❌ (你的答案: {user_ans})")
                        st.info(f"正确答案：{result['correct_answer']}")
                total_q = len(st.session_state.questions)
                score_details = f"提交了 {subject} 测试 ({difficulty})，共 {total_q} 题，答对 {correct_count} 题"
                save_record_silently(
                    username=st.session_state.username,
                    action_type="📝 完成习题测试",
                    details=score_details
                )
                st.metric("得分", f"{correct_count}/{total_q}")

        with col2:
            if st.button("查看答案", key="view_answers"):
                st.write("---")
                for i, q in enumerate(st.session_state.questions):
                    st.info(f"**第 {i + 1} 题 正确答案**：{q['a']}")
                    st.write(f"**解析**：{q['explanation']}")

with tab2:
    st.header("智能试卷生成")

    if "exam_paper" not in st.session_state:
        st.session_state.exam_paper = None

    with st.expander("⚙️ 试卷配置（点击展开）", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            subject_exam = st.text_input("科目名称", value="Python程序设计", key="subject_exam")
            title = st.text_input("试卷标题", value=f"{subject_exam}单元测试卷", key="title_exam")
        with col2:
            duration = st.number_input("考试时长（分钟）", min_value=30, max_value=180, value=90, step=10, key="duration")
            total_score = st.number_input("试卷总分", min_value=50, max_value=150, value=100, step=10,
                                          key="total_score")

        st.divider()

        st.subheader("📋 试卷结构")

        num_sections = st.number_input("题型数量", min_value=1, max_value=6, value=3, step=1, key="num_sections")

        sections = []
        for i in range(int(num_sections)):
            st.markdown(f"**题型 {i + 1}**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                q_type = st.selectbox(
                    "题型",
                    ["选择题", "填空题", "判断题", "简答题", "计算题", "论述题"],
                    key=f"exam_type_{i}"
                )
            with col2:
                count = st.number_input("数量", min_value=1, max_value=30, value=10, key=f"exam_count_{i}")
            with col3:
                score = st.number_input("每题分值", min_value=1, max_value=20, value=3, key=f"exam_score_{i}")
            with col4:
                difficulty = st.selectbox(
                    "难度",
                    ["简单", "中等", "困难"],
                    key=f"exam_diff_{i}"
                )

            sections.append({
                "type": q_type,
                "count": int(count),
                "score_per_question": int(score),
                "difficulty": difficulty
            })
            st.divider()

    if st.button("🚀 生成试卷", key="generate_exam", type="primary"):
        with st.spinner("正在生成试卷，这可能需要一些时间..."):
            try:
                generator = create_exam_generator()
                result = generate_exam_paper_api(
                    generator=generator,
                    subject=subject_exam,
                    title=title,
                    duration=duration,
                    total_score=total_score,
                    sections=sections
                )

                if result['success']:
                    st.session_state.exam_paper = result['data']
                    st.success("✅ 试卷生成成功！")

                    save_record_silently(
                        username=st.session_state.username,
                        action_type="📝 生成完整试卷",
                        details=f"科目：{subject_exam} | 标题：{title} | 总分：{total_score}分"
                    )
                else:
                    st.error(f"生成失败：{result['error']}")
            except Exception as e:
                st.error(f"发生错误：{str(e)}")

    if st.session_state.exam_paper:
        st.divider()

        exam_tab1, exam_tab2, exam_tab3 = st.tabs(["📖 试卷内容", "📊 试卷统计", "📥 导出试卷"])

        with exam_tab1:
            st.subheader("📄 试卷内容预览")

            show_answers = st.checkbox("显示答案和解析", value=False, key="show_exam_answers")

            exam_data = st.session_state.exam_paper
            st.markdown(f"# {exam_data['title']}")
            st.markdown(
                f"**科目：** {exam_data['subject']}  &nbsp;&nbsp; **考试时间：** {exam_data['duration']}分钟  &nbsp;&nbsp; **总分：** {exam_data['total_score']}分")
            st.markdown("---")

            for section in exam_data['sections']:
                st.markdown(f"## {section['section_name']}")
                st.markdown(
                    f"*（共{len(section['questions'])}题，每题{section['score_per_question']}分，共{section['total_section_score']}分）*")
                st.markdown("")

                for q in section['questions']:
                    st.markdown(f"**{q['id']}. {q['question']}**")

                    if 'options' in q and q['options']:
                        for opt in q['options']:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{opt}")

                    if show_answers:
                        with st.expander(f"查看第{q['id']}题答案和解析"):
                            st.success(f"**答案：** {q['answer']}")
                            st.info(f"**解析：** {q['explanation']}")

                    st.markdown("")

                st.markdown("---")

        with exam_tab2:
            st.subheader("📊 试卷统计分析")

            try:
                generator = create_exam_generator()
                stats_result = get_statistics_api(generator, st.session_state.exam_paper)

                if stats_result['success']:
                    stats = stats_result['data']

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("题型分布")
                        st.bar_chart(stats['question_type_distribution'])

                        st.subheader("分数分布")
                        st.bar_chart(stats['score_distribution'])

                    with col2:
                        st.subheader("难度分布")
                        st.bar_chart(stats['difficulty_distribution'])

                    st.divider()

                    st.subheader("📋 详细统计")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("总题数", stats['total_questions'])
                    with col2:
                        st.metric("总分数", st.session_state.exam_paper['total_score'])
                    with col3:
                        avg_score = st.session_state.exam_paper['total_score'] / stats['total_questions'] if stats[
                                                                                                                 'total_questions'] > 0 else 0
                        st.metric("平均每题分值", f"{avg_score:.1f}分")

                    st.subheader("题型详细信息")
                    type_data = []
                    for q_type, count in stats['question_type_distribution'].items():
                        score = stats['score_distribution'].get(q_type, 0)
                        type_data.append({
                            "题型": q_type,
                            "题数": count,
                            "总分": score,
                            "每题分值": score / count if count > 0 else 0
                        })
                    st.dataframe(type_data, use_container_width=True)
                else:
                    st.error(f"统计失败：{stats_result['error']}")
            except Exception as e:
                st.error(f"获取统计信息失败：{str(e)}")

        with exam_tab3:
            st.subheader("📥 导出试卷")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📄 导出试卷（无答案）", key="export_no_ans", use_container_width=True):
                    try:
                        generator = create_exam_generator()
                        result = export_to_markdown_api(
                            generator=generator,
                            exam_paper=st.session_state.exam_paper,
                            include_answers=False
                        )

                        if result['success']:
                            st.download_button(
                                label="下载试卷",
                                data=result['data'],
                                file_name=f"{st.session_state.exam_paper['title']}.md",
                                mime="text/markdown",
                                key="download_no_ans_exam"
                            )
                            st.success("试卷已生成，点击下载按钮保存")

                            save_record_silently(
                                username=st.session_state.username,
                                action_type="📥 导出试卷",
                                details=f"试卷标题：{st.session_state.exam_paper['title']} | 格式：Markdown（无答案）"
                            )
                        else:
                            st.error(f"导出失败：{result['error']}")
                    except Exception as e:
                        st.error(f"导出出错：{str(e)}")

            with col2:
                if st.button("📋 导出试卷（含答案）", key="export_with_ans", use_container_width=True):
                    try:
                        generator = create_exam_generator()
                        result = export_to_markdown_api(
                            generator=generator,
                            exam_paper=st.session_state.exam_paper,
                            include_answers=True
                        )

                        if result['success']:
                            st.download_button(
                                label="下载试卷（含答案）",
                                data=result['data'],
                                file_name=f"{st.session_state.exam_paper['title']}_含答案.md",
                                mime="text/markdown",
                                key="download_with_ans_exam"
                            )
                            st.success("试卷（含答案）已生成，点击下载按钮保存")

                            save_record_silently(
                                username=st.session_state.username,
                                action_type="📥 导出试卷（含答案）",
                                details=f"试卷标题：{st.session_state.exam_paper['title']}"
                            )
                        else:
                            st.error(f"导出失败：{result['error']}")
                    except Exception as e:
                        st.error(f"导出出错：{str(e)}")

            st.divider()
            if st.button("📊 导出JSON格式", key="export_json", use_container_width=True):
                json_data = json.dumps(st.session_state.exam_paper, ensure_ascii=False, indent=2)
                st.download_button(
                    label="下载JSON文件",
                    data=json_data,
                    file_name=f"{st.session_state.exam_paper['title']}.json",
                    mime="application/json",
                    key="download_json_exam"
                )
