from flask import Blueprint, render_template_string, request, redirect, url_for, flash
import threading, time, requests, re, random, os, json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ======== BLUEPRINT ========
nhaydz_bp = Blueprint("nhaydz", __name__, url_prefix="/nhaydz")

TASKS = {}
TASK_ID_COUNTER = 1
NHAY_FILE = "nhay.txt"

# ------------------- USER AGENTS (ƯU TIÊN DESKTOP MỚI) -------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

def get_session_with_retries():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session

# ====================== LẤY TÊN - LOẠI BỎ RÁC ======================
def get_name_from_uid(uid, cookie, fb_dtsg=None):
    """
    Trả về tên thật của UID, hoặc None nếu không lấy được hoặc tên là rác.
    """
    session = get_session_with_retries()
    user_agent = random.choice(USER_AGENTS)
    headers = {
        'Cookie': cookie,
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    session.headers.update(headers)

    # Phương thức 1: API (tốt nhất, ít bị chặn)
    if fb_dtsg:
        try:
            form = {
                f"ids[0]": uid,
                "fb_dtsg": fb_dtsg,
                "__a": "1",
                "__req": "1b",
                "__rev": "1015919737"
            }
            api_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://www.facebook.com',
                'Referer': 'https://www.facebook.com/',
            }
            resp = session.post("https://www.facebook.com/chat/user_info/", data=form, headers=api_headers, timeout=10)
            if resp.status_code == 200:
                text = resp.text
                if text.startswith("for (;;);"):
                    text = text[9:]
                data = json.loads(text)
                profile = data.get("payload", {}).get("profiles", {}).get(uid)
                if profile:
                    name = profile.get("name")
                    if name and isinstance(name, str):
                        # Loại bỏ tên rác
                        lower_name = name.lower()
                        if ("trình duyệt" not in lower_name and 
                            "hỗ trợ" not in lower_name and 
                            "facebook" not in lower_name and
                            "lỗi" not in lower_name and
                            "không tìm thấy" not in lower_name and
                            len(name) > 2):
                            return name
        except Exception as e:
            print(f"[!] API error: {e}")

    # Phương thức 2: HTML (fallback)
    urls = [
        f"https://mbasic.facebook.com/profile.php?id={uid}&v=info",
        f"https://mbasic.facebook.com/profile.php?id={uid}",
        f"https://www.facebook.com/profile.php?id={uid}",
    ]
    for url in urls:
        try:
            resp = session.get(url, timeout=12, allow_redirects=True)
            if resp.status_code != 200:
                continue
            text = resp.text
            # Nếu trang chứa "trình duyệt không hỗ trợ" thì bỏ qua
            if "trình duyệt" in text.lower() and "không hỗ trợ" in text.lower():
                continue
            if "login" in text.lower() or "Không tìm thấy" in text:
                continue
            # Lấy title
            match = re.search(r'<title>(.*?)</title>', text)
            if match:
                title = match.group(1).strip()
                title = re.sub(r' \| Facebook$', '', title)
                if title and "Facebook" not in title and "login" not in title.lower():
                    lower_title = title.lower()
                    if ("trình duyệt" not in lower_title and 
                        "hỗ trợ" not in lower_title and
                        "lỗi" not in lower_title and
                        "không tìm thấy" not in lower_title):
                        return title
            # Lấy h1
            match = re.search(r'<h1[^>]*>([^<]+)</h1>', text)
            if match:
                name = match.group(1).strip()
                if name and len(name) > 1:
                    lower_name = name.lower()
                    if ("trình duyệt" not in lower_name and 
                        "hỗ trợ" not in lower_name and
                        "lỗi" not in lower_name and
                        "không tìm thấy" not in lower_name):
                        return name
            # Meta og:title
            match = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', text)
            if match:
                name = match.group(1).strip()
                lower_name = name.lower()
                if ("trình duyệt" not in lower_name and 
                    "hỗ trợ" not in lower_name and
                    "lỗi" not in lower_name and
                    "không tìm thấy" not in lower_name):
                    return name
        except Exception as e:
            print(f"[!] HTML error: {e}")
            continue
    return None

# ====================== CLASS MESSENGER (SIÊU CỨNG) ======================
class Messenger:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.extract_user_id()
        self.user_agent = random.choice(USER_AGENTS)
        self.fb_dtsg = None
        self.name = ""
        self.session = get_session_with_retries()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.facebook.com/',
            'Upgrade-Insecure-Requests': '1',
        })
        self.init_params()

    def extract_user_id(self):
        match = re.search(r"c_user=(\d+)", self.cookie)
        if not match:
            raise Exception("Cookie không có c_user")
        return match.group(1)

    def _get_dtsg_from_html(self, text):
        patterns = [
            r'name="fb_dtsg"\s+value="([^"]+)"',
            r'"fb_dtsg":"([^"]+)"',
            r'fb_dtsg\s*=\s*"([^"]+)"',
            r'FB_DTSG\s*=\s*"([^"]+)"',
            r'"token":"([^"]+)"',
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1)
        scripts = re.findall(r'<script[^>]*>([\s\S]*?)</script>', text)
        for script in scripts:
            if 'fb_dtsg' in script:
                m = re.search(r'fb_dtsg\s*[:=]\s*"([^"]+)"', script)
                if m:
                    return m.group(1)
        return None

    def _get_dtsg_from_ajax(self):
        try:
            url = "https://www.facebook.com/ajax/bootloader-endpoint/"
            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': 'https://www.facebook.com/',
            }
            resp = self.session.post(url, data={}, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'token' in data:
                    return data['token']
                if 'fb_dtsg' in data:
                    return data['fb_dtsg']
        except:
            pass
        return None

    def init_params(self):
        urls = [
            'https://mbasic.facebook.com/me',
            'https://www.facebook.com/',
            'https://m.facebook.com/me',
            'https://mbasic.facebook.com/messages/',
            'https://www.facebook.com/messages/',
        ]
        for url in urls:
            try:
                for attempt in range(2):
                    if attempt > 0:
                        self.session.headers['User-Agent'] = random.choice(USER_AGENTS)
                    resp = self.session.get(url, timeout=12, allow_redirects=True)
                    if resp.status_code != 200:
                        continue
                    dtsg = self._get_dtsg_from_html(resp.text)
                    if dtsg:
                        self.fb_dtsg = dtsg
                        name_match = re.search(r'<title>(.*?)</title>', resp.text)
                        if name_match:
                            self.name = name_match.group(1).replace(" | Facebook", "").strip()
                        print(f"[+] Lấy fb_dtsg thành công từ {url}")
                        return
            except:
                continue

        dtsg_ajax = self._get_dtsg_from_ajax()
        if dtsg_ajax:
            self.fb_dtsg = dtsg_ajax
            try:
                prof = self.session.get('https://mbasic.facebook.com/me', timeout=10)
                if prof.status_code == 200:
                    nm = re.search(r'<title>(.*?)</title>', prof.text)
                    if nm:
                        self.name = nm.group(1).replace(" | Facebook", "").strip()
            except:
                pass
            print("[+] Lấy fb_dtsg từ Ajax thành công")
            return

        dtsg_in_cookie = re.search(r'fb_dtsg=([^;]+)', self.cookie)
        if dtsg_in_cookie:
            self.fb_dtsg = dtsg_in_cookie.group(1)
            print("[+] Lấy fb_dtsg từ cookie thành công")
            return

        raise Exception(
            "Không thể lấy fb_dtsg từ mọi nguồn. Cookie có thể hết hạn hoặc thiếu 'xs'/'datr'. "
            "Hãy đăng nhập Facebook và lấy cookie mới."
        )

    def refresh_fb_dtsg(self):
        try:
            self.session = get_session_with_retries()
            self.session.headers.update({
                'User-Agent': random.choice(USER_AGENTS),
                'Cookie': self.cookie,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
                'Connection': 'keep-alive',
                'Referer': 'https://www.facebook.com/',
            })
            self.init_params()
            print(f"[!] Refresh fb_dtsg thành công cho {self.name} ({self.user_id})")
        except Exception as e:
            print(f"[!] Refresh thất bại: {e}")

    def gui_tn(self, recipient_id, message, id_tag=None, name_tag=None, max_retries=3):
        for attempt in range(max_retries):
            timestamp = int(time.time() * 1000)
            data = {
                'thread_fbid': recipient_id,
                'action_type': 'ma-type:user-generated-message',
                'body': message,
                'client': 'mercury',
                'author': f'fbid:{self.user_id}',
                'timestamp': timestamp,
                'source': 'source:chat:web',
                'offline_threading_id': str(timestamp),
                'message_id': str(timestamp),
                'ephemeral_ttl_mode': '',
                '__user': self.user_id,
                '__a': '1',
                '__req': '1b',
                '__rev': '1015919737',
                'fb_dtsg': self.fb_dtsg
            }
            if id_tag:
                if name_tag:
                    name_clean = name_tag[1:] if name_tag.startswith('@') else name_tag
                else:
                    name_clean = "người dùng"
                lower_msg = message.lower()
                lower_name = name_clean.lower()
                pos = lower_msg.find(lower_name)
                if pos == -1:
                    pos = len(message)
                data.update({
                    'profile_xmd[0][offset]': str(pos),
                    'profile_xmd[0][length]': str(len(name_clean)),
                    'profile_xmd[0][id]': str(id_tag),
                    'profile_xmd[0][type]': 'p'
                })

            headers = {
                'Cookie': self.cookie,
                'User-Agent': self.user_agent,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://www.facebook.com',
                'Referer': f'https://www.facebook.com/messages/t/{recipient_id}',
                'Host': 'www.facebook.com'
            }
            try:
                resp = requests.post('https://www.facebook.com/messaging/send/', data=data, headers=headers, timeout=15)
                if resp.status_code != 200:
                    continue
                if 'for (;;);' in resp.text:
                    clean = resp.text.replace('for (;;);', '')
                    try:
                        result = json.loads(clean)
                        if result.get('error') and str(result.get('error')) != "0":
                            self.refresh_fb_dtsg()
                            data['fb_dtsg'] = self.fb_dtsg
                            continue
                        return {'success': True}
                    except:
                        pass
                return {'success': True}
            except Exception as e:
                print(f"[!] Lỗi gửi lần {attempt+1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt+1))
        return {'success': False, 'error_description': 'Gửi thất bại sau nhiều lần thử'}

# ====================== TASK ======================
class Task:
    def __init__(self, tid, messenger, recipient_id, messages, delay, tag_uid=None, tag_name=None):
        self.tid = tid
        self.messenger = messenger
        self.recipient_id = recipient_id
        self.messages = messages
        self.delay = delay
        self.tag_uid = tag_uid
        self.tag_name = tag_name
        self.running = True
        self.message_count = 0
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        while self.running:
            msg = random.choice(self.messages)
            if self.tag_uid:
                if self.tag_name:
                    full_msg = msg + f" @{self.tag_name}"
                else:
                    full_msg = msg + f" @UID_{self.tag_uid}"
                result = self.messenger.gui_tn(
                    self.recipient_id,
                    full_msg,
                    id_tag=self.tag_uid,
                    name_tag=self.tag_name if self.tag_name else "người dùng"
                )
            else:
                result = self.messenger.gui_tn(self.recipient_id, msg)

            if result.get('success'):
                self.message_count += 1
                print(f"[+] Gửi thành công tới {self.recipient_id}")
            else:
                print(f"[-] Lỗi: {result.get('error_description')}")
            time.sleep(self.delay)

    @property
    def user_id(self):
        return self.messenger.user_id

# ====================== HTML ======================
HTML = r"""
<!DOCTYPE html>
<html lang="vi">
<head><meta charset="UTF-8"><title>Auto Nhây + Tag</title>
<style>
body { font-family: 'Segoe UI', Arial; background: url('https://www.icegif.com/wp-content/uploads/2022/11/icegif-317.gif') no-repeat center center fixed; background-size: cover; color: #e6edf3; padding: 20px; margin: 0; min-height: 100vh; }
.overlay { background: rgba(13, 17, 23, 0.85); min-height: 100vh; padding: 20px; }
.card { background: rgba(22, 27, 34, 0.95); border: 1px solid #00ffff; border-radius: 20px; padding: 30px; max-width: 700px; margin: 0 auto; backdrop-filter: blur(10px); box-shadow: 0 0 30px rgba(0, 255, 255, 0.3); animation: fadeInUp 0.8s ease; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
h1 { color: #00ffff; text-align: center; text-shadow: 0 0 20px #00ffff; margin-bottom: 25px; font-size: 2.2em; }
label { color: #00ffff; display: block; margin-top: 20px; font-weight: 600; font-size: 1.1em; }
textarea, input { width: 100%; padding: 15px; border-radius: 12px; border: 2px solid #00ffff; background: rgba(13, 17, 23, 0.8); color: white; font-size: 1em; transition: all 0.3s ease; box-sizing: border-box; }
textarea:focus, input:focus { border-color: #00ff88; box-shadow: 0 0 15px rgba(0, 255, 136, 0.5); outline: none; transform: scale(1.02); }
button { background: linear-gradient(135deg, #00ffff, #00ff88); color: #0d1117; padding: 16px 30px; border: none; border-radius: 15px; cursor: pointer; margin-top: 25px; width: 100%; font-weight: bold; font-size: 1.2em; transition: all 0.3s ease; }
button:hover { transform: translateY(-3px); box-shadow: 0 10px 25px rgba(0, 255, 255, 0.4); background: linear-gradient(135deg, #00ff88, #00ffff); }
.alert { margin-top: 15px; padding: 15px; border-radius: 12px; border: 1px solid; backdrop-filter: blur(5px); }
.alert-success { background: rgba(46, 160, 67, 0.2); color: #00ff88; border-color: #00ff88; }
.alert-error { background: rgba(248, 81, 73, 0.2); color: #ff4444; border-color: #ff4444; }
.alert-info { background: rgba(0, 150, 255, 0.2); color: #00aaff; border-color: #00aaff; }
table { margin-top: 40px; width: 100%; border-collapse: collapse; background: rgba(22, 27, 34, 0.95); border-radius: 15px; overflow: hidden; box-shadow: 0 0 20px rgba(0, 255, 255, 0.2); }
th, td { border: 1px solid #00ffff; padding: 15px; text-align: center; }
th { color: #00ffff; background: rgba(0, 255, 255, 0.1); font-weight: 600; }
td { background: rgba(13, 17, 23, 0.7); }
.status-running { color: #00ff88; font-weight: bold; text-shadow: 0 0 10px #00ff88; }
.status-stopped { color: #ff4444; font-weight: bold; text-shadow: 0 0 10px #ff4444; }
.action-btn { padding: 10px 18px; border: none; border-radius: 10px; color: white; cursor: pointer; font-weight: 600; transition: all 0.3s ease; margin: 2px; }
.btn-stop { background: linear-gradient(135deg, #ff4444, #ff6b6b); }
.btn-start { background: linear-gradient(135deg, #00ff88, #00cc66); }
.btn-delete { background: linear-gradient(135deg, #888888, #aaaaaa); }
.back-btn { display: inline-block; margin-top: 30px; background: linear-gradient(135deg, #00ffff, #0099ff); color: #0b0c10; text-decoration: none; padding: 14px 35px; border-radius: 15px; font-weight: bold; font-size: 1.1em; transition: all 0.3s ease; box-shadow: 0 5px 15px rgba(0, 255, 255, 0.3); }
.back-btn:hover { background: linear-gradient(135deg, #0099ff, #00ffff); transform: translateY(-3px) scale(1.05); }
.form-group { margin-bottom: 20px; }
.tag-hint { color: #ff9900; font-size: 0.9em; margin-top: 5px; }
</style>
</head>
<body>
<div class="overlay"><div class="card">
<h1>💬 Auto Nhây + Tag Messenger</h1>
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    {% for cat, msg in messages %}<div class="alert alert-{{cat}}">{{msg}}</div>{% endfor %}
  {% endif %}
{% endwith %}
<form method="POST" action="/nhaydz/add_task">
  <div class="form-group"><label>🔐 Cookie Facebook:</label><textarea name="cookie" rows="3" required></textarea></div>
  <div class="form-group"><label>👤 UID hoặc ID Box Chat:</label><input type="text" name="recipient_id" required></div>
  <div class="form-group"><label>🏷️ UID người cần tag (để trống nếu không):</label><input type="text" name="tag_uid" placeholder="VD: 1000xxxxxx"><div class="tag-hint">Dù không lấy được tên, tag vẫn hoạt động bằng UID.</div></div>
  <div class="form-group"><label>⏱ Delay (giây):</label><input type="number" name="delay" min="0.1" step="0.1" required></div>
  <button type="submit">🚀 Bắt Đầu</button>
</form>
</div>
<table>
<tr><th>ID</th><th>User</th><th>Box</th><th>Tag UID</th><th>Tin đã gửi</th><th>Delay</th><th>Trạng thái</th><th>Hành động</th></tr>
{% for tid, t in tasks.items() %}
<tr>
<td>{{tid}}</td><td>{{t.user_id}}</td><td>{{t.recipient_id}}</td><td>{{t.tag_uid if t.tag_uid else '-'}}</td>
<td>{{t.message_count}}</td><td>{{t.delay}}</td>
<td>{% if t.running %}<span class="status-running">🟢 Đang chạy</span>{% else %}<span class="status-stopped">🔴 Đã dừng</span>{% endif %}</td>
<td>
{% if t.running %}<a href="/nhaydz/stop/{{tid}}"><button class="action-btn btn-stop">🛑 Dừng</button></a>
{% else %}<a href="/nhaydz/start/{{tid}}"><button class="action-btn btn-start">▶️ Chạy</button></a>{% endif %}
<a href="/nhaydz/delete/{{tid}}"><button class="action-btn btn-delete">🗑️ Xóa</button></a>
</td>
</tr>
{% endfor %}
</table>
<div style="text-align:center;"><a href="/menu" class="back-btn">⬅️ Quay về Menu</a></div>
</div></body>
</html>
"""

# ====================== ROUTES ======================
@nhaydz_bp.route('/')
def index():
    return render_template_string(HTML, tasks=TASKS)

@nhaydz_bp.route('/add_task', methods=['POST'])
def add_task():
    global TASK_ID_COUNTER
    cookie = request.form['cookie'].strip()
    recipient_id = request.form['recipient_id'].strip()
    delay = float(request.form['delay'])
    tag_uid = request.form.get('tag_uid', '').strip()
    if tag_uid == '':
        tag_uid = None

    if not os.path.exists(NHAY_FILE):
        flash(f"❌ Không tìm thấy file '{NHAY_FILE}'!", "error")
        return redirect(url_for("nhaydz.index"))
    with open(NHAY_FILE, 'r', encoding='utf-8') as f:
        messages = [line.strip() for line in f if line.strip()]
    if not messages:
        flash("❌ File trống!", "error")
        return redirect(url_for("nhaydz.index"))

    try:
        messenger = Messenger(cookie)
    except Exception as e:
        flash(f"❌ Lỗi đăng nhập: {str(e)}", "error")
        return redirect(url_for("nhaydz.index"))

    tag_name = None
    if tag_uid:
        try:
            name = get_name_from_uid(tag_uid, cookie, messenger.fb_dtsg)
            if name:
                tag_name = name
                flash(f"✅ Đã tìm thấy tên: {tag_name}", "success")
            else:
                flash(f"⚠️ Không lấy được tên cho UID {tag_uid} (có thể bị ẩn hoặc không tồn tại), nhưng vẫn tag bằng UID.", "info")
                tag_name = None
        except Exception as e:
            flash(f"⚠️ Lỗi lấy tên: {e}, vẫn tag bằng UID.", "info")
            tag_name = None
    else:
        flash("ℹ️ Không tag.", "info")

    tid = str(TASK_ID_COUNTER)
    TASK_ID_COUNTER += 1
    task = Task(tid, messenger, recipient_id, messages, delay, tag_uid, tag_name)
    TASKS[tid] = task
    flash(f"✅ Bắt đầu nhây {recipient_id} (delay {delay}s, {len(messages)} câu)", "success")
    return redirect(url_for("nhaydz.index"))

@nhaydz_bp.route('/stop/<tid>')
def stop_task(tid):
    if tid in TASKS:
        TASKS[tid].running = False
        flash(f"🛑 Dừng task #{tid}", "error")
    return redirect(url_for("nhaydz.index"))

@nhaydz_bp.route('/start/<tid>')
def start_task(tid):
    if tid in TASKS:
        t = TASKS[tid]
        if not t.running:
            t.running = True
            threading.Thread(target=t.run, daemon=True).start()
            flash(f"▶️ Tiếp tục task #{tid}", "success")
    return redirect(url_for("nhaydz.index"))

@nhaydz_bp.route('/delete/<tid>')
def delete_task(tid):
    if tid in TASKS:
        TASKS[tid].running = False
        del TASKS[tid]
        flash(f"🗑️ Đã xóa task #{tid}", "error")
    return redirect(url_for("nhaydz.index"))
