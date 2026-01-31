import streamlit as st
import imaplib
import email
from email.header import decode_header
import re
import pandas as pd

# ==========================================
# 1. 页面配置 & 深度 CSS 定制
# ==========================================
st.set_page_config(
    page_title="Mail Cleaner",
    page_icon="⚫",
    layout="wide",
    initial_sidebar_state="collapsed" # 默认收起侧边栏，我们不用它了
)

# 动脑子设计的 CSS：黑白、高对比、大字号、去除默认 Streamlit 的塑料感
st.markdown("""
<style>
    /* === 全局重置 === */
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
        font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* === 隐藏顶部红线、汉堡菜单、Footer === */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* === 标题排版 === */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -2px !important;
        font-size: 3.5rem !important;
        border-bottom: 4px solid #FFFFFF;
        padding-bottom: 20px;
        margin-bottom: 40px;
        text-transform: uppercase;
    }
    
    h3 {
        font-weight: 600;
        border-left: 5px solid #fff;
        padding-left: 15px;
        margin-top: 30px;
    }

    /* === 输入框深度定制 === */
    /* 移除默认的圆角和灰色背景，改为纯黑背景+白色粗边框 */
    .stTextInput input, .stTextInput input:focus {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 0px !important; /* 直角，更硬朗 */
        padding: 15px !important;
        font-size: 1.1rem !important;
        box-shadow: none !important;
    }
    
    /* 输入框 Label */
    .stTextInput label {
        color: #FFFFFF !important;
        font-size: 0.9rem !important;
        font-weight: bold !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* === 按钮定制 === */
    /* 纯白按钮，黑字，点击反转 */
    .stButton > button {
        width: 100%;
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 0px !important;
        font-weight: 900 !important;
        text-transform: uppercase;
        padding: 15px 0 !important;
        font-size: 1.2rem !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 2px solid #FFFFFF !important;
    }

    /* === 教程区域 (Expander) === */
    .streamlit-expanderHeader {
        background-color: #111111 !important;
        color: #FFFFFF !important;
        border: 1px solid #333 !important;
        border-radius: 0px !important;
    }
    
    /* === 表格样式 === */
    [data-testid="stDataFrame"] {
        border: 1px solid #333;
    }
    
    /* 进度条颜色 */
    .stProgress > div > div > div > div {
        background-color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 核心逻辑 (保持不变，功能最重要)
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
        status_text = st.empty()
        
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
                                "SENDER": sender, # 全大写表头，更硬朗
                                "METHOD": "WEB LINK" if link else "EMAIL",
                                "ACTION": link if link else f"mailto:{mailto}"
                            })
                            status_text.caption(f"> DETECTED: {sender}")
            except: continue
            
        mail.logout()
        progress_bar.empty()
        status_text.empty()
        return data_list
    except Exception as e:
        return str(e)

# ==========================================
# 3. 全新的 UI 布局逻辑
# ==========================================

# 状态管理
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

# --- Header ---
st.markdown("# UNSUBSCRIBE PROTOCOL")

# --- 如果还没扫描结果，显示登录分栏 ---
if st.session_state.scan_results is None:
    
    # 采用 4:6 分栏：左边教程，右边操作
    col_info, col_login = st.columns([4, 6], gap="large")
    
    with col_info:
        st.markdown("### 01. REQUIRED ACCESS")
        st.markdown("""
        To scan your inbox securely, regular passwords will not work. 
        You **must** use an App Password.
        """)
        
        st.markdown("---")
        
        # 将难懂的教程做成折叠菜单，把“怎么做”喂到嘴边
        with st.expander("GMAIL (Google) 教程"):
            st.markdown("""
            1. 登录 Google 账号 -> 安全性 (Security)
            2. 开启 **两步验证 (2-Step Verification)**
            3. 搜索 "App Passwords" (应用专用密码)
            4. 创建并复制那个 **16位 乱码**
            """)
            
        with st.expander("ICLOUD / QQ / OUTLOOK"):
            st.markdown("""
            * **QQ邮箱**: 设置 -> 账户 -> 开启IMAP -> 获取授权码
            * **Outlook**: Account -> Security -> Advanced -> App Password
            * **iCloud**: Apple ID -> App-Specific Passwords
            """)

    with col_login:
        st.markdown("### 02. ESTABLISH CONNECTION")
        
        # 邮箱输入
        user_email = st.text_input("YOUR EMAIL", placeholder="name@example.com")
        
        # 自动判断服务器逻辑
        auto_server = ""
        if user_email and "@" in user_email:
            domain = user_email.split("@")[1]
            if "gmail" in domain: auto_server = "imap.gmail.com"
            elif "qq" in domain: auto_server = "imap.qq.com"
            elif "163" in domain: auto_server = "imap.163.com"
            elif "outlook" in domain or "hotmail" in domain: auto_server = "outlook.office365.com"
            elif "icloud" in domain: auto_server = "imap.mail.me.com"

        # 密码输入 (提示词修改得更直白)
        user_pass = st.text_input("APP PASSWORD (NOT LOGIN PASS)", 
                                type="password", 
                                placeholder="Paste the 16-digit code here")
        
        # 服务器地址 (如果自动判断了就填入，否则留空)
        server = st.text_input("IMAP ENDPOINT", value=auto_server)
        
        limit = st.slider("SCAN DEPTH", 50, 500, 100)
        
        st.markdown("<br>", unsafe_allow_html=True) # 增加一点间距
        
        if st.button("INITIATE SCAN"):
            if user_email and user_pass and server:
                with st.spinner("ACCESSING NEURAL NETWORK..."): # 稍微中二一点的提示语
                    res = scan_inbox(user_email, user_pass, server, limit)
                    if isinstance(res, str): # 如果返回是字符串，说明报错了
                        st.error(f"CONNECTION FAILED: {res}")
                        st.warning("CHECK: 1. Did you use an App Password? 2. Is IMAP enabled?")
                    else:
                        st.session_state.scan_results = res
                        st.rerun() # 刷新页面进入结果页
            else:
                st.error("MISSING CREDENTIALS")

# --- 结果展示页 (全屏) ---
else:
    # 顶部添加一个“重新扫描”的小按钮
    c1, c2 = st.columns([8, 2])
    with c1:
        st.success(f"SCAN COMPLETE. FOUND {len(st.session_state.scan_results)} SUBSCRIPTIONS.")
    with c2:
        if st.button("NEW SCAN"):
            st.session_state.scan_results = None
            st.rerun()
            
    if st.session_state.scan_results:
        df = pd.DataFrame(st.session_state.scan_results)
        
        st.dataframe(
            df,
            column_config={
                "ACTION": st.column_config.LinkColumn(
                    "TERMINATE", # 按钮名字改得更有攻击性
                    display_text="UNSUBSCRIBE",
                    validate="^https://.*|^mailto:.*"
                ),
                "SENDER": st.column_config.TextColumn("SOURCE", width="large"),
                "METHOD": st.column_config.TextColumn("PROTOCOL", width="small"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.markdown("## NO TARGETS FOUND.")
        st.caption("Your inbox is clean.")
