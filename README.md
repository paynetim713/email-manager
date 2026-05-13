# Email Subscription Manager

Streamlit 写的小工具：连你自己的邮箱，扫一遍收件箱，把所有发过订阅邮件给你的发件人列出来，挨个一键退订。

做这个的契机：自己 Gmail 里垃圾订阅多到看不过来，逐个去"取消订阅"链接太累，所以写了这个一次性看完的工具。

**在线试用** → https://email-manager-f9xbsvcjdadz9qbymoia72.streamlit.app/

## 它怎么工作

通过 IMAP 拉一段时间内的邮件，读 `List-Unsubscribe` 头（RFC 2369 标准），统计每个发件域有多少封邮件、最早 / 最近一封什么时候发的，按数量排序。点退订按钮的话，它访问头里给的 URL 或者用 mailto 发退订请求。

整个过程数据都在内存里，**不写文件、不存数据库**，关闭页面就清了。

## 跑起来

```bash
pip install -r requirements.txt
streamlit run app.py
```

打开 `http://localhost:8501`，填邮箱地址 + IMAP App Password（Gmail / QQ / 163 这类要在邮箱设置里生成专用密码，不能用登录密码）。

## 注意事项

- 这工具**不会**自动批量退订，每条都要你确认——担心误删的话可以这么用。
- `List-Unsubscribe` 不是所有发件方都用，有的营销邮件就是不给退订链接。这类只能手动去他们网站取消。
- IMAP App Password 只在你当前会话内存里，**不**会传到任何后端服务器（这个就是它自己的后端）。

## 协议

MIT。
