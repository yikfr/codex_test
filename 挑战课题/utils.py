import streamlit as st


def render_sidebar(active_page="main"):
    with st.sidebar:
        st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
        st.markdown("""
        <style>
        .avatar-container {
            text-align: center;
            padding: 10px;
        }
        .avatar-img {
            border-radius: 50%;
            width: 80px;
            height: 80px;
            object-fit: cover;
            border: 2px solid #ddd;
            cursor: pointer;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="avatar-container">', unsafe_allow_html=True)
        st.image("https://api.dicebear.com/7.x/adventurer/svg?seed=Felix", width=80)
        st.markdown(f"**{st.session_state.username}**", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("👤 个人主页"):
            st.switch_page("pages/profile.py")

        st.markdown("---")

        if st.button("🚹 AI助手", use_container_width=True):
            st.switch_page("pages/chat.py")
            
        if st.button("📅 学习规划", use_container_width=True):
            st.switch_page("pages/plan.py")

        if st.button("✍️ 习题生成", use_container_width=True):
            st.switch_page("pages/text.py")

        if st.button("📚 历史记录", use_container_width=True):
            st.switch_page("pages/history.py")

        st.markdown("---")

        st.link_button("关于我们","https://www.bilibili.com/video/BV1GJ411x7h7/?spm_id_from=333.337.search-card.all.click")
