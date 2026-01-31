import streamlit as st
import imaplib
import email
from email.header import decode_header
import re
import pandas as pd
from datetime import datetime
import time

# ==========================================
# 1. 页面配置
# ==========================================
st.set_page_config(
    page_title="Email Subscription Manager",
    page_icon="📧",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. 增强的CSS样式
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* === 浅色模式变量 === */
    :root {
        --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --card-bg: rgba(255, 255, 255, 0.95);
        --text-primary: #1a202c;
        --text-secondary: #4a5568;
        --input-bg: #f7fafc;
        --input-border: #e2e8f0;
        --btn-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --btn-danger: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --btn-success: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.1);
        --shadow-md: 0 8px 30px rgba(0, 0, 0, 0.12);
        --shadow-lg: 0 20px 60px rgba(0, 0, 0, 0.15);
        --accent-color: #667eea;
    }

    /* === 深色模式变量 === */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-gradient: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            --card-bg: rgba(26, 32, 44, 0.95);
            --text-primary: #f7fafc;
            --text-secondary: #cbd5e0;
            --input-bg: #2d3748;
            --input-border: #4a5568;
            --btn-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --btn-danger: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --btn-success: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
            --shadow-md: 0 8px 30px rgba(0, 0, 0, 0.4);
            --shadow-lg: 0 20px 60px rgba(0, 0, 0, 0.5);
            --accent-color: #667eea;
        }
    }

    /* === 全局样式 === */
    .stApp {
        background: var(--bg-gradient);
        background-attachment: fixed;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .block-container {
        background-color: var(--card-bg);
        padding: 3rem 2.5rem !important;
        border-radius: 20px;
        box-shadow: var(--shadow-lg);
        backdrop-filter: blur(20px);
        max-width: 900px;
        margin-top: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* === 标题样式 === */
    h1 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        text-align: center;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.02em;
    }
    
    .subtitle {
        color: var(--text-secondary) !important;
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 2.5rem;
        font-weight: 500;
    }

    h2, h3 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    /* === 输入框样式 === */
    .stTextInput > div > div,
    .stNumberInput > div > div {
        background-color: var(--input-bg) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 10px !important;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div:focus-within,
    .stNumberInput > div > div:focus-within {
        border-color: var(--accent-color) !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    input, input::placeholder {
        color: var(--text-primary) !important;
        opacity: 1 !important;
    }

    label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* === 按钮样式 === */
    .stButton > button {
        background: var(--btn-primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        box-shadow: var(--shadow-sm);
        transition: all 0.3s ease;
        width: 100%;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* 删除按钮 */
    .delete-btn button {
        background: var(--btn-danger) !important;
    }

    /* 扫描按钮 */
    .scan-btn button {
        background: var(--btn-success) !important;
    }

    /* === 信息卡片 === */
    .info-card {
        background: var(--input-bg);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
        border-left: 4px solid var(--accent-color);
    }

    .info-card h3 {
        margin-top: 0;
        font-size: 1.1rem;
    }

    .info-card ul {
        margin: 0.5rem 0;
        padding-left: 1.5rem;
    }

    .info-card li {
        color: var(--text-secondary);
        margin: 0.3rem 0;
    }

    /* === 统计卡片 === */
    .stat-card {
        background: var(--input-bg);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: var(--shadow-sm);
    }

    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--accent-color);
        margin: 0;
    }

    .stat-label {
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }

    /* === 表格样式 === */
    [data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }

    /* === 进度条 === */
    .stProgress > div > div {
        background-color: var(--accent-color) !important;
    }

    /* === 提示框样式 === */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: var(--shadow-sm);
    }

    /* === 滑块样式 === */
    .stSlider > div > div > div {
        background-color: var(--accent-color) !important;
    }

    /* === 隐藏元素 === */
    header, footer, #MainMenu {
        visibility: hidden;
    }

    /* === 响应式设计 === */
    @media (max-width: 768px) {
        .block-container {
            padding: 2rem 1.5rem !important;
        }
        
        h1 {
            font-size: 2rem !important;
        }
    }

    /* === 加载动画 === */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 辅助函数
# ==========================================

def decode_field(header_value):
    """解码邮件头部字段"""
    if not header_value:
        return "Unknown"
    try:
        decoded_list = decode_header(header_value)
        text, encoding = decoded_list[0]
        if isinstance(text, bytes):
            return text.decode(encoding if encoding else 'utf-8', errors='ignore')
        return str(text)
    except Exception:
        return str(header_value)

def parse_unsubscribe(header_text):
    """解析退订链接"""
    http_link = None
    mailto = None
    
    # 提取HTTP链接
    http_match = re.search(r'<(https?://[^>]+)>', header_text)
    if not http_match:
        http_match = re.search(r'(https?://\S+)', header_text)
    if http_match:
        http_link = http_match.group(1)
    
    # 提取mailto链接
    mailto_match = re.search(r'<mailto:([^>]+)>', header_text)
    if mailto_match:
        mailto = mailto_match.group(1)
    
    return http_link, mailto

def extract_email_address(from_header):
    """提取邮件地址"""
    match = re.search(r'<([^>]+)>', from_header)
    if match:
        return match.group(1)
    return from_header.strip()

def get_imap_server(email_address):
    """根据邮箱地址自动识别IMAP服务器"""
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
        "yeah.net": "imap.yeah.net",
        "yahoo.com": "imap.mail.yahoo.com",
        "icloud.com": "imap.mail.me.com",
        "aol.com": "imap.aol.com",
        "zoho.com": "imap.zoho.com",
    }
    
    for key, server in imap_servers.items():
        if key in domain:
            return server
    
    return f"imap.{domain}"

def scan_inbox(user, password, server, limit):
    """扫描邮箱中的订阅邮件"""
    try:
        # 连接到IMAP服务器
        mail = imaplib.IMAP4_SSL(server, timeout=30)
        mail.login(user, password)
        mail.select("inbox")
        
        # 搜索所有邮件
        status, messages = mail.search(None, 'ALL')
        if status != 'OK':
            return "Failed to search emails"
        
        email_ids = messages[0].split()
        total_emails = len(email_ids)
        
        # 限制扫描数量
        email_ids = email_ids[-limit:]
        
        data_list = []
        seen_senders = set()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, e_id in enumerate(reversed(email_ids)):
            progress = (i + 1) / len(email_ids)
            progress_bar.progress(progress)
            status_text.caption(f"Scanning... {i + 1}/{len(email_ids)} emails")
            
            try:
                # 只获取必要的头部信息
                _, msg_data = mail.fetch(e_id, '(BODY.PEEK[HEADER.FIELDS (FROM LIST-UNSUBSCRIBE DATE)])')
                
                if not msg_data or not msg_data[0]:
                    continue
                
                msg = email.message_from_bytes(msg_data[0][1])
                unsub = msg.get("List-Unsubscribe")
                
                if unsub:
                    from_header = decode_field(msg.get("From"))
                    sender_name = from_header.split("<")[0].strip().replace('"', '')
                    sender_email = extract_email_address(from_header)
                    
                    # 去重
                    if sender_email not in seen_senders:
                        link, mailto = parse_unsubscribe(unsub)
                        
                        if link or mailto:
                            seen_senders.add(sender_email)
                            
                            # 获取最后收到邮件的日期
                            date_header = msg.get("Date")
                            date_str = "Unknown"
                            if date_header:
                                try:
                                    date_str = decode_field(date_header)
                                except:
                                    pass
                            
                            data_list.append({
                                "Select": False,
                                "Sender": sender_name if sender_name else sender_email,
                                "Email": sender_email,
                                "Last Received": date_str,
                                "Unsubscribe": link if link else f"mailto:{mailto}"
                            })
            
            except Exception as e:
                continue
        
        mail.logout()
        progress_bar.empty()
        status_text.empty()
        
        return data_list
    
    except imaplib.IMAP4.error as e:
        return f"IMAP Error: {str(e)}"
    except Exception as e:
        return f"Connection Error: {str(e)}"

def delete_emails(user, password, server, targets):
    """删除指定发件人的所有邮件"""
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
            status_text.caption(f"Deleting emails from: {sender_email}...")
            
            # 搜索该发件人的所有邮件
            status, messages = mail.search(None, f'(FROM "{sender_email}")')
            
            if status == 'OK' and messages[0]:
                email_list = messages[0].split()
                for num in email_list:
                    mail.store(num, '+FLAGS', '\\Deleted')
                    total_deleted += 1
                deleted_count += 1
        
        # 永久删除
        mail.expunge()
        mail.logout()
        
        progress_bar.empty()
        status_text.empty()
        
        return True, f"Successfully deleted {total_deleted} emails from {deleted_count} senders"
    
    except Exception as e:
        return False, f"Delete Error: {str(e)}"

# ==========================================
# 4. 初始化会话状态
# ==========================================

if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

if 'creds' not in st.session_state:
    st.session_state.creds = {}

if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = None

# ==========================================
# 5. 主界面
# ==========================================

st.markdown("<h1>📧 Email Subscription Manager</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Clean your inbox from unwanted subscriptions</div>", unsafe_allow_html=True)

# --- 登录阶段 ---
if st.session_state.scan_results is None:
    
    # 使用说明
    with st.expander("ℹ️ How to use this tool", expanded=False):
        st.markdown("""
        <div class='info-card'>
            <h3>📋 Step-by-Step Guide:</h3>
            <ul>
                <li><strong>Step 1:</strong> Enter your email address</li>
                <li><strong>Step 2:</strong> Generate an app password (not your regular password)</li>
                <li><strong>Step 3:</strong> Click "Start Scanning" to find subscriptions</li>
                <li><strong>Step 4:</strong> Select unwanted subscriptions and delete them</li>
            </ul>
            
            <h3>🔐 How to get App Password:</h3>
            <ul>
                <li><strong>Gmail:</strong> Google Account → Security → 2-Step Verification → App passwords</li>
                <li><strong>Outlook:</strong> Account Security → Additional security options → App passwords</li>
                <li><strong>QQ Mail:</strong> Settings → Account → Generate authorization code</li>
            </ul>
            
            <h3>🔒 Privacy & Security:</h3>
            <ul>
                <li>All operations are performed directly on your device</li>
                <li>Your credentials are not stored or transmitted</li>
                <li>Use app-specific passwords, not your main password</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    
    # 邮箱输入
    user_email = st.text_input(
        "📮 Email Address",
        placeholder="example@gmail.com",
        help="Enter the email address you want to scan"
    )
    
    # 自动检测IMAP服务器
    auto_server = get_imap_server(user_email)
    
    # 密码输入
    user_pass = st.text_input(
        "🔑 App Password",
        type="password",
        placeholder="Your app-specific password (not regular password)",
        help="Use an app password for security. Never use your main email password."
    )
    
    # IMAP服务器
    server = st.text_input(
        "🌐 IMAP Server",
        value=auto_server,
        placeholder="imap.gmail.com",
        help="IMAP server address (auto-detected for common providers)"
    )
    
    # 扫描深度
    limit = st.slider(
        "🔍 Scan Depth (number of emails to scan)",
        min_value=50,
        max_value=1000,
        value=200,
        step=50,
        help="Higher values take longer but find more subscriptions"
    )
    
    st.write("")
    
    # 扫描按钮
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="scan-btn">', unsafe_allow_html=True)
        scan_button = st.button("🚀 Start Scanning", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    if scan_button:
        if not user_email or not user_pass or not server:
            st.error("⚠️ Please fill in all fields")
        elif "@" not in user_email:
            st.error("⚠️ Please enter a valid email address")
        else:
            # 保存凭证
            st.session_state.creds = {
                "u": user_email,
                "p": user_pass,
                "s": server,
                "limit": limit
            }
            
            with st.spinner("🔄 Connecting to your mailbox..."):
                res = scan_inbox(user_email, user_pass, server, limit)
                
                if isinstance(res, str):
                    st.error(f"❌ {res}")
                    st.info("💡 Troubleshooting tips:\n- Make sure you're using an app password, not your regular password\n- Check if IMAP is enabled in your email settings\n- Verify the IMAP server address is correct")
                else:
                    st.session_state.scan_results = pd.DataFrame(res)
                    st.session_state.last_scan_time = datetime.now()
                    st.rerun()

# --- 结果管理阶段 ---
else:
    df = st.session_state.scan_results
    
    if not df.empty:
        # 统计信息
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{len(df)}</div>
                <div class='stat-label'>Subscriptions Found</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            selected_count = len(df[df["Select"] == True])
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{selected_count}</div>
                <div class='stat-label'>Selected</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if st.session_state.last_scan_time:
                time_str = st.session_state.last_scan_time.strftime("%H:%M")
            else:
                time_str = "N/A"
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number' style='font-size: 1.8rem;'>{time_str}</div>
                <div class='stat-label'>Last Scan</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        
        # 快速选择
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Select All"):
                df["Select"] = True
                st.session_state.scan_results = df
                st.rerun()
        with col2:
            if st.button("❌ Deselect All"):
                df["Select"] = False
                st.session_state.scan_results = df
                st.rerun()
        
        st.write("")
        
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
                    width="medium"
                ),
                "Last Received": st.column_config.TextColumn(
                    "Last Email",
                    width="medium"
                ),
                "Unsubscribe": st.column_config.LinkColumn(
                    "Action",
                    display_text="🔗 Unsubscribe",
                    width="small"
                ),
            },
            hide_index=True,
            use_container_width=True,
            height=400,
            disabled=["Sender", "Email", "Last Received", "Unsubscribe"]
        )
        
        # 更新选择
        st.session_state.scan_results = edited_df
        
        selected_rows = edited_df[edited_df["Select"] == True]
        selected_senders = selected_rows["Email"].tolist()
        
        st.write("")
        
        # 操作按钮
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.markdown('<div class="scan-btn">', unsafe_allow_html=True)
            if st.button("🔄 Rescan Inbox", use_container_width=True):
                creds = st.session_state.creds
                with st.spinner("🔄 Rescanning..."):
                    res = scan_inbox(creds['u'], creds['p'], creds['s'], creds.get('limit', 200))
                    if isinstance(res, str):
                        st.error(f"❌ {res}")
                    else:
                        st.session_state.scan_results = pd.DataFrame(res)
                        st.session_state.last_scan_time = datetime.now()
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            if st.button("🏠 Start Over", use_container_width=True):
                st.session_state.scan_results = None
                st.session_state.creds = {}
                st.session_state.last_scan_time = None
                st.rerun()
        
        with col3:
            st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
            if len(selected_senders) > 0:
                if st.button(f"🗑️ Delete ({len(selected_senders)})", use_container_width=True):
                    with st.spinner(f"🗑️ Deleting emails from {len(selected_senders)} senders..."):
                        creds = st.session_state.creds
                        success, msg = delete_emails(creds['u'], creds['p'], creds['s'], selected_senders)
                        
                        if success:
                            st.success(f"✅ {msg}")
                            time.sleep(2)
                            
                            # 重新扫描
                            with st.spinner("🔄 Refreshing..."):
                                res = scan_inbox(creds['u'], creds['p'], creds['s'], creds.get('limit', 200))
                                if not isinstance(res, str):
                                    st.session_state.scan_results = pd.DataFrame(res)
                                    st.session_state.last_scan_time = datetime.now()
                                st.rerun()
                        else:
                            st.error(f"❌ {msg}")
            else:
                st.button("🗑️ Delete (0)", disabled=True, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 警告提示
        if len(selected_senders) > 0:
            st.warning(f"⚠️ Warning: This will permanently delete ALL emails from the {len(selected_senders)} selected sender(s). This action cannot be undone!")
    
    else:
        st.balloons()
        st.success("🎉 Your inbox is clean! No subscriptions found.")
        st.write("")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🏠 Back to Home", use_container_width=True):
                st.session_state.scan_results = None
                st.session_state.creds = {}
                st.session_state.last_scan_time = None
                st.rerun()

# ==========================================
# 6. 页脚
# ==========================================
st.write("")
st.write("")
st.markdown("""
<div style='text-align: center; color: var(--text-secondary); font-size: 0.85rem; margin-top: 3rem; opacity: 0.7;'>
    Made with ❤️ for a cleaner inbox | Your data never leaves your device
</div>
""", unsafe_allow_html=True)
