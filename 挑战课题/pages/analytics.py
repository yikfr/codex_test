import streamlit as st
import pymysql
import pandas as pd
import datetime
import re
from utils import render_sidebar

# 页面基础配置设置 (开启宽屏模式适配图表)
st.set_page_config(page_title="学情数据分析", page_icon="📈", layout="wide")

# 1. 权限校验
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录后查看学情分析")
    st.switch_page("log_in.py")

# 渲染侧边栏
render_sidebar(active_page="analytics")

# 2. 数据库连接管理封装
def get_db_connection():
    """建立并返回数据库连接，带有完善的异常处理机制"""
    try:
        return pymysql.connect(
            host=st.secrets["mysql"]["host"],
            port=st.secrets["mysql"]["port"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            ssl={"ssl": {}}
        )
    except Exception as e:
        st.error(f"数据库连接建立失败，请检查配置或网络状态: {e}")
        return None

# 3. 核心数据拉取与缓存优化
# 使用 Streamlit 的 cache_data 装饰器，缓存结果5分钟，极大降低数据库查询压力
@st.cache_data(ttl=300)
def fetch_user_learning_data(username: str) -> pd.DataFrame:
    """
    获取用户的全部学习记录，并转化为 Pandas DataFrame 以便后续深度分析
    """
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        with conn.cursor() as cursor:
            # 提取历史记录中的核心字段
            sql = """
            SELECT action_type, details, record_time 
            FROM user_records 
            WHERE username=%s 
            ORDER BY record_time ASC
            """
            cursor.execute(sql, (username,))
            result = cursor.fetchall()
            
            if not result:
                return pd.DataFrame()
                
            # 转换为强大的 Pandas DataFrame 进行数据处理
            df = pd.DataFrame(result)
            # 确保时间列为 datetime 格式
            df['record_time'] = pd.to_datetime(df['record_time'])
            return df
    finally:
        conn.close()

# 4. 数据清洗与特征提取函数
def parse_quiz_scores(details_text: str):
    """
    使用正则表达式从测试记录 details 中提取准确率。
    匹配格式示例: "提交了 高数 测试 (简单)，共 5 题，答对 3 题"
    """
    try:
        # 正则匹配总题数和答对题数
        match = re.search(r"共\s*(\d+)\s*题，答对\s*(\d+)\s*题", details_text)
        if match:
            total = int(match.group(1))
            correct = int(match.group(2))
            accuracy = (correct / total) * 100 if total > 0 else 0
            return pd.Series([total, correct, accuracy])
    except Exception as e:
        pass
    return pd.Series([None, None, None])

# ================= 主页面渲染逻辑 =================
st.title("📈 个人学情深度分析 (Study Analytics)")
st.markdown("基于您的历史交互数据，AI为您自动生成的学习轨迹与效能报告。")

# 获取当前用户数据
df_records = fetch_user_learning_data(st.session_state.username)

if df_records.empty:
    st.info("数据量不足：您目前还没有产生足够的学习行为记录，快去使用功能吧！")
    st.stop()

# 数据预处理
# 增加日期列方便按日统计
df_records['date'] = df_records['record_time'].dt.date

# ----------------- 模块 A: 核心学习指标 -----------------
st.subheader("📊 核心学习效能指标")
col1, col2, col3, col4 = st.columns(4)

total_actions = len(df_records)
chat_count = len(df_records[df_records['action_type'].str.contains('chat')])
plan_count = len(df_records[df_records['action_type'] == '📅 生成学习计划'])
quiz_count = len(df_records[df_records['action_type'] == '📝 完成习题测试'])

col1.metric("系统总交互次数", f"{total_actions} 次", "活跃度良好")
col2.metric("AI 问答求助", f"{chat_count} 次")
col3.metric("制定学习规划", f"{plan_count} 份")
col4.metric("完成随堂测试", f"{quiz_count} 场")

st.markdown("---")

# ----------------- 模块 B: 学习行为趋势分析 -----------------
st.subheader("📅 近期学习活跃度趋势")
# 按日期统计每天的操作频次
daily_activity = df_records.groupby('date').size().reset_index(name='活跃频次')
daily_activity.set_index('date', inplace=True)
# 渲染折线图
st.line_chart(daily_activity, use_container_width=True)

# ----------------- 模块 C: 习题正确率深度挖掘 -----------------
st.subheader("🎯 习题测试准确率追踪")
# 过滤出“完成习题测试”的记录
df_quizzes = df_records[df_records['action_type'] == '📝 完成习题测试'].copy()

if not df_quizzes.empty:
    # 应用正则表达式函数提取分数
    df_quizzes[['total_q', 'correct_q', 'accuracy']] = df_quizzes['details'].apply(parse_quiz_scores)
    df_quizzes = df_quizzes.dropna(subset=['accuracy'])
    
    if not df_quizzes.empty:
        # 重置索引并可视化正确率曲线
        chart_data = df_quizzes[['record_time', 'accuracy']].set_index('record_time')
        st.area_chart(chart_data, y="accuracy", color="#4CAF50")
        
        # 统计平均正确率
        avg_acc = df_quizzes['accuracy'].mean()
        st.caption(f"💡 您的历史平均刷题正确率为 **{avg_acc:.1f}%**。")
        if avg_acc < 60:
            st.warning("⚠️ 发现薄弱环节：您的整体正确率偏低，建议使用『AI助手』深入讲解错题。")
        elif avg_acc > 85:
            st.success("🌟 基础非常扎实！建议在生成习题时尝试将难度调整为『困难』。")
else:
    st.info("您还没有完成过任何习题测试。去【习题生成】版块做几道题，即可解锁您的正确率趋势图！")

# ----------------- 模块 D: 原始数据导出报表 -----------------
st.markdown("---")
with st.expander("📥 导出我的完整学习报表 (CSV)"):
    st.write("您可以下载您的历史行为原始数据，用于本地备份或作为导师检查的佐证材料。")
    # 清理准备导出的数据
    export_df = df_records[['record_time', 'action_type', 'details']].rename(
        columns={'record_time': '发生时间', 'action_type': '行为类型', 'details': '详细内容'}
    )
    csv = export_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="下载 CSV 报表",
        data=csv,
        file_name=f"study_report_{st.session_state.username}_{datetime.date.today()}.csv",
        mime="text/csv",
    )
