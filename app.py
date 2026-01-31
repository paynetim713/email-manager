import streamlit as st
import imaplib
import email
from email.header import decode_header
import re
import pandas as pd
from datetime import datetime
import time

# ==========================================
# 页面配置
# ==========================================
st.set_page_config(
    page_title="Email Subscription Manager",
    page_icon="📨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# CSS 样式表 (已修复滑块数字显示问题)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* === 基础变量 === */
    :root {
        --background: #f8f9fa;
        --surface: #ffffff;
        --primary: #2563eb;
        --text-primary: #111827;
        --text-secondary: #6b7280;
        --border: #e5e7eb;
    }

    /* === 深色模式适配 (精准修复，不误伤滑块) === */
    @media (prefers-color-scheme: dark) {
        :root {
            --background: #0e1117;
            --surface: #1f2937;
            --primary: #3b82f6;
            --text-primary: #f9fafb;
            --text-secondary: #d1d5db;
            --border: #374151;
        }
        
        /* 只针对文本类元素强制变白，避开组件容器 */
        .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
        .stMarkdown h4, .stMarkdown h5, .stMarkdown h6, 
        .stMarkdown li, .stMarkdown span, .stMarkdown label,
        .subtitle, .stat-label, .card-title {
            color: #f9fafb !important;
        }
        
        /* 修复输入框深色背景 */
        .stTextInput > div > div {
            background-color: #1f2937 !important;
            color: white !important;
            border-color: #374151 !important;
        }
        .stTextInput input {
            color: white !important;
        }
    }

    /* === 通用样式 === */
    .stApp {
        background-color: var(--background);
        font-family: 'Inter', sans-serif;
    }

    /* 头部样式 */
    .header-container {
        text-align: center;
        margin-bottom: 2rem;
        padding-bottom: 2rem;
        border-bottom: 1px solid var(--border);
    }
    .main-title {
        font-size: 2rem;
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1rem;
        color: var(--text-secondary);
    }

    /* 统计卡片 */
    .stat-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--primary);
    }
    .stat-label {
        font-size: 0.85rem;
        color: var(--text-secondary);
    }

    /* 按钮优化 */
    .stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    
    /* 红色删除按钮 */
    .btn-danger button {
        background-color: #ef4444 !important;
        color: white !important;
        border: none !important;
    }
    .btn-danger button:hover {
        background-color: #dc2626 !important;
    }
    
    /* 绿色开始按钮 */
    .btn-success button {
        background-color: #10b981 !important;
        color: white !important;
        border: none !important;
    }
    .btn-success button:hover {
        background-color: #059669 !important;
    }

    /* 隐藏杂项 */
    header, footer, #MainMenu {visibility: hidden;}
    
    /* 链接样式 */
    a { color: var(--primary); text-decoration: none; }
    a:hover { text-decoration: underline; }

</style>
""", unsafe_allow_html=True)

# ==========================================
# 核心逻辑函数
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
    if match: return match.group(1)
    return from_header.strip()

def get_imap_server(email_address):
    if not email_address or "@" not in email_address: return ""
    domain = email_address.split("@")[1].lower()
    imap_servers = {
        "gmail.com": "imap.gmail.com",
        "qq.com": "imap.qq.com",
        "163.com": "imap.163.com",
        "outlook.com": "outlook.office365.com",
    }
    for key, server in imap_servers.items():
        if key in domain: return server
    return f"imap.{domain}"

def scan_inbox(user, password, server, limit):
    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(user, password)
        mail.select("inbox")
        status, messages = mail.search(None, 'ALL')
        if status != 'OK': return "Failed to search"
        
        email_ids = messages[0].split()[-limit:]
        data_list = []
        seen_senders = set()
        progress_bar = st.progress(0)
        
        for i, e_id in enumerate(reversed(email_ids)):
            progress_bar.progress((i + 1) / len(email_ids))
            try:
                _, msg_data = mail.fetch(e_id, '(BODY.PEEK[HEADER.FIELDS (FROM LIST-UNSUBSCRIBE DATE)])')
                msg = email.message_from_bytes(msg_data[0][1])
                unsub = msg.get("List-Unsubscribe")
                if unsub:
                    from_header = decode_field(msg.get("From"))
                    sender_email = extract_email_address(from_header)
                    if sender_email not in seen_senders:
                        link, mailto = parse_unsubscribe(unsub)
                        if link or mailto:
                            seen_senders.add(sender_email)
                            data_list.append({
                                "Select": False,
                                "Sender": from_header.split("<")[0].strip().replace('"', ''),
                                "Email": sender_email,
                                "Unsubscribe": link if link else f"mailto:{mailto}"
                            })
            except: continue
        mail.logout()
        progress_bar.empty()
        return data_list
    except Exception as e: return f"Error: {str(e)}"

def delete_emails(user, password, server, targets):
    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(user, password)
        mail.select("inbox")
        count = 0
        for sender in targets:
            status, msgs = mail.search(None, f'(FROM "{sender}")')
            if status == 'OK':
                for num in msgs[0].split():
                    mail.store(num, '+FLAGS', '\\Deleted')
                count += 1
        mail.expunge()
        mail.logout()
        return True, f"Cleaned {count} senders."
    except Exception as e: return False, str(e)

# ==========================================
# 状态管理
# ==========================================
if 'scan_results' not in st.session_state: st.session_state.scan_results = None
if 'creds' not in st.session_state: st.session_state.creds = {}
if 'last_scan_time' not in st.session_state: st.session_state.last_scan_time = None

# ==========================================
# 主界面
# ==========================================

# 标题区
st.markdown("""
<div class="header-container">
    <h1 class="main-title">Email Manager</h1>
    <p class="subtitle">Quickly unsubscribe and clean your inbox</p>
</div>
""", unsafe_allow_html=True)

# 登录阶段
if st.session_state.scan_results is None:
    
    # 使用指南
    with st.expander("📝 How to get App Password?"):
        st.markdown("""
        * **Gmail**: Google Account > Security > 2-Step Verification > App passwords
        * **QQ Mail**: Settings > Account > IMAP > Generate Code
        * **Outlook**: Security > Advanced > App Passwords
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        user_email = st.text_input("Email Address", placeholder="name@example.com")
        auto_server = get_imap_server(user_email)
    with col2:
        server = st.text_input("IMAP Server", value=auto_server)

    user_pass = st.text_input("App Password", type="password", help="Use your 16-digit App Password")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # === 滑块：原生样式，数字显示正常 ===
    limit = st.slider("Scan Depth (Latest emails)", 50, 1000, 200, step=50)
    st.caption("Higher depth takes longer to scan.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 开始按钮
    st.markdown('<div class="btn-success">', unsafe_allow_html=True)
    if st.button("Start Scanning", use_container_width=True):
        if user_email and user_pass and server:
            st.session_state.creds = {"u": user_email, "p": user_pass, "s": server, "limit": limit}
            with st.spinner("Scanning..."):
                res = scan_inbox(user_email, user_pass, server, limit)
                if isinstance(res, str):
                    st.error(res)
                else:
                    st.session_state.scan_results = pd.DataFrame(res)
                    st.session_state.last_scan_time = datetime.now()
                    st.rerun()
        else:
            st.warning("Please enter your email credentials.")
    st.markdown('</div>', unsafe_allow_html=True)

# 结果阶段
else:
    df = st.session_state.scan_results
    
    if not df.empty:
        # 统计数据
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='stat-card'><div class='stat-value'>{len(df)}</div><div class='stat-label'>Subscriptions</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='stat-card'><div class='stat-value'>{len(df[df['Select']==True])}</div><div class='stat-label'>Selected</div></div>", unsafe_allow_html=True)
        with c3:
            t = st.session_state.last_scan_time.strftime("%H:%M")
            st.markdown(f"<div class='stat-card'><div class='stat-value'>{t}</div><div class='stat-label'>Scan Time</div></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # 选择按钮
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Select All", use_container_width=True):
                df["Select"] = True
                st.session_state.scan_results = df
                st.rerun()
        with col_btn2:
            if st.button("Deselect All", use_container_width=True):
                df["Select"] = False
                st.session_state.scan_results = df
                st.rerun()

        # 数据表
        edited_df = st.data_editor(
            df,
            column_config={
                "Select": st.column_config.CheckboxColumn("Mark", width="small"),
                "Unsubscribe": st.column_config.LinkColumn("Action", display_text="👉 Unsubscribe"),
                "Sender": st.column_config.TextColumn("Sender", width="large"),
                "Email": st.column_config.TextColumn("Email Address", width="medium"),
            },
            hide_index=True,
            use_container_width=True,
            height=500,
            disabled=["Sender", "Email", "Unsubscribe"]
        )
        st.session_state.scan_results = edited_df
        
        # 底部操作栏
        st.markdown("<hr>", unsafe_allow_html=True)
        selected_emails = edited_df[edited_df["Select"] == True]["Email"].tolist()
        
        b1, b2 = st.columns([1, 2])
        with b1:
            if st.button("Back", use_container_width=True):
                st.session_state.scan_results = None
                st.rerun()
        
        with b2:
            st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
            if selected_emails:
                if st.button(f"🗑️ Delete {len(selected_emails)} Senders", use_container_width=True):
                    creds = st.session_state.creds
                    with st.spinner("Cleaning..."):
                        success, msg = delete_emails(creds['u'], creds['p'], creds['s'], selected_emails)
                        if success:
                            st.success(msg)
                            time.sleep(1)
                            # 自动刷新
                            res = scan_inbox(creds['u'], creds['p'], creds['s'], creds['limit'])
                            st.session_state.scan_results = pd.DataFrame(res)
                            st.rerun()
                        else:
                            st.error(msg)
            else:
                st.button("Delete (Select first)", disabled=True, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        # 空状态
        st.markdown("""
        <div style="text-align: center; padding: 4rem; background: var(--surface); border-radius: 8px; border: 1px dashed var(--border);">
            <h3>✨ Your inbox is clean</h3>
            <p style="color: var(--text-secondary);">No subscriptions found in the scanned range.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Go Back", use_container_width=True):
            st.session_state.scan_results = None
            st.rerun()

# 页脚
st.markdown("""
<div style="text-align: center; margin-top: 3rem; color: var(--text-secondary); font-size: 0.8rem;">
    Email Subscription Manager | Secure & Local
</div>
""", unsafe_allow_html=True)
