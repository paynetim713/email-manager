import streamlit as st
import imaplib
import email
from email.header import decode_header
import re
import pandas as pd

# ==========================================
# 1. 页面配置
# ==========================================
st.set_page_config(
    page_title="Subscription Cleaner",
    page_icon="✨",
    layout="centered", # 关键：改为 centered 布局，防止大屏拉伸变丑
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. 顶级 CSS 设计 (现代 SaaS 风格)
# ==========================================
st.markdown("""
<style>
    /* 引入更现代的字体 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    /* === 全局背景 === */
    .stApp {
        background-color: #000000; /* 纯黑背景 */
        font-family: 'Inter', sans-serif;
    }

    /* === 核心卡片容器微调 === */
    /* Streamlit 的 centered 布局默认宽度有点窄，我们稍微放宽一点 */
    .block-container {
        max-width: 700px;
        padding-top: 4rem;
        padding-bottom: 4rem;
    }

    /* === 标题样式 === */
    h1 {
        font-weight: 600 !important;
        font-size: 2.5rem !important;
        color: #ffffff !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.02em;
    }
    .subtitle {
        text-align: center;
        color: #888888;
        font-size: 1rem;
        margin-bottom: 3rem;
        font-weight: 400;
    }

    /* === 输入框美化 (磨砂质感) === */
    .stTextInput > div > div {
        background-color: #111111 !important; /* 深灰背景 */
        border: 1px solid #333333 !important; /* 极细边框 */
        border-radius: 8px !important; /* 优雅圆角 */
        color: white !important;
        transition: all 0.2s ease;
    }
    
    /* 输入框聚焦效果 */
    .stTextInput > div > div:focus-within {
        border-color: #666666 !important;
        box-shadow: 0 0 0 1px #666666 !important;
    }
    
    /* 输入框内的文字 */
    input {
        color: #ffffff !important;
    }

    /* Label 样式 */
    .stTextInput label {
        color: #bbbbbb !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.4rem !important;
    }

    /* === 按钮定制 (高级白) === */
    .stButton > button {
        width: 100%;
        background-color: #ffffff !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 0 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        margin-top: 1rem !important;
        transition: opacity 0.2s;
    }
    .stButton > button:hover {
        opacity: 0.9;
    }
    
    /* === Expander (教程区域) === */
    .streamlit-expanderHeader {
        background-color: #000000 !important;
        color: #666666 !important;
        font-size: 0.85rem !important;
        border: none !important;
    }
    .streamlit-expanderContent {
        background-color: #000000 !important;
        color: #666666 !important;
        border: none !important;
        font-size: 0.85rem !important;
        padding-top: 0 !important;
    }
    
    /* === 结果表格美化 === */
    [data-testid="stDataFrame"] {
        border: 1px solid #333;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* 隐藏顶部红线和菜单 */
    header, footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 核心逻辑
# ==========================================
def decode_field(header_value):
    if not header_value: return "Unknown"
    try:
        decoded_list = decode_header(header_value)
        text, encoding = decoded_list[0]
        if isinstance(text, bytes):
            return text.decode(encoding if encoding else 'utf-8', errors='ignore')
        return str(text)
    except: return str(header_value)

def parse_unsubscribe(header_text):
    http_link = None
    mailto = None
    http_match = re.search(r'<(https?://[^>]+)>', header_text)
    if not http_match: http_match = re.search(r'(https?://\S+)', header_text)
    if http_match: http_link = http_match.group(1)
    mailto_match = re.search(r'<mailto:([^>]+)>', header_text)
    if mailto_match: mailto = mailto_match.group(1)
    return http_link, mailto

def scan_inbox(user, password, server, limit):
    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(user, password)
        mail.select("inbox")
        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()[-limit:]
        
        data_list = []
        seen_senders = set()
        progress_bar = st.progress(0)
        
        for i, e_id in enumerate(reversed(email_ids)):
            progress_bar.progress((i + 1) / len(email_ids))
            try:
                _, msg_data = mail.fetch(e_id, '(BODY.PEEK[HEADER.FIELDS (FROM LIST-UNSUBSCRIBE)])')
                msg = email.message_from_bytes(msg_data[0][1])
                unsub = msg.get("List-Unsubscribe")
                if unsub:
                    sender = decode_field(msg.get("From")).split("<")[0].strip().replace('"', '')
                    if sender not in seen_senders:
                        link, mailto = parse_unsubscribe(unsub)
                        if link or mailto:
                            seen_senders.add(sender)
                            data_list.append({
                                "Sender": sender,
                                "Type": "Web Link" if link else "Email",
                                "Action": link if link else f"mailto:{mailto}"
                            })
            except: continue
            
        mail.logout()
        progress_bar.empty()
        return data_list
    except Exception as e:
        return str(e)

# ==========================================
# 4. 界面布局
# ==========================================

# 状态管理
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

# --- 标题区 ---
st.markdown("<h1>Subscription Manager</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Connect your inbox to detect and unsubscribe from newsletters.</p>", unsafe_allow_html=True)

# --- 登录界面 (未扫描时显示) ---
if st.session_state.scan_results is None:
    
    # 一个干净的卡片区域
    with st.container():
        user_email = st.text_input("Email Address", placeholder="name@example.com")
        
        # 自动填充服务器逻辑
        auto_server = ""
        if user_email and "@" in user_email:
            domain = user_email.split("@")[1]
            if "gmail" in domain: auto_server = "imap.gmail.com"
            elif "qq" in domain: auto_server = "imap.qq.com"
            elif "163" in domain: auto_server = "imap.163.com"
            elif "outlook" in domain: auto_server = "outlook.office365.com"
            elif "icloud" in domain: auto_server = "imap.mail.me.com"

        user_pass = st.text_input("App Password", 
                                type="password", 
                                help="Not your login password. Check the guide below if unsure.",
                                placeholder="The 16-character app password")
        
        server = st.text_input("IMAP Server", value=auto_server)
        
        limit = st.slider("Scan Depth (Last N emails)", 50, 500, 100)
        
        if st.button("Start Scan"):
            if user_email and user_pass and server:
                with st.spinner("Connecting..."):
                    res = scan_inbox(user_email, user_pass, server, limit)
                    if isinstance(res, str):
                        st.error(f"Error: {res}")
                    else:
                        st.session_state.scan_results = res
                        st.rerun()
            else:
                st.caption("Please fill in all fields.")

    # --- 极简风格的折叠教程 ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("How to get an App Password?"):
        st.markdown("""
        **Gmail**: Account > Security > 2-Step Verification > App passwords  
        **QQ**: Settings > Account > IMAP > Generate Authorization Code  
        **Outlook**: Security > Advanced Security > App Passwords
        """)

# --- 结果展示界面 (扫描后显示) ---
else:
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"### Found {len(st.session_state.scan_results)} Subscriptions")
    with c2:
        if st.button("Rescan"):
            st.session_state.scan_results = None
            st.rerun()
            
    if st.session_state.scan_results:
        df = pd.DataFrame(st.session_state.scan_results)
        st.dataframe(
            df,
            column_config={
                "Action": st.column_config.LinkColumn(
                    "Action",
                    display_text="Unsubscribe",
                    validate="^https://.*|^mailto:.*"
                ),
                "Sender": st.column_config.TextColumn("Sender", width="large"),
                "Type": st.column_config.TextColumn("Type", width="small"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.success("No active subscriptions found in the scanned range.")
