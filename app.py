import streamlit as st
import imaplib
import email
from email.header import decode_header
import re
import pandas as pd

# --- 页面全局设置 ---
st.set_page_config(
    page_title="Subscription Manager",
    page_icon="✉️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS 样式---
st.markdown("""
<style>
    h1 { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 300; letter-spacing: -1px; }
    section[data-testid="stSidebar"] { background-color: #f8f9fa; }
    .stButton>button { border-radius: 4px; font-weight: 500; }
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 核心工具函数 ---
def decode_field(header_value):
    if not header_value: return "Unknown"
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

def scan_inbox(user, password, server, limit):
    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(user, password)
        mail.select("inbox")
        
        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()
        latest_ids = email_ids[-limit:]
        
        data_list = []
        seen_senders = set()

        # 进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        total = len(latest_ids)

        for i, e_id in enumerate(reversed(latest_ids)):
            progress_bar.progress((i + 1) / total)
            
            #只抓取 Header
            _, msg_data = mail.fetch(e_id, '(BODY.PEEK[HEADER.FIELDS (FROM LIST-UNSUBSCRIBE)])')
            msg = email.message_from_bytes(msg_data[0][1])
            
            unsub_header = msg.get("List-Unsubscribe")
            
            if unsub_header:
                sender_raw = msg.get("From")
                sender_name = decode_field(sender_raw)
                clean_name = sender_name.split("<")[0].strip().replace('"', '')
                
                if clean_name in seen_senders:
                    continue
                
                http_link, mailto_addr = parse_unsubscribe(unsub_header)
                
                if http_link or mailto_addr:
                    seen_senders.add(clean_name)
                    final_link = http_link if http_link else f"mailto:{mailto_addr}"
                    link_type = "Web Link" if http_link else "Email"
                    
                    data_list.append({
                        "Source": clean_name,
                        "Type": link_type,
                        "Action": final_link 
                    })
                    status_text.caption(f"Analyzing... Found: {clean_name}")

        mail.logout()
        progress_bar.empty()
        status_text.empty()
        return data_list

    except Exception as e:
        st.error(f"Connection Error: {e}")
        return []

# --- 界面主逻辑 ---
st.title("Email Subscription Manager")
st.markdown("Connect to your IMAP server to detect and manage newsletter subscriptions.")
st.divider()

if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

with st.sidebar:
    st.markdown("### Configuration")
    email_user = st.text_input("Email Address")
    email_pass = st.text_input("App Password", type="password")
    
    default_server = ""
    if "@" in email_user:
        if "gmail" in email_user: default_server = "imap.gmail.com"
        elif "qq" in email_user: default_server = "imap.qq.com"
        elif "163" in email_user: default_server = "imap.163.com"
        elif "outlook" in email_user: default_server = "outlook.office365.com"
    
    imap_server = st.text_input("IMAP Server", value=default_server)
    scan_limit = st.slider("Scan Depth", 50, 500, 100)
    
    st.markdown("---")
    if st.button("Start Scan", type="primary"):
        if email_user and email_pass and imap_server:
            with st.spinner("Processing..."):
                results = scan_inbox(email_user, email_pass, imap_server, scan_limit)
                st.session_state.scan_results = results
        else:
            st.warning("Please provide credentials.")

# --- 结果展示 ---
if st.session_state.scan_results is not None:
    data = st.session_state.scan_results
    
    if len(data) > 0:
        st.markdown(f"**Found {len(data)} Subscriptions**")
        
        df = pd.DataFrame(data)
        
        st.dataframe(
            df,
            column_config={
                "Action": st.column_config.LinkColumn(
                    "Unsubscribe",
                    display_text="Unsubscribe", 
                    validate="^https://.*|^mailto:.*"
                ),
                "Source": st.column_config.TextColumn("Sender", width="large"),
                "Type": st.column_config.TextColumn("Method", width="small"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No active subscriptions found in the scanned range.")
