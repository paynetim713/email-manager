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
    page_title="Subscription Cleaner Pro",
    page_icon="🧹",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. CSS：保持青春版风格，增加交互提示
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700&display=swap');

    .stApp {
        background: linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%);
        background-attachment: fixed;
        font-family: 'Nunito', sans-serif;
    }

    .block-container {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 2rem 3rem !important;
        border-radius: 25px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
        margin-top: 2rem;
        max-width: 800px; /* 稍微宽一点以容纳勾选框 */
    }

    h1 {
        color: #2d3436 !important;
        font-weight: 800 !important;
        text-align: center;
        font-size: 2.2rem !important;
    }
    
    .subtitle {
        text-align: center;
        color: #636e72;
        margin-bottom: 2rem;
    }

    /* 输入框样式 */
    .stTextInput > div > div {
        background-color: #f1f2f6 !important;
        border: none !important;
        border-radius: 12px !important;
        color: #2d3436 !important;
    }
    
    /* 红色删除按钮 */
    .delete-btn button {
        background: linear-gradient(45deg, #ff7675, #d63031) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(214, 48, 49, 0.3);
    }
    .delete-btn button:hover {
        transform: translateY(-2px);
    }
    
    /* 普通按钮 */
    .primary-btn button {
        background: linear-gradient(45deg, #74b9ff, #0984e3) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: bold;
    }

    /* 提示框 */
    .stInfo {
        background-color: #e3f2fd;
        border-radius: 10px;
    }
    
    /* 隐藏杂项 */
    header, footer, #MainMenu {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 核心功能函数
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
    """从 'Name <email@example.com>' 中提取纯邮箱地址"""
    match = re.search(r'<([^>]+)>', from_header)
    if match:
        return match.group(1)
    return from_header.strip() # 如果没有尖括号，直接返回

# 扫描功能
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
                # 增加了抓取 Return-Path 以便更精准删除，但这通常用 FROM 就够了
                _, msg_data = mail.fetch(e_id, '(BODY.PEEK[HEADER.FIELDS (FROM LIST-UNSUBSCRIBE)])')
                msg = email.message_from_bytes(msg_data[0][1])
                unsub = msg.get("List-Unsubscribe")
                
                if unsub:
                    from_header = decode_field(msg.get("From"))
                    sender_name = from_header.split("<")[0].strip().replace('"', '')
                    sender_email = extract_email_address(from_header) # 提取纯邮箱用于删除
                    
                    if sender_email not in seen_senders: # 使用邮箱地址去重更准确
                        link, mailto = parse_unsubscribe(unsub)
                        if link or mailto:
                            seen_senders.add(sender_email)
                            data_list.append({
                                "Select": False, # 默认不勾选
                                "Sender Name": sender_name,
                                "Sender Email": sender_email, # 隐藏列，用于后台删除
                                "Unsubscribe Link": link if link else f"mailto:{mailto}"
                            })
            except: continue
            
        mail.logout()
        progress_bar.empty()
        return data_list
    except Exception as e:
        return str(e)

# 删除功能
def delete_emails(user, password, server, targets):
    """批量删除指定发件人的所有邮件"""
    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(user, password)
        mail.select("inbox")
        
        deleted_count = 0
        status_text = st.empty()
        
        for sender_email in targets:
            status_text.write(f"🗑️ Deleting emails from: {sender_email}...")
            # 搜索该发件人的所有邮件
            status, messages = mail.search(None, f'(FROM "{sender_email}")')
            if status == 'OK':
                for num in messages[0].split():
                    mail.store(num, '+FLAGS', '\\Deleted') # 标记为删除
                deleted_count += 1
        
        mail.expunge() # 永久移除
        mail.logout()
        return True, f"Successfully cleaned emails from {deleted_count} senders."
    except Exception as e:
        return False, str(e)

# ==========================================
# 4. 界面逻辑
# ==========================================

# 状态管理
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None
if 'creds' not in st.session_state:
    st.session_state.creds = {}

st.markdown("<h1>Inbox Detox</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Unsubscribe & Delete in one go.</div>", unsafe_allow_html=True)

# --- 阶段一：登录扫描 ---
if st.session_state.scan_results is None:
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            user_email = st.text_input("Email", placeholder="yourname@gmail.com")
        with c2:
            user_pass = st.text_input("App Password", type="password", placeholder="16-digit code")
            
        # 自动填充服务器
        auto_server = ""
        if user_email and "@" in user_email:
            domain = user_email.split("@")[1]
            if "gmail" in domain: auto_server = "imap.gmail.com"
            elif "qq" in domain: auto_server = "imap.qq.com"
            elif "163" in domain: auto_server = "imap.163.com"
            elif "outlook" in domain: auto_server = "outlook.office365.com"
            
        server = st.text_input("Server", value=auto_server)
        limit = st.slider("Scan Depth", 50, 500, 100)
        
        st.write("")
        col_btn, _ = st.columns([1, 0.5])
        with col_btn:
            st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
            if st.button("Start Scan 🔍"):
                if user_email and user_pass and server:
                    # 保存凭证用于后续删除操作
                    st.session_state.creds = {"u": user_email, "p": user_pass, "s": server}
                    with st.spinner("Scanning..."):
                        res = scan_inbox(user_email, user_pass, server, limit)
                        if isinstance(res, str):
                            st.error(f"Error: {res}")
                        else:
                            st.session_state.scan_results = pd.DataFrame(res)
                            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- 阶段二：管理与清理 ---
else:
    df = st.session_state.scan_results
    
    if not df.empty:
        st.info("💡 **How to use:** Click the link to Unsubscribe first, **THEN** check the box and click 'Delete' to remove their emails.")
        
        # 使用 data_editor 实现可勾选的表格
        edited_df = st.data_editor(
            df,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select to delete emails",
                    default=False,
                    width="small"
                ),
                "Unsubscribe Link": st.column_config.LinkColumn(
                    "Action",
                    display_text="👉 Unsubscribe", # 引导性文字
                    width="medium"
                ),
                "Sender Name": st.column_config.TextColumn("Sender", width="large"),
                "Sender Email": None # 隐藏真实邮箱列，界面更干净
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed" # 禁止添加新行
        )
        
        # 获取被勾选的行
        selected_rows = edited_df[edited_df["Select"] == True]
        selected_senders = selected_rows["Sender Email"].tolist()
        
        st.write("")
        c1, c2 = st.columns([1, 1])
        
        # 重新扫描按钮
        with c1:
            if st.button("🔄 Rescan Only"):
                # 重用凭证重新扫描
                creds = st.session_state.creds
                with st.spinner("Refreshing..."):
                    res = scan_inbox(creds['u'], creds['p'], creds['s'], limit)
                    st.session_state.scan_results = pd.DataFrame(res)
                    st.rerun()

        # 核心功能：删除并刷新
        with c2:
            st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
            # 只有勾选了才显示删除按钮，防止误触
            if len(selected_senders) > 0:
                if st.button(f"🗑️ Delete Emails ({len(selected_senders)})"):
                    creds = st.session_state.creds
                    with st.spinner("Cleaning up inbox..."):
                        success, msg = delete_emails(creds['u'], creds['p'], creds['s'], selected_senders)
                        if success:
                            st.success(msg)
                            # 删除成功后立即重新扫描，验证是否干净了
                            res = scan_inbox(creds['u'], creds['p'], creds['s'], limit)
                            st.session_state.scan_results = pd.DataFrame(res)
                            st.rerun()
                        else:
                            st.error(f"Failed: {msg}")
            else:
                st.button("🗑️ Delete Emails", disabled=True) # 禁用状态
            st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        st.balloons()
        st.success("Your inbox is clean! No subscriptions found.")
        if st.button("Back"):
            st.session_state.scan_results = None
            st.rerun()
