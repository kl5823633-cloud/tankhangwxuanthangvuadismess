from flask import Blueprint, render_template_string, request, redirect, url_for, session
import threading, time, requests, re

treongo_bp = Blueprint("treongo", __name__, url_prefix="/treongo")

TASKS = {}  # Danh sách task đang chạy

# ====================== HTML GIAO DIỆN TOOL ======================
HTML = r"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Messenger - Treo Ngôn</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial;
            background: #0d1117 url('https://www.icegif.com/wp-content/uploads/2022/11/icegif-317.gif') center/cover fixed;
            color: #e6edf3;
            padding: 20px;
            min-height: 100vh;
            position: relative;
        }
        
        body::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(13, 17, 23, 0.85);
            z-index: -1;
        }
        
        .card {
            background: rgba(22, 27, 34, 0.9);
            border: 1px solid #30363d;
            border-radius: 16px;
            padding: 25px;
            max-width: 700px;
            margin: 0 auto;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
        }
        
        h1 {
            color: #58a6ff;
            text-align: center;
            margin-bottom: 20px;
            font-size: 2rem;
            text-shadow: 0 0 10px rgba(88, 166, 255, 0.5);
        }
        
        label {
            color: #58a6ff;
            display: block;
            margin-top: 15px;
            font-weight: 600;
        }
        
        textarea, input {
            width: 100%;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid #30363d;
            background: rgba(13, 17, 23, 0.7);
            color: white;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        textarea:focus, input:focus {
            outline: none;
            border-color: #58a6ff;
            box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.2);
        }
        
        button {
            background: linear-gradient(135deg, #238636, #2ea043);
            color: white;
            padding: 14px 20px;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            margin-top: 20px;
            width: 100%;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(35, 134, 54, 0.3);
        }
        
        button:hover {
            background: linear-gradient(135deg, #2ea043, #3fb950);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(46, 160, 67, 0.4);
        }
        
        .alert {
            margin-top: 15px;
            padding: 12px;
            border-radius: 10px;
            font-weight: 500;
        }
        
        .alert-success {
            background: rgba(46, 160, 67, 0.2);
            color: #3fb950;
            border: 1px solid rgba(63, 185, 80, 0.3);
        }
        
        .alert-error {
            background: rgba(248, 81, 73, 0.2);
            color: #f85149;
            border: 1px solid rgba(248, 81, 73, 0.3);
        }
        
        table {
            margin-top: 30px;
            width: 100%;
            border-collapse: collapse;
            background: rgba(22, 27, 34, 0.9);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
        }
        
        th, td {
            border: 1px solid #30363d;
            padding: 12px;
            text-align: center;
        }
        
        th {
            color: #58a6ff;
            background: rgba(13, 17, 23, 0.7);
            font-weight: 600;
        }
        
        .status-running {
            color: #3fb950;
            font-weight: bold;
            text-shadow: 0 0 8px rgba(63, 185, 80, 0.5);
        }
        
        .status-stopped {
            color: #f85149;
            font-weight: bold;
        }
        
        .action-btn {
            padding: 8px 15px;
            border: none;
            border-radius: 8px;
            color: white;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s ease;
            margin: 2px;
        }
        
        .btn-stop {
            background: linear-gradient(135deg, #f85149, #da3633);
            box-shadow: 0 3px 10px rgba(248, 81, 73, 0.3);
        }
        
        .btn-stop:hover {
            background: linear-gradient(135deg, #da3633, #c92a2a);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(218, 54, 51, 0.4);
        }
        
        .btn-start {
            background: linear-gradient(135deg, #d29922, #e3b341);
            box-shadow: 0 3px 10px rgba(210, 153, 34, 0.3);
        }
        
        .btn-start:hover {
            background: linear-gradient(135deg, #e3b341, #f2cc60);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(227, 179, 65, 0.4);
        }
        
        .btn-delete {
            background: linear-gradient(135deg, #6e7681, #8b949e);
            box-shadow: 0 3px 10px rgba(110, 118, 129, 0.3);
        }
        
        .btn-delete:hover {
            background: linear-gradient(135deg, #8b949e, #a8b1bd);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(139, 148, 158, 0.4);
        }
        
        .back-btn {
            display: inline-block;
            margin-top: 25px;
            background: linear-gradient(135deg, #00ffff, #00b3b3);
            color: #0b0c10;
            text-decoration: none;
            padding: 12px 30px;
            border-radius: 12px;
            font-weight: bold;
            transition: all 0.3s ease;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 255, 255, 0.3);
        }
        
        .back-btn:hover {
            background: linear-gradient(135deg, #00d0d0, #008f8f);
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 6px 20px rgba(0, 208, 208, 0.4);
        }
        
        .center {
            text-align: center;
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(63, 185, 80, 0.7);
            }
            70% {
                box-shadow: 0 0 0 10px rgba(63, 185, 80, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(63, 185, 80, 0);
            }
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>💬 Treo Ngôn Messenger</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for cat, msg in messages %}
                    <div class="alert alert-{{cat}}">{{msg}}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST" action="/treongo/add_task">
            <label>Cookie Facebook:</label>
            <textarea name="cookie" placeholder="Nhập cookie Facebook..." required rows="3"></textarea>

            <label>UID hoặc ID Box Chat:</label>
            <input type="text" name="recipient_id" placeholder="VD: 6155xxxx hoặc 7920xxxx" required>

            <label>Nội dung tin nhắn:</label>
            <textarea name="message" placeholder="Nhập nội dung tin nhắn..." required rows="3"></textarea>

            <label>⏱ Delay giữa mỗi tin (giây):</label>
            <input type="number" name="delay" placeholder="VD: 3" min="0.1" step="0.1" required>

            <button type="submit" class="pulse">🚀 Bắt đầu treo ngôn</button>
        </form>
    </div>

    <table>
        <tr>
            <th>ID</th><th>User</th><th>Box</th><th>Tin đã gửi</th><th>Delay (s)</th><th>Trạng thái</th><th>Hành động</th>
        </tr>
        {% for tid, t in tasks.items() %}
        <tr>
            <td>{{tid}}</td>
            <td>{{t.user_id}}</td>
            <td>{{t.recipient_id}}</td>
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
                    <a href="/treongo/stop/{{tid}}"><button class="action-btn btn-stop">🛑 Dừng</button></a>
                {% else %}
                    <a href="/treongo/start/{{tid}}"><button class="action-btn btn-start">▶️ Chạy</button></a>
                {% endif %}
                <a href="/treongo/delete/{{tid}}"><button class="action-btn btn-delete">🗑️ Xóa</button></a>
            </td>
        </tr>
        {% endfor %}
    </table>

    <!-- 🟢 Nút quay về menu chính -->
    <div class="center">
        <a href="/menu" class="back-btn">⬅️ Quay về Menu Chính</a>
    </div>

</body>
</html>
"""
# ====================== LỚP CHÍNH XỬ LÝ MESSENGER ======================
class Messenger:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.extract_user_id()
        self.fb_dtsg = self.get_fb_dtsg()
        self.valid = self.user_id is not None and self.fb_dtsg is not None

    def extract_user_id(self):
        match = re.search(r"c_user=(\d+)", self.cookie)
        if not match:
            print("[!] Cookie không hợp lệ (không có c_user)")
            return None
        return match.group(1)

    def get_fb_dtsg(self):
        try:
            headers = {'Cookie': self.cookie, 'User-Agent': 'Mozilla/5.0'}
            res = requests.get('https://mbasic.facebook.com/profile.php', headers=headers)
            if 'checkpoint' in res.url or 'login' in res.url:
                print(f"[!] Cookie checkpoint hoặc hết hạn: {self.user_id}")
                return None
            token = re.search(r'name="fb_dtsg" value="(.*?)"', res.text)
            if not token:
                print(f"[!] Không tìm thấy fb_dtsg: {self.user_id}")
                return None
            return token.group(1)
        except Exception as e:
            print(f"[!] Lỗi khi lấy fb_dtsg: {e}")
            return None

    def send_message(self, recipient_id, message):
        if not self.valid:
            print(f"[!] Bỏ qua vì tài khoản không hợp lệ: {self.user_id}")
            return False
        try:
            ts = int(time.time() * 1000)
            data = {
                'thread_fbid': recipient_id,
                'action_type': 'ma-type:user-generated-message',
                'body': message,
                'client': 'mercury',
                'author': f'fbid:{self.user_id}',
                'timestamp': ts,
                'source': 'source:chat:web',
                'offline_threading_id': str(ts),
                'message_id': str(ts),
                '__user': self.user_id,
                '__a': '1',
                'fb_dtsg': self.fb_dtsg
            }
            headers = {
                'Cookie': self.cookie,
                'User-Agent': 'python-http',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            res = requests.post('https://www.facebook.com/messaging/send/', data=data, headers=headers)
            if res.status_code != 200 or 'error' in res.text:
                print(f"[!] Lỗi gửi tới {recipient_id} bởi {self.user_id}: {res.text[:100]}")
                return False
            return True
        except Exception as e:
            print(f"[!] Exception gửi tới {recipient_id} bởi {self.user_id}: {e}")
            return False

# ====================== TASK (LUỒNG GỬI LIÊN TỤC) ======================
class Task:
    def __init__(self, task_id, messenger, recipient_id, message, delay):
        self.task_id = task_id
        self.messenger = messenger
        self.recipient_id = recipient_id
        self.message = message
        self.delay = delay
        self.start_time = time.time()
        self.running = True
        self.message_count = 0
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        while self.running:
            success = self.messenger.send_message(self.recipient_id, self.message)
            if success:
                self.message_count += 1
            time.sleep(self.delay)

    @property
    def user_id(self):
        return self.messenger.user_id

    @property
    def runtime(self):
        return round(time.time() - self.start_time, 1)

# ====================== ROUTES ======================
@treongo_bp.route('/')
def index():
    return render_template_string(HTML, tasks=TASKS)

@treongo_bp.route('/add_task', methods=['POST'])
def add_task():
    cookie = request.form['cookie']
    recipient_id = request.form['recipient_id']
    message = request.form['message']
    delay = float(request.form.get('delay', 5))

    try:
        messenger = Messenger(cookie)
        if not messenger.valid:
            return "Lỗi: Cookie không hợp lệ hoặc đã hết hạn!"
    except Exception as e:
        return f"Lỗi: {str(e)}"

    tid = str(len(TASKS) + 1)
    TASKS[tid] = Task(tid, messenger, recipient_id, message, delay)
    return redirect(url_for('treongo.index'))

@treongo_bp.route('/stop/<task_id>')
def stop_task(task_id):
    if task_id in TASKS:
        TASKS[task_id].running = False
    return redirect(url_for('treongo.index'))

@treongo_bp.route('/start/<task_id>')
def start_task(task_id):
    if task_id in TASKS:
        TASKS[task_id].running = True
    return redirect(url_for('treongo.index'))

@treongo_bp.route('/delete/<task_id>')
def delete_task(task_id):
    if task_id in TASKS:
        TASKS[task_id].running = False
        del TASKS[task_id]
    return redirect(url_for('treongo.index'))
