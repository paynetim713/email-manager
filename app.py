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
    page_icon="🌓", # 图标暗示日夜切换
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. CSS：自适应日夜双色设计
# ==========================================
st.markdown("""
<style>
    /* 引入字体 */
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700&display=swap');

    /* === 默认变量 (浅色模式) === */
    :root {
        --bg-gradient: linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%);
        --card-bg: rgba(255, 255, 255, 0.90);
        --text-color: #2d3436;
        --input-bg: #f1f2f6;
        --input-border: transparent;
        --btn-gradient: linear-gradient(45deg, #ff9a9e 0%, #fad0c4 99%);
        --shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
    }

    /* === 深色模式覆盖 (当系统处于深色模式时生效) === */
    @media (prefers-color-scheme: dark) {
        :root {
            /* 深邃的午夜渐变 */
            --bg-gradient: linear-gradient(to right, #0f2027, #203a43, #2c5364); 
            /* 深色磨砂玻璃 */
            --card-bg: rgba(30, 30, 30, 0.80); 
            --text-color: #dfe6e9;
            --input-bg: #2d3436;
            --input-border: 1px solid #636e72;
            /* 赛博朋克蓝按钮 */
            --btn-gradient: linear-gradient(45deg, #0984e3, #00cec9); 
            --shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        }
    }

    /* === 应用变量 === */
    .stApp {
        background: var(--bg-gradient);
        background-attachment: fixed;
        font-family: 'Nunito', sans-serif;
    }

    /* 核心卡片容器 */
    .block-container {
        background-color: var(--card-bg);
        padding: 2.5rem !important;
        border-radius: 25px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(10px); /* 毛玻璃特效 */
        max-width: 750px;
        margin-top: 2rem;
    }

    /* 标题颜色 */
    h1, h2, h3, .subtitle {
        color: var(--text-color) !important;
    }
    
    h1 {
        font-weight: 800 !important;
        text-align: center;
        padding-bottom: 10px;
    }
    
    .subtitle {
        text-align: center;
        opacity: 0.8;
        margin-bottom: 2rem;
    }

    /* 输入框适配 */
    .stTextInput > div > div {
        background-color: var(--input-bg) !important;
        border: var(--input-border) !important;
        border-radius: 12px !important;
        color: var(--text-color) !important;
    }
    /* 输入框内的文字颜色 */
    input {
        color: var(--text-color) !important;
    }
    /* Label 颜色 */
    .stTextInput label {
        color: var(--text-color) !important;
        opacity: 0.8;
    }

    /* === 按钮样式 === */
    .stButton > button {
        background: var(--btn-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
    }
    
    /* 红色删除按钮单独定义 */
    .delete-btn button {
        background: linear-gradient(45deg, #ff7675, #d63031) !important;
    }

    /* 表格背景适配 */
    [data-testid="stDataFrame"] {
        background-color: transparent !important;
    }
    
    /* 隐藏杂项 */
    header, footer, #MainMenu {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 核心功能 (保持 v9 的全功能版本)
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

def extract_email_address(from_header):
    match = re.search(r'<([^>]+)>', from_header)
    if match:
        return match.group(1)
    return from_header.strip()

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
                    from_header = decode_field(msg.get("From"))
                    sender_name = from_header.split("<")[0].strip().replace('"', '')
                    sender_email = extract_email_address(from_header)
                    
                    if sender_email not in seen_senders:
                        link, mailto = parse_unsubscribe(unsub)
                        if link or mailto:
                            seen_senders.add(sender_email)
                            data_list.append({
                                "Select": False,
                                "Sender Name": sender_name,
                                "Sender Email": sender_email,
                                "Unsubscribe Link": link if link else f"mailto:{mailto}"
                            })
            except: continue
            
        mail.logout()
        progress_bar.empty()
        return data_list
    except Exception as e:
        return str(e)

def delete_emails(user, password, server, targets):
    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(user, password)
        mail.select("inbox")
        deleted_count = 0
        status_text = st.empty()
        for sender_email in targets:
            status_text.caption(f"Deleting emails from: {sender_email}...")
            status, messages = mail.search(None, f'(FROM "{sender_email}")')
            if status == 'OK':
                for num in messages[0].split():
                    mail.store(num, '+FLAGS', '\\Deleted')
                deleted_count += 1
        mail.expunge()
        mail.logout()
        status_text.empty()
        return True, f"Cleaned emails from {deleted_count} senders."
    except Exception as e:
        return False, str(e)

# ==========================================
# 4. 界面逻辑
# ==========================================

if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None
if 'creds' not in st.session_state:
    st.session_state.creds = {}

st.markdown("<h1>Subscription Manager</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Auto-detects Dark/Light mode</div>", unsafe_allow_html=True)

# --- 登录阶段 ---
if st.session_state.scan_results is None:
    with st.container():
        user_email = st.text_input("Email Address", placeholder="e.g. name@gmail.com")
        
        auto_server = ""
        if user_email and "@" in user_email:
            domain = user_email.split("@")[1]
            if "gmail" in domain: auto_server = "imap.gmail.com"
            elif "qq" in domain: auto_server = "imap.qq.com"
            elif "163" in domain: auto_server = "imap.163.com"
            elif "outlook" in domain: auto_server = "outlook.office365.com"
            
        user_pass = st.text_input("App Password", type="password", placeholder="The 16-digit code")
        server = st.text_input("IMAP Server", value=auto_server)
        limit = st.slider("Scan Depth", 50, 500, 100)
        
        st.write("")
        if st.button("Start Scanning"):
            if user_email and user_pass and server:
                st.session_state.creds = {"u": user_email, "p": user_pass, "s": server}
                with st.spinner("Connecting..."):
                    res = scan_inbox(user_email, user_pass, server, limit)
                    if isinstance(res, str):
                        st.error(f"Connection failed: {res}")
                    else:
                        st.session_state.scan_results = pd.DataFrame(res)
                        st.rerun()

# --- 结果管理阶段 ---
else:
    df = st.session_state.scan_results
    
    if not df.empty:
        st.success(f"Found {len(df)} subscriptions.")
        
        edited_df = st.data_editor(
            df,
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", default=False, width="small"),
                "Unsubscribe Link": st.column_config.LinkColumn("Action", display_text="👉 Unsubscribe", width="medium"),
                "Sender Name": st.column_config.TextColumn("Sender", width="large"),
                "Sender Email": None
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed"
        )
        
        selected_rows = edited_df[edited_df["Select"] == True]
        selected_senders = selected_rows["Sender Email"].tolist()
        
        st.write("")
        c1, c2 = st.columns([1, 1])
        
        with c1:
            if st.button("🔄 Rescan List"):
                creds = st.session_state.creds
                res = scan_inbox(creds['u'], creds['p'], creds['s'], limit)
                st.session_state.scan_results = pd.DataFrame(res)
                st.rerun()

        with c2:
            st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
            if len(selected_senders) > 0:
                if st.button(f"🗑️ Delete Selected ({len(selected_senders)})"):
                    creds = st.session_state.creds
                    success, msg = delete_emails(creds['u'], creds['p'], creds['s'], selected_senders)
                    if success:
                        st.success(msg)
                        res = scan_inbox(creds['u'], creds['p'], creds['s'], limit)
                        st.session_state.scan_results = pd.DataFrame(res)
                        st.rerun()
            else:
                st.button("Delete (Select first)", disabled=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        st.balloons()
        st.success("Your inbox is clean!")
        if st.button("Back"):
            st.session_state.scan_results = None
            st.rerun()
