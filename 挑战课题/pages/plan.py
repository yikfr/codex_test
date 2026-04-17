import streamlit as st
import pymysql
import json
import time
from datetime import datetime, timedelta
from deepseek_fb3 import ask_deepseek
from typing import Optional, Dict, List

CONFIG = {
    "plan": {
        "min_days": 3,
        "max_days": 30,
        "default_days": 7,
        "stages": ["基础阶段", "强化阶段", "冲刺阶段"],
        "difficulty_levels": ["入门", "进阶", "精通"],
        "time_formats": ["小时", "分钟"],
        "intensity_rules": {
            "轻松": {"study_ratio": 0.6, "practice_ratio": 0.2, "review_ratio": 0.2},
            "标准": {"study_ratio": 0.5, "practice_ratio": 0.3, "review_ratio": 0.2},
            "高强度": {"study_ratio": 0.4, "practice_ratio": 0.4, "review_ratio": 0.2}
        }
    },
    "prompt_template": """
请帮我制定一个结构化的详细学习计划，要求如下：
1. 整体阶段划分：{stages_desc}
2. 学习目标：{goal}
3. 学习周期：{days}天（{stage_days_desc}）
4. 每天学习时长：{daily_time}{time_unit}（{intensity_desc}）
5. 基础水平：{basic_level}
6. 目标难度：{target_difficulty}
7. 学习场景：{scene}

输出要求：
1. 按「DayX [阶段] 难度：XXX」格式开头
2. 每天内容包含：
   - 核心学习内容（量化：{study_min}分钟）
   - 实操练习（量化：{practice_min}分钟）
   - 复盘复习（量化：{review_min}分钟）
3. 难度随天数逐步提升，符合{basic_level}到{target_difficulty}的进阶逻辑
4. 每个阶段结束包含阶段复盘要求
5. 简洁清晰，结构化展示
""",
    "db": {
        "table_name": "user_records",
        "index_fields": ["username", "action_type", "record_time"],
        "max_detail_length": 4096
    },
    "api": {
        "timeout": 30,
        "retry_times": 2
    }
}


class DBManager:
    def __init__(self):
        self.conn: Optional[pymysql.Connection] = None
        self._connect()

    def _connect(self):
        try:
            self.conn = pymysql.connect(
                host=st.secrets["mysql"]["host"],
                port=st.secrets["mysql"]["port"],
                user=st.secrets["mysql"]["user"],
                password=st.secrets["mysql"]["password"],
                database=st.secrets["mysql"]["database"],
                charset="utf8mb4",
                autocommit=True,
                ssl={"ssl": {"ca": "/etc/ssl/cert.pem"}}
            )
            self._init_table()
        except Exception as e:
            st.error(f"数据库连接失败：{str(e)}")
            self.conn = None

    def _init_table(self):
        if not self.conn:
            return
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS `{CONFIG['db']['table_name']}` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `username` VARCHAR(50) NOT NULL,
                    `action_type` VARCHAR(50) NOT NULL,
                    `details` TEXT,
                    `record_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `plan_version` VARCHAR(20) DEFAULT 'v1.0',
                    INDEX idx_username (username),
                    INDEX idx_action (action_type),
                    INDEX idx_time (record_time)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS `plan_execution` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `username` VARCHAR(50) NOT NULL,
                    `plan_version` VARCHAR(20) NOT NULL,
                    `day` INT NOT NULL,
                    `status` ENUM('未完成', '已完成', '延期') DEFAULT '未完成',
                    `actual_time` INT DEFAULT 0,
                    `notes` TEXT,
                    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_plan_version (plan_version)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
        except Exception as e:
            st.error(f"表初始化失败：{str(e)}")

    def insert_record(self, username: str, action_type: str, details: str, plan_version: str = "v1.0") -> bool:
        if not self.conn or len(details) > CONFIG['db']['max_detail_length']:
            return False

        retry_times = CONFIG['api']['retry_times']
        while retry_times > 0:
            try:
                with self.conn.cursor() as cursor:
                    sql = f"""
                    INSERT INTO `{CONFIG['db']['table_name']}` 
                    (username, action_type, details, plan_version) 
                    VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(sql,
                                   (username, action_type, details[:CONFIG['db']['max_detail_length']], plan_version))
                return True
            except Exception as e:
                retry_times -= 1
                time.sleep(1)
                if retry_times == 0:
                    st.error(f"记录保存失败：{str(e)}")
                    return False
        return False

    def insert_execution(self, username: str, plan_version: str, day: int, status: str, actual_time: int = 0,
                         notes: str = "") -> bool:
        if not self.conn:
            return False
        try:
            with self.conn.cursor() as cursor:
                sql = """
                REPLACE INTO `plan_execution` 
                (username, plan_version, day, status, actual_time, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (username, plan_version, day, status, actual_time, notes))
            return True
        except Exception as e:
            st.error(f"执行记录保存失败：{str(e)}")
            return False

    def get_plan_versions(self, username: str) -> List[str]:
        if not self.conn:
            return []
        try:
            with self.conn.cursor() as cursor:
                sql = f"""
                SELECT DISTINCT plan_version FROM `{CONFIG['db']['table_name']}`
                WHERE username = %s AND action_type = '📅 生成学习计划'
                ORDER BY record_time DESC
                """
                cursor.execute(sql, (username,))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            st.error(f"获取版本失败：{str(e)}")
            return []

    def close(self):
        if self.conn and self.conn.open:
            self.conn.close()


def validate_inputs(goal: str, daily_time: str, time_unit: str) -> Dict[str, str]:
    errors = {}
    if not goal.strip():
        errors["goal"] = "学习目标不能为空"
    elif len(goal) < 10:
        errors["goal"] = "学习目标需至少10个字"

    if not daily_time.strip():
        errors["daily_time"] = "每天学习时间不能为空"
    else:
        try:
            time_val = float(daily_time)
            if time_val <= 0:
                errors["daily_time"] = "学习时间需大于0"
            elif time_unit == "分钟" and time_val > 1440:
                errors["daily_time"] = "不能超过1440分钟"
            elif time_unit == "小时" and time_val > 24:
                errors["daily_time"] = "不能超过24小时"
        except ValueError:
            errors["daily_time"] = "学习时间需输入数字"
    return errors


def generate_plan_version() -> str:
    return f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def calculate_stage_days(days: int) -> Dict[str, int]:
    stage_days = {}
    total_stages = len(CONFIG['plan']['stages'])
    base_days = days // total_stages
    remainder = days % total_stages

    for i, stage in enumerate(CONFIG['plan']['stages']):
        stage_days[stage] = base_days + (1 if i < remainder else 0)

    if sum(stage_days.values()) != days:
        stage_days[CONFIG['plan']['stages'][-1]] += days - sum(stage_days.values())
    return stage_days


def main():
    st.set_page_config(page_title="学习计划", page_icon="📅", layout="wide")

    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("请先登录")
        st.switch_page("log_in.py")

    if "stop_generate" not in st.session_state:
        st.session_state.stop_generate = False
    if "plan_versions" not in st.session_state:
        st.session_state.plan_versions = []
    if "current_plan_version" not in st.session_state:
        st.session_state.current_plan_version = ""
    if "execution_records" not in st.session_state:
        st.session_state.execution_records = {}

    db_manager = DBManager()

    st.title("📅 AI学习计划生成")
    st.markdown("### 🎯 定制你的专属学习计划")

    col1, col2 = st.columns(2)
    with col1:
        goal = st.text_area("你的学习目标", placeholder="例如：7天掌握高数导数，完成50道练习题", height=100)
        basic_level = st.selectbox("你的基础水平", CONFIG['plan']['difficulty_levels'], index=0)
        target_difficulty = st.selectbox("目标难度", CONFIG['plan']['difficulty_levels'], index=1)

    with col2:
        days = st.slider("学习周期（天）", CONFIG['plan']['min_days'], CONFIG['plan']['max_days'],
                         CONFIG['plan']['default_days'])
        style = st.selectbox("学习强度", list(CONFIG['plan']['intensity_rules'].keys()), index=1)
        scene = st.selectbox("学习场景", ["备考", "兴趣学习", "职场技能提升", "考级考证"], index=0)

        time_col1, time_col2 = st.columns(2)
        with time_col1:
            daily_time = st.text_input("每天学习时长", placeholder="2.5")
        with time_col2:
            time_unit = st.selectbox("时间单位", CONFIG['plan']['time_formats'], index=0)

    input_errors = validate_inputs(goal, daily_time, time_unit)
    if input_errors:
        for field, error in input_errors.items():
            st.error(f"⚠️ {error}")

    generate_btn = st.button("🚀 生成学习计划", disabled=bool(input_errors))
    if generate_btn:
        st.session_state.stop_generate = False
        plan_version = generate_plan_version()
        st.session_state.current_plan_version = plan_version

        total_min = float(daily_time) * (60 if time_unit == "小时" else 1)
        intensity_rule = CONFIG['plan']['intensity_rules'][style]
        study_min = int(total_min * intensity_rule['study_ratio'])
        practice_min = int(total_min * intensity_rule['practice_ratio'])
        review_min = int(total_min * intensity_rule['review_ratio'])
        stage_days = calculate_stage_days(days)

        stages_desc = " | ".join([f"{stage}：{days}天" for stage, days in stage_days.items()])
        stage_days_desc = f"分为{len(CONFIG['plan']['stages'])}个阶段（{stages_desc}）"
        intensity_desc = f"学习{study_min}分钟 + 练习{practice_min}分钟 + 复习{review_min}分钟"

        prompt = CONFIG['prompt_template'].format(
            stages_desc=stages_desc,
            goal=goal,
            days=days,
            stage_days_desc=stage_days_desc,
            daily_time=daily_time,
            time_unit=time_unit,
            intensity_desc=intensity_desc,
            basic_level=basic_level,
            target_difficulty=target_difficulty,
            scene=scene,
            study_min=study_min,
            practice_min=practice_min,
            review_min=review_min
        )

        with st.spinner("正在生成结构化学习计划..."):
            retry_times = CONFIG['api']['retry_times']
            response = None
            while retry_times > 0 and not st.session_state.stop_generate:
                try:
                    response = ask_deepseek(prompt, timeout=CONFIG['api']['timeout'])
                    if response:
                        break
                except Exception as e:
                    retry_times -= 1
                    st.warning(f"生成失败，重试 {retry_times} 次 | 错误：{str(e)}")
                    time.sleep(1)

            if st.session_state.stop_generate:
                st.info("计划生成已取消")
            elif response:
                st.session_state.plan = response
                st.session_state.plan_versions = db_manager.get_plan_versions(st.session_state.username)

                record_details = json.dumps({
                    "goal": goal,
                    "days": days,
                    "daily_time": f"{daily_time}{time_unit}",
                    "style": style,
                    "basic_level": basic_level,
                    "target_difficulty": target_difficulty,
                    "scene": scene,
                    "version": plan_version
                }, ensure_ascii=False)
                db_manager.insert_record(
                    username=st.session_state.username,
                    action_type="📅 生成学习计划",
                    details=record_details,
                    plan_version=plan_version
                )
                st.success("✅ 结构化学习计划生成成功！")
            else:
                st.error("❌ 生成失败，请稍后重试")

    if "plan" in st.session_state and not st.session_state.stop_generate:
        if st.button("🛑 取消生成"):
            st.session_state.stop_generate = True
            st.info("已取消生成")

    st.markdown("---")
    st.markdown("### 📌 学习计划管理")

    plan_versions = db_manager.get_plan_versions(st.session_state.username)
    if plan_versions:
        selected_version = st.selectbox("选择计划版本", plan_versions)
        if st.button("📋 加载该版本计划"):
            st.session_state.current_plan_version = selected_version
            st.success(f"已加载版本：{selected_version}")

    if "plan" in st.session_state and st.session_state.plan:
        st.markdown(
            """<style>.plan-card{background:#f8f9fa;padding:15px;border-radius:8px;margin:10px 0;border-left:4px solid #007bff;}.progress-bar{height:8px;border-radius:4px;margin:5px 0;background:#e9ecef;}.progress-fill{height:100%;border-radius:4px;background:#28a745;}</style>""",
            unsafe_allow_html=True)

        plan_lines = st.session_state.plan.split("\n")
        total_days = days
        current_day = 0

        st.markdown(f"#### 当前版本：{st.session_state.current_plan_version}")
        st.markdown("#### 学习进度：")
        progress = st.progress(0)

        for line in plan_lines:
            if line.strip().startswith("Day"):
                current_day += 1
                progress.progress(current_day / total_days)
                st.markdown(
                    f"""<div class="plan-card"><div>{line}</div><div class="progress-bar"><div class="progress-fill" style="width:{current_day / total_days * 100}%"></div></div></div>""",
                    unsafe_allow_html=True)
            elif line.strip():
                st.markdown(f"<div style='padding-left:20px;'>{line}</div>", unsafe_allow_html=True)

        col_download1, col_download2 = st.columns(2)
        with col_download1:
            st.download_button("📥 下载为TXT", st.session_state.plan,
                               file_name=f"study_plan_{st.session_state.current_plan_version}.txt")
        with col_download2:
            json_plan = json.dumps({"version": st.session_state.current_plan_version, "goal": goal, "days": days,
                                    "plan": st.session_state.plan}, ensure_ascii=False, indent=2)
            st.download_button("📥 下载为JSON", json_plan,
                               file_name=f"study_plan_{st.session_state.current_plan_version}.json")

        st.markdown("---")
        st.markdown("### 📝 计划执行跟踪")

        track_day = st.number_input("选择天数", min_value=1, max_value=days, value=1)
        track_col1, track_col2, track_col3 = st.columns(3)

        with track_col1:
            track_status = st.selectbox("完成状态", ["未完成", "已完成", "延期"], index=0)
        with track_col2:
            track_actual_time = st.number_input("实际学习时长（分钟）", min_value=0, value=0)
        with track_col3:
            track_notes = st.text_input("学习笔记/复盘")

        if st.button("💾 保存执行记录"):
            success = db_manager.insert_execution(
                username=st.session_state.username,
                plan_version=st.session_state.current_plan_version,
                day=track_day,
                status=track_status,
                actual_time=track_actual_time,
                notes=track_notes
            )
            if success:
                st.success(f"已保存Day{track_day}执行记录！")
                st.session_state.execution_records[track_day] = {"status": track_status,
                                                                 "actual_time": track_actual_time, "notes": track_notes}

        if st.session_state.execution_records:
            st.markdown("#### 执行记录汇总")
            for day, record in st.session_state.execution_records.items():
                st.markdown(f"- Day{day}：{record['status']} | {record['actual_time']}分钟 | {record['notes']}")

    if st.button("🗑️ 清空当前计划"):
        if "plan" in st.session_state:
            del st.session_state.plan
        st.session_state.current_plan_version = ""
        st.session_state.execution_records = {}
        st.success("已清空当前计划！")

    db_manager.close()
