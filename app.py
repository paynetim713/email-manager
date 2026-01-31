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
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 专业简洁的CSS设计
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* 浅色模式 */
    :root {
        --background: #f8f9fa;
        --surface: #ffffff;
        --primary: #2563eb;
        --primary-hover: #1d4ed8;
        --text-primary: #111827;
        --text-secondary: #6b7280;
        --text-tertiary: #9ca3af;
        --border: #e5e7eb;
        --border-light: #f3f4f6;
        --success: #10b981;
        --error: #ef4444;
        --warning: #f59e0b;
        --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    /* 深色模式 */
    @media (prefers-color-scheme: dark) {
        :root {
            --background: #111827;
            --surface: #1f2937;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --text-primary: #f9fafb;
            --text-secondary: #d1d5db;
            --text-tertiary: #9ca3af;
            --border: #374151;
            --border-light: #2d3748;
            --success: #34d399;
            --error: #f87171;
            --warning: #fbbf24;
            --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.3);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        }
    }

    /* 全局样式 */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background-color: var(--background);
    }

    .main .block-container {
        max-width: 1200px;
        padding: 2rem 1rem;
    }

    /* 标题区域 */
    .header-container {
        text-align: center;
        margin-bottom: 3rem;
        padding-bottom: 2rem;
        border-bottom: 1px solid var(--border);
    }

    .main-title {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.025em;
    }

    .subtitle {
        font-size: 1rem;
        color: var(--text-secondary);
        font-weight: 400;
        margin: 0;
    }

    /* 卡片样式 */
    .card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow);
    }

    .card-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 1rem 0;
    }

    /* 输入框 */
    .stTextInput > div > div,
    .stNumberInput > div > div {
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
    }

    .stTextInput > div > div:focus-within,
    .stNumberInput > div > div:focus-within {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }

    input {
        color: var(--text-primary) !important;
        font-size: 0.9rem !important;
    }

    input::placeholder {
        color: var(--text-tertiary) !important;
    }

    label {
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.5rem !important;
    }

    /* 按钮 */
    .stButton > button {
        background-color: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.2s !important;
        box-shadow: var(--shadow) !important;
    }

    .stButton > button:hover {
        background-color: var(--primary-hover) !important;
        box-shadow: var(--shadow-md) !important;
    }

    .stButton > button:disabled {
        opacity: 0.5 !important;
        cursor: not-allowed !important;
    }

    /* 按钮变体 */
    .btn-danger button {
        background-color: var(--error) !important;
    }

    .btn-danger button:hover {
        background-color: #dc2626 !important;
    }

    .btn-success button {
        background-color: var(--success) !important;
    }

    .btn-success button:hover {
        background-color: #059669 !important;
    }

    .btn-secondary button {
        background-color: var(--border-light) !important;
        color: var(--text-primary) !important;
    }

    .btn-secondary button:hover {
        background-color: var(--border) !important;
    }

    /* 统计卡片 */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }

    .stat-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.25rem;
        text-align: center;
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary);
        margin: 0;
        line-height: 1;
    }

    .stat-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-top: 0.5rem;
        font-weight: 500;
    }

    /* 表格 */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }

    [data-testid="stDataFrame"] th {
        background-color: var(--border-light) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        padding: 0.75rem !important;
    }

    [data-testid="stDataFrame"] td {
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
        padding: 0.75rem !important;
    }

    /* 提示信息 */
    .stAlert {
        border-radius: 6px !important;
        border: 1px solid transparent !important;
        font-size: 0.9rem !important;
    }

    .stSuccess {
        background-color: rgba(16, 185, 129, 0.1) !important;
        border-color: var(--success) !important;
        color: var(--text-primary) !important;
    }

    .stError {
        background-color: rgba(239, 68, 68, 0.1) !important;
        border-color: var(--error) !important;
        color: var(--text-primary) !important;
    }

    .stWarning {
        background-color: rgba(245, 158, 11, 0.1) !important;
        border-color: var(--warning) !important;
        color: var(--text-primary) !important;
    }

    .stInfo {
        background-color: rgba(37, 99, 235, 0.1) !important;
        border-color: var(--primary) !important;
        color: var(--text-primary) !important;
    }

    /* 滑块 */
    .stSlider [data-baseweb="slider"] {
        background-color: var(--primary) !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }

    .streamlit-expanderContent {
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 6px 6px !important;
    }

    /* 进度条 */
    .stProgress > div > div {
        background-color: var(--primary) !important;
    }

    /* 隐藏元素 */
    header, footer, #MainMenu {
        visibility: hidden;
    }

    /* 帮助文本 */
    .help-text {
        font-size: 0.875rem;
        color: var(--text-tertiary);
        margin-top: 0.25rem;
    }

    /* 分隔线 */
    hr {
        border: none;
        border-top: 1px solid var(--border);
        margin: 2rem 0;
    }

    /* 操作按钮组 */
    .action-buttons {
        display: flex;
        gap: 0.75rem;
        margin-top: 1.5rem;
    }

    /* 信息列表 */
    .info-list {
        list-style: none;
        padding: 0;
        margin: 1rem 0;
    }

    .info-list li {
        color: var(--text-secondary);
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--border-light);
        font-size: 0.9rem;
    }

    .info-list li:last-child {
        border-bottom: none;
    }

    .info-list strong {
        color: var(--text-primary);
        font-weight: 600;
    }

    /* 空状态 */
    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: var(--text-secondary);
    }

    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }

    /* 响应式 */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem 0.5rem;
        }

        .main-title {
            font-size: 1.5rem;
        }

        .stats-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 核心功能函数
# ==========================================

def decode_field(header_value):
    if not header_value:
        return "Unknown"
    try:
        decoded_list = decode_header(header_value)
        text, encoding = decoded_list[0]
        if isinstance(text, bytes):
            return text.decode(encoding if encoding else 'utf-8', errors='ignore')
        return str(text)
    except:
        return str(header_value)

def parse_unsubscribe(header_text):
    http_link = None
    mailto = None
    
    http_match = re.search(r'<(https?://[^>]+)>', header_text)
    if not http_match:
        http_match = re.search(r'(https?://\S+)', header_text)
    if http_match:
        http_link = http_match.group(1)
    
    mailto_match = re.search(r'<mailto:([^>]+)>', header_text)
    if mailto_match:
        mailto = mailto_match.group(1)
    
    return http_link, mailto

def extract_email_address(from_header):
    match = re.search(r'<([^>]+)>', from_header)
    if match:
        return match.group(1)
    return from_header.strip()

def get_imap_server(email_address):
    if not email_address or "@" not in email_address:
        return ""
    
    domain = email_address.split("@")[1].lower()
    
    imap_servers = {
        "gmail.com": "imap.gmail.com",
        "googlemail.com": "imap.gmail.com",
        "outlook.com": "outlook.office365.com",
        "hotmail.com": "outlook.office365.com",
        "live.com": "outlook.office365.com",
        "qq.com": "imap.qq.com",
        "163.com": "imap.163.com",
        "126.com": "imap.126.com",
        "yahoo.com": "imap.mail.yahoo.com",
        "icloud.com": "imap.mail.me.com",
    }
    
    for key, server in imap_servers.items():
        if key in domain:
            return server
    
    return f"imap.{domain}"

def scan_inbox(user, password, server, limit):
    try:
        mail = imaplib.IMAP4_SSL(server, timeout=30)
        mail.login(user, password)
        mail.select("inbox")
        
        status, messages = mail.search(None, 'ALL')
        if status != 'OK':
            return "Failed to search emails"
        
        email_ids = messages[0].split()
        email_ids = email_ids[-limit:]
        
        data_list = []
        seen_senders = set()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, e_id in enumerate(reversed(email_ids)):
            progress = (i + 1) / len(email_ids)
            progress_bar.progress(progress)
            status_text.caption(f"Scanning: {i + 1} / {len(email_ids)}")
            
            try:
                _, msg_data = mail.fetch(e_id, '(BODY.PEEK[HEADER.FIELDS (FROM LIST-UNSUBSCRIBE DATE)])')
                
                if not msg_data or not msg_data[0]:
                    continue
                
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
                            
                            date_header = msg.get("Date")
                            date_str = "Unknown"
                            if date_header:
                                try:
                                    date_str = decode_field(date_header)[:16]
                                except:
                                    pass
                            
                            data_list.append({
                                "Select": False,
                                "Sender": sender_name if sender_name else sender_email,
                                "Email": sender_email,
                                "Last Received": date_str,
                                "Unsubscribe": link if link else f"mailto:{mailto}"
                            })
            
            except:
                continue
        
        mail.logout()
        progress_bar.empty()
        status_text.empty()
        
        return data_list
    
    except Exception as e:
        return f"Error: {str(e)}"

def delete_emails(user, password, server, targets):
    try:
        mail = imaplib.IMAP4_SSL(server, timeout=30)
        mail.login(user, password)
        mail.select("inbox")
        
        deleted_count = 0
        total_deleted = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, sender_email in enumerate(targets):
            progress = (i + 1) / len(targets)
            progress_bar.progress(progress)
            status_text.caption(f"Deleting from: {sender_email}")
            
            status, messages = mail.search(None, f'(FROM "{sender_email}")')
            
            if status == 'OK' and messages[0]:
                email_list = messages[0].split()
                for num in email_list:
                    mail.store(num, '+FLAGS', '\\Deleted')
                    total_deleted += 1
                deleted_count += 1
        
        mail.expunge()
        mail.logout()
        
        progress_bar.empty()
        status_text.empty()
        
        return True, f"Deleted {total_deleted} emails from {deleted_count} senders"
    
    except Exception as e:
        return False, f"Error: {str(e)}"

# ==========================================
# 会话状态初始化
# ==========================================

if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

if 'creds' not in st.session_state:
    st.session_state.creds = {}

if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = None

# ==========================================
# 主界面
# ==========================================

# 标题
st.markdown("""
<div class="header-container">
    <h1 class="main-title">Email Subscription Manager</h1>
    <p class="subtitle">Clean your inbox from unwanted subscriptions</p>
</div>
""", unsafe_allow_html=True)

# 登录阶段
if st.session_state.scan_results is None:
    
    # 使用说明
    with st.expander("How to use this tool"):
        st.markdown("""
        <ul class="info-list">
            <li><strong>Step 1:</strong> Enter your email address</li>
            <li><strong>Step 2:</strong> Generate an app-specific password (not your regular password)</li>
            <li><strong>Step 3:</strong> Click Start Scanning to find subscriptions</li>
            <li><strong>Step 4:</strong> Select unwanted subscriptions and delete them</li>
        </ul>
        
        <p style="margin-top: 1rem; color: var(--text-secondary); font-size: 0.9rem;">
            <strong>Security:</strong> All operations are performed locally. Your credentials are never stored or transmitted.
        </p>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 登录表单
    col1, col2 = st.columns([2, 1])
    
    with col1:
        user_email = st.text_input(
            "Email Address",
            placeholder="your.email@example.com"
        )
    
    with col2:
        auto_server = get_imap_server(user_email)
        server = st.text_input(
            "IMAP Server",
            value=auto_server,
            placeholder="imap.gmail.com"
        )
    
    user_pass = st.text_input(
        "App Password",
        type="password",
        placeholder="Enter your app-specific password",
        help="Generate an app password from your email provider's security settings"
    )
    
    limit = st.slider(
        "Number of emails to scan",
        min_value=50,
        max_value=1000,
        value=200,
        step=50
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="btn-success">', unsafe_allow_html=True)
        if st.button("Start Scanning", use_container_width=True):
            if not user_email or not user_pass or not server:
                st.error("Please fill in all required fields")
            elif "@" not in user_email:
                st.error("Please enter a valid email address")
            else:
                st.session_state.creds = {
                    "u": user_email,
                    "p": user_pass,
                    "s": server,
                    "limit": limit
                }
                
                with st.spinner("Connecting to your mailbox..."):
                    res = scan_inbox(user_email, user_pass, server, limit)
                    
                    if isinstance(res, str):
                        st.error(res)
                    else:
                        st.session_state.scan_results = pd.DataFrame(res)
                        st.session_state.last_scan_time = datetime.now()
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 结果管理阶段
else:
    df = st.session_state.scan_results
    
    if not df.empty:
        # 统计信息
        selected_count = len(df[df["Select"] == True])
        
        cols = st.columns(3)
        with cols[0]:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{len(df)}</div>
                <div class="stat-label">Subscriptions Found</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{selected_count}</div>
                <div class="stat-label">Selected</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[2]:
            time_str = st.session_state.last_scan_time.strftime("%H:%M") if st.session_state.last_scan_time else "N/A"
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value" style="font-size: 1.5rem;">{time_str}</div>
                <div class="stat-label">Last Scan</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 快速操作
        col1, col2, col3, col4 = st.columns([1, 1, 2, 2])
        with col1:
            if st.button("Select All", use_container_width=True):
                df["Select"] = True
                st.session_state.scan_results = df
                st.rerun()
        with col2:
            if st.button("Deselect All", use_container_width=True):
                df["Select"] = False
                st.session_state.scan_results = df
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 数据表格
        edited_df = st.data_editor(
            df,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    default=False,
                    width="small"
                ),
                "Sender": st.column_config.TextColumn(
                    "Sender",
                    width="large"
                ),
                "Email": st.column_config.TextColumn(
                    "Email Address",
                    width="large"
                ),
                "Last Received": st.column_config.TextColumn(
                    "Last Email",
                    width="medium"
                ),
                "Unsubscribe": st.column_config.LinkColumn(
                    "Unsubscribe Link",
                    display_text="Open Link",
                    width="medium"
                ),
            },
            hide_index=True,
            use_container_width=True,
            height=700,
            disabled=["Sender", "Email", "Last Received", "Unsubscribe"]
        )
        
        st.session_state.scan_results = edited_df
        
        selected_rows = edited_df[edited_df["Select"] == True]
        selected_senders = selected_rows["Email"].tolist()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 操作按钮
        if len(selected_senders) > 0:
            st.warning(f"Warning: This will permanently delete all emails from {len(selected_senders)} selected sender(s)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="btn-success">', unsafe_allow_html=True)
            if st.button("Rescan Inbox", use_container_width=True):
                creds = st.session_state.creds
                with st.spinner("Rescanning..."):
                    res = scan_inbox(creds['u'], creds['p'], creds['s'], creds.get('limit', 200))
                    if isinstance(res, str):
                        st.error(res)
                    else:
                        st.session_state.scan_results = pd.DataFrame(res)
                        st.session_state.last_scan_time = datetime.now()
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="btn-secondary">', unsafe_allow_html=True)
            if st.button("Start Over", use_container_width=True):
                st.session_state.scan_results = None
                st.session_state.creds = {}
                st.session_state.last_scan_time = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
            if len(selected_senders) > 0:
                if st.button(f"Delete Selected ({len(selected_senders)})", use_container_width=True):
                    with st.spinner(f"Deleting emails from {len(selected_senders)} senders..."):
                        creds = st.session_state.creds
                        success, msg = delete_emails(creds['u'], creds['p'], creds['s'], selected_senders)
                        
                        if success:
                            st.success(msg)
                            time.sleep(2)
                            
                            with st.spinner("Refreshing..."):
                                res = scan_inbox(creds['u'], creds['p'], creds['s'], creds.get('limit', 200))
                                if not isinstance(res, str):
                                    st.session_state.scan_results = pd.DataFrame(res)
                                    st.session_state.last_scan_time = datetime.now()
                                st.rerun()
                        else:
                            st.error(msg)
            else:
                st.button("Delete Selected (0)", disabled=True, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">✓</div>
            <h3>Your inbox is clean</h3>
            <p>No subscriptions found in your mailbox</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Go Back", use_container_width=True):
                st.session_state.scan_results = None
                st.session_state.creds = {}
                st.session_state.last_scan_time = None
                st.rerun()

# 页脚
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: var(--text-tertiary); font-size: 0.875rem;">
    Your data stays on your device | Open source project
</div>
""", unsafe_allow_html=True)
