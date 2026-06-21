from flask import Blueprint, render_template_string, request, redirect, url_for, flash
import threading, time, requests, re, random, os, json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ======== BLUEPRINT ========
nhaydz_bp = Blueprint("nhaydz", __name__, url_prefix="/nhaydz")

TASKS = {}
TASK_ID_COUNTER = 1
NHAY_FILE = "nhay.txt"

# ------------------- USER AGENTS (lấy từ mess.py) -------------------
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 11; RMX2185) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.140 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.68 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; V2031) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.60 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; CPH2481) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.86 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

# ====================== SESSION VỚI RETRY ======================
def get_session_with_retries():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session

# ====================== HÀM LẤY TÊN BẰNG API (từ mess.py) ======================
def get_name_from_uid(uid, cookie, fb_dtsg, a="1", req="1b", rev="1015919737"):
    """
    Lấy tên hiển thị của UID thông qua API chat/user_info/
    Trả về tên hoặc None nếu lỗi.
    """
    try:
        form = {
            f"ids[0]": uid,
            "fb_dtsg": fb_dtsg,
            "__a": a,
            "__req": req,
            "__rev": rev
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Origin': 'https://www.facebook.com',
            'Referer': 'https://www.facebook.com/',
            'User-Agent': random.choice(USER_AGENTS)
        }
        resp = requests.post("https://www.facebook.com/chat/user_info/", headers=headers, data=form, timeout=10)
        text = resp.text
        if text.startswith("for (;;);"):
            text = text[9:]
        data = json.loads(text)
        profile = data.get("payload", {}).get("profiles", {}).get(uid)
        if profile:
            name = profile.get("name")
            if name:
                return name
        return None
    except Exception as e:
        print(f"[!] Lỗi get_name_from_uid: {e}")
        return None

# ====================== LỚP MESSENGER (dựa trên mess.py) ======================
class Messenger:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.extract_user_id()
        self.user_agent = random.choice(USER_AGENTS)
        self.fb_dtsg = None
        self.name = ""
        self.init_params()

    def extract_user_id(self):
        match = re.search(r"c_user=(\d+)", self.cookie)
        if not match:
            raise Exception("Cookie không có c_user")
        return match.group(1)

    def init_params(self):
        headers = {'Cookie': self.cookie, 'User-Agent': self.user_agent}
        try:
            resp = requests.get('https://mbasic.facebook.com/me', headers=headers, timeout=10)
            name_match = re.search(r'<title>(.*?)</title>', resp.text)
            if name_match:
                self.name = name_match.group(1).replace(" | Facebook", "").strip()
            fb_dtsg_match = re.search(r'name="fb_dtsg" value="(.*?)"', resp.text)
            if fb_dtsg_match:
                self.fb_dtsg = fb_dtsg_match.group(1)
            else:
                raise Exception("Không thể lấy fb_dtsg từ mbasic")
        except Exception as e:
            # Fallback: thử www.facebook.com
            try:
                resp2 = requests.get('https://www.facebook.com/', headers=headers, timeout=10)
                fb_dtsg_match2 = re.search(r'name="fb_dtsg" value="(.*?)"', resp2.text)
                if fb_dtsg_match2:
                    self.fb_dtsg = fb_dtsg_match2.group(1)
                    # Lấy tên từ profile
                    prof = requests.get('https://www.facebook.com/me', headers=headers, timeout=10)
                    name_match2 = re.search(r'<title>(.*?)</title>', prof.text)
                    if name_match2:
                        self.name = name_match2.group(1).replace(" | Facebook", "").strip()
                else:
                    raise Exception("Không thể lấy fb_dtsg từ cả mbasic và www")
            except Exception as e2:
                raise Exception(f"Lỗi khởi tạo Messenger: {e2}")

    def refresh_fb_dtsg(self):
        try:
            self.init_params()
            print(f"[!] Làm mới fb_dtsg cho {self.name} ({self.user_id})")
        except Exception as e:
            print(f"[!] Làm mới thất bại: {e}")

    def gui_tn(self, recipient_id, message, id_tag=None, name_tag=None, max_retries=3):
        for attempt in range(max_retries):
            timestamp = int(time.time() * 1000)
            offline_threading_id = str(timestamp)
            message_id = str(timestamp)

            data = {
                'thread_fbid': recipient_id,
                'action_type': 'ma-type:user-generated-message',
                'body': message,
                'client': 'mercury',
                'author': f'fbid:{self.user_id}',
                'timestamp': timestamp,
                'source': 'source:chat:web',
                'offline_threading_id': offline_threading_id,
                'message_id': message_id,
                'ephemeral_ttl_mode': '',
                '__user': self.user_id,
                '__a': '1',
                '__req': '1b',
                '__rev': '1015919737',
                'fb_dtsg': self.fb_dtsg
            }

            if id_tag and name_tag:
                # Tìm vị trí tag trong message (có thể đã có @tên)
                if name_tag.startswith('@'):
                    name_clean = name_tag[1:]
                else:
                    name_clean = name_tag
                lower_msg = message.lower()
                lower_name = name_clean.lower()
                pos = lower_msg.find(lower_name)
                if pos != -1:
                    data.update({
                        'profile_xmd[0][offset]': str(pos),
                        'profile_xmd[0][length]': str(len(name_clean)),
                        'profile_xmd[0][id]': str(id_tag),
                        'profile_xmd[0][type]': 'p'
                    })

            headers = {
                'Cookie': self.cookie,
                'User-Agent': self.user_agent,
                'Accept': '*/*',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://www.facebook.com',
                'Referer': f'https://www.facebook.com/messages/t/{recipient_id}',
                'Host': 'www.facebook.com',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty'
            }

            try:
                resp = requests.post('https://www.facebook.com/messaging/send/', data=data, headers=headers, timeout=15)
                if resp.status_code != 200:
                    continue

                if 'for (;;);' in resp.text:
                    clean_text = resp.text.replace('for (;;);', '')
                    try:
                        result = json.loads(clean_text)
                        if result.get('error') and str(result.get('error')) != "0":
                            self.refresh_fb_dtsg()
                            data['fb_dtsg'] = self.fb_dtsg
                            continue
                        return {'success': True}
                    except:
                        pass
                return {'success': True}
            except Exception as e:
                print(f"[!] Lần {attempt+1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt+1))
        return {'success': False, 'error_description': 'Gửi thất bại sau nhiều lần thử'}

# ====================== TASK (giữ nguyên) ======================
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
            if self.tag_uid and self.tag_name:
                full_msg = msg + f" @{self.tag_name}"
                result = self.messenger.gui_tn(
                    self.recipient_id,
                    full_msg,
                    id_tag=self.tag_uid,
                    name_tag=f"@{self.tag_name}"
                )
            else:
                result = self.messenger.gui_tn(self.recipient_id, msg)

            if result.get('success'):
                self.message_count += 1
                print(f"[+] Đã gửi tới {self.recipient_id}")
            else:
                print(f"[-] Lỗi: {result.get('error_description')}")
            time.sleep(self.delay)

    @property
    def user_id(self):
        return self.messenger.user_id

# ====================== HTML (giữ nguyên) ======================
HTML = r"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Auto Nhây + Tag</title>
    <style>
        body { 
            font-family: 'Segoe UI', Arial; 
            background: url('https://www.icegif.com/wp-content/uploads/2022/11/icegif-317.gif') no-repeat center center fixed;
            background-size: cover;
            color: #e6edf3; 
            padding: 20px;
            margin: 0;
            min-height: 100vh;
        }
        .overlay {
            background: rgba(13, 17, 23, 0.85);
            min-height: 100vh;
            padding: 20px;
        }
        .card {
            background: rgba(22, 27, 34, 0.95); 
            border: 1px solid #00ffff; 
            border-radius: 20px; 
            padding: 30px; 
            max-width: 700px; 
            margin: 0 auto;
            backdrop-filter: blur(10px);
            box-shadow: 0 0 30px rgba(0, 255, 255, 0.3);
            animation: fadeInUp 0.8s ease;
        }
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        h1 { 
            color: #00ffff; 
            text-align: center; 
            text-shadow: 0 0 20px #00ffff;
            margin-bottom: 25px;
            font-size: 2.2em;
        }
        label { 
            color: #00ffff; 
            display: block; 
            margin-top: 20px;
            font-weight: 600;
            font-size: 1.1em;
        }
        textarea, input {
            width: 100%; 
            padding: 15px; 
            border-radius: 12px;
            border: 2px solid #00ffff; 
            background: rgba(13, 17, 23, 0.8); 
            color: white;
            font-size: 1em;
            transition: all 0.3s ease;
            box-sizing: border-box;
        }
        textarea:focus, input:focus {
            border-color: #00ff88;
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.5);
            outline: none;
            transform: scale(1.02);
        }
        button {
            background: linear-gradient(135deg, #00ffff, #00ff88);
            color: #0d1117; 
            padding: 16px 30px;
            border: none; 
            border-radius: 15px; 
            cursor: pointer; 
            margin-top: 25px; 
            width: 100%;
            font-weight: bold;
            font-size: 1.2em;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        button:hover { 
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0, 255, 255, 0.4);
            background: linear-gradient(135deg, #00ff88, #00ffff);
        }
        button:active {
            transform: translateY(0);
        }
        .alert { 
            margin-top: 15px; 
            padding: 15px; 
            border-radius: 12px; 
            border: 1px solid;
            backdrop-filter: blur(5px);
        }
        .alert-success { 
            background: rgba(46, 160, 67, 0.2); 
            color: #00ff88;
            border-color: #00ff88;
        }
        .alert-error { 
            background: rgba(248, 81, 73, 0.2); 
            color: #ff4444;
            border-color: #ff4444;
        }
        .alert-info {
            background: rgba(0, 150, 255, 0.2);
            color: #00aaff;
            border-color: #00aaff;
        }
        table { 
            margin-top: 40px; 
            width: 100%; 
            border-collapse: collapse; 
            background: rgba(22, 27, 34, 0.95);
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
            backdrop-filter: blur(10px);
        }
        th, td { 
            border: 1px solid #00ffff; 
            padding: 15px; 
            text-align: center; 
        }
        th { 
            color: #00ffff; 
            background: rgba(0, 255, 255, 0.1);
            font-weight: 600;
        }
        td {
            background: rgba(13, 17, 23, 0.7);
        }
        .status-running { 
            color: #00ff88; 
            font-weight: bold;
            text-shadow: 0 0 10px #00ff88;
        }
        .status-stopped { 
            color: #ff4444; 
            font-weight: bold;
            text-shadow: 0 0 10px #ff4444;
        }
        .action-btn { 
            padding: 10px 18px; 
            border: none; 
            border-radius: 10px; 
            color: white; 
            cursor: pointer; 
            font-weight: 600;
            transition: all 0.3s ease;
            margin: 2px;
        }
        .btn-stop { 
            background: linear-gradient(135deg, #ff4444, #ff6b6b);
        }
        .btn-stop:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 68, 68, 0.4);
        }
        .btn-start { 
            background: linear-gradient(135deg, #00ff88, #00cc66);
        }
        .btn-start:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 255, 136, 0.4);
        }
        .btn-delete { 
            background: linear-gradient(135deg, #888888, #aaaaaa);
        }
        .btn-delete:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(136, 136, 136, 0.4);
        }
        .back-btn {
            display: inline-block; 
            margin-top: 30px; 
            background: linear-gradient(135deg, #00ffff, #0099ff);
            color: #0b0c10; 
            text-decoration: none; 
            padding: 14px 35px; 
            border-radius: 15px; 
            font-weight: bold;
            font-size: 1.1em;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(0, 255, 255, 0.3);
        }
        .back-btn:hover { 
            background: linear-gradient(135deg, #0099ff, #00ffff);
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 10px 25px rgba(0, 255, 255, 0.5);
        }
        .form-group {
            margin-bottom: 20px;
        }
        ::placeholder {
            color: #888;
            opacity: 0.7;
        }
        .tag-hint {
            color: #ff9900;
            font-size: 0.9em;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="overlay">
        <div class="card">
            <h1>💬 Auto Nhây + Tag Messenger</h1>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for cat, msg in messages %}
                        <div class="alert alert-{{cat}}">{{msg}}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST" action="/nhaydz/add_task">
                <div class="form-group">
                    <label>🔐 Cookie Facebook:</label>
                    <textarea name="cookie" placeholder="Paste cookie ở đây..." rows="3" required></textarea>
                </div>
                <div class="form-group">
                    <label>👤 UID hoặc ID Box Chat:</label>
                    <input type="text" name="recipient_id" placeholder="VD: 6155xxxx hoặc 7920xxxx" required>
                </div>
                <div class="form-group">
                    <label>🏷️ UID người cần tag (để trống nếu không tag):</label>
                    <input type="text" name="tag_uid" placeholder="Nhập ID người cần tag (ví dụ: 1000xxxxxx)">
                    <div class="tag-hint">Nếu có tag, tin nhắn sẽ tự động thêm @Tên và tag đúng người.</div>
                </div>
                <div class="form-group">
                    <label>⏱ Delay giữa mỗi tin (giây):</label>
                    <input type="number" name="delay" placeholder="VD: 3" min="0.1" step="0.1" required>
                </div>
                <button type="submit">🚀 Bắt Đầu Nhây</button>
            </form>
        </div>

        <table>
            <tr>
                <th>ID</th>
                <th>User</th>
                <th>Box</th>
                <th>Tag UID</th>
                <th>Tin đã gửi</th>
                <th>Delay (s)</th>
                <th>Trạng thái</th>
                <th>Hành động</th>
            </tr>
            {% for tid, t in tasks.items() %}
            <tr>
                <td>{{tid}}</td>
                <td>{{t.user_id}}</td>
                <td>{{t.recipient_id}}</td>
                <td>{{t.tag_uid if t.tag_uid else '-'}}</td>
                <td>{{t.message_count}}</td>
                <td>{{t.delay}}</td>
                <td>
                    {% if t.running %}
                        <span class="status-running">🟢 Đang chạy</span>
                    {% else %}
                        <span class="status-stopped">🔴 Đã dừng</span>
                    {% endif %}
                </td>
                <td>
                    {% if t.running %}
                        <a href="/nhaydz/stop/{{tid}}"><button class="action-btn btn-stop">🛑 Dừng</button></a>
                    {% else %}
                        <a href="/nhaydz/start/{{tid}}"><button class="action-btn btn-start">▶️ Chạy</button></a>
                    {% endif %}
                    <a href="/nhaydz/delete/{{tid}}"><button class="action-btn btn-delete">🗑️ Xóa</button></a>
                </td>
            </tr>
            {% endfor %}
        </table>

        <div style="text-align:center;">
            <a href="/menu" class="back-btn">⬅️ Quay về Menu Chính</a>
        </div>
    </div>
</body>
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
        flash(f"❌ File '{NHAY_FILE}' trống!", "error")
        return redirect(url_for("nhaydz.index"))

    # Khởi tạo messenger
    try:
        messenger = Messenger(cookie)
    except Exception as e:
        flash(f"❌ Lỗi đăng nhập: {str(e)}", "error")
        return redirect(url_for("nhaydz.index"))

    # Xử lý tag – sử dụng API lấy tên
    tag_name = None
    if tag_uid:
        try:
            # Lấy tên từ API, cần fb_dtsg của messenger
            name = get_name_from_uid(tag_uid, cookie, messenger.fb_dtsg)
            if name:
                tag_name = name
                flash(f"✅ Đã tìm thấy tên: {tag_name}", "success")
            else:
                flash(f"⚠️ Không lấy được tên cho UID {tag_uid}. Bỏ qua tag.", "error")
                tag_uid = None
        except Exception as e:
            flash(f"⚠️ Lỗi khi lấy tên: {str(e)}. Bỏ qua tag.", "error")
            tag_uid = None
    else:
        flash("ℹ️ Không tag, chỉ gửi tin nhắn bình thường.", "info")

    tid = str(TASK_ID_COUNTER)
    TASK_ID_COUNTER += 1
    task = Task(tid, messenger, recipient_id, messages, delay, tag_uid, tag_name)
    TASKS[tid] = task
    flash(f"✅ Đã bắt đầu nhây UID {recipient_id} (delay {delay}s, {len(messages)} câu) với tag {tag_uid if tag_uid else 'không'}", "success")
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
