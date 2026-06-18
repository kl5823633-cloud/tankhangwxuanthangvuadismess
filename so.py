from flask import Blueprint, render_template_string, request, redirect, url_for, flash
import threading, time, requests, re, random, os

# ======== BLUEPRINT ========
so_bp = Blueprint("so", __name__, url_prefix="/so")

TASKS = {}
TASK_ID_COUNTER = 1
SO_FILE = "so.txt"

# ====================== HTML GIAO DIỆN ======================
HTML = r"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Messenger - Gửi Sớ Liên Tục</title>
    <style>
        body { 
            font-family: 'Segoe UI', Arial; 
            background: url('https://i0.wp.com/giffiles.alphacoders.com/132/13250.gif') no-repeat center center fixed;
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
            border: 1px solid #00ff88; 
            border-radius: 20px; 
            padding: 30px; 
            max-width: 800px; 
            margin: 0 auto;
            backdrop-filter: blur(10px);
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.3);
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
            color: #00ff88; 
            text-align: center; 
            text-shadow: 0 0 20px #00ff88;
            margin-bottom: 25px;
            font-size: 2.2em;
        }
        label { 
            color: #00ff88; 
            display: block; 
            margin-top: 20px;
            font-weight: 600;
            font-size: 1.1em;
        }
        textarea, input {
            width: 100%; 
            padding: 15px; 
            border-radius: 12px;
            border: 2px solid #00ff88; 
            background: rgba(13, 17, 23, 0.8); 
            color: white;
            font-size: 1em;
            transition: all 0.3s ease;
            box-sizing: border-box;
        }
        textarea:focus, input:focus {
            border-color: #00ffff;
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
            outline: none;
            transform: scale(1.02);
        }
        button {
            background: linear-gradient(135deg, #00ff88, #00ffff);
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
            box-shadow: 0 10px 25px rgba(0, 255, 136, 0.4);
            background: linear-gradient(135deg, #00ffff, #00ff88);
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
        table { 
            margin-top: 40px; 
            width: 100%; 
            border-collapse: collapse; 
            background: rgba(22, 27, 34, 0.95);
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
            backdrop-filter: blur(10px);
        }
        th, td { 
            border: 1px solid #00ff88; 
            padding: 15px; 
            text-align: center; 
        }
        th { 
            color: #00ff88; 
            background: rgba(0, 255, 136, 0.1);
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
            background: linear-gradient(135deg, #00ff88, #00ffff);
            color: #0b0c10; 
            text-decoration: none; 
            padding: 14px 35px; 
            border-radius: 15px; 
            font-weight: bold;
            font-size: 1.1em;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(0, 255, 136, 0.3);
        }
        .back-btn:hover { 
            background: linear-gradient(135deg, #00ffff, #00ff88);
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 10px 25px rgba(0, 255, 136, 0.5);
        }
        .form-group {
            margin-bottom: 20px;
        }
        ::placeholder {
            color: #888;
            opacity: 0.7;
        }
        .info-text {
            color: #00ffff;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .progress-bar {
            width: 100%;
            height: 10px;
            background: rgba(13, 17, 23, 0.8);
            border-radius: 5px;
            overflow: hidden;
            margin-top: 5px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff88, #00ffff);
            border-radius: 5px;
            transition: width 0.3s ease;
        }
        .file-info {
            background: rgba(0, 255, 136, 0.1);
            padding: 10px;
            border-radius: 8px;
            margin-top: 10px;
            border: 1px solid #00ff88;
        }
        .loop-count {
            color: #00ffff;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="overlay">
        <div class="card">
            <h1>🔄 Gửi Sớ Liên Tục</h1>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for cat, msg in messages %}
                        <div class="alert alert-{{cat}}">{{msg}}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="file-info">
                <strong>📁 File so.txt:</strong> 
                {% if file_exists %}
                    <span style="color: #00ff88;">✅ Tồn tại ({{ thread_count }} tin nhắn)</span>
                {% else %}
                    <span style="color: #ff4444;">❌ Không tồn tại</span>
                {% endif %}
                <br>
                <strong>💬 Chế độ:</strong> Gửi liên tục lặp lại không dừng
            </div>

            <form method="POST" action="/so/add_task">
                <div class="form-group">
                    <label>🔐 Cookie Facebook:</label>
                    <textarea name="cookie" placeholder="Nhập cookie Facebook tại đây..." rows="3" required></textarea>
                </div>

                <div class="form-group">
                    <label>👥 UID Box Chat:</label>
                    <input type="text" name="box_id" placeholder="Nhập UID box chat..." required>
                    <div class="info-text">💡 UID của box chat muốn gửi sớ</div>
                </div>

                <div class="form-group">
                    <label>⏱ Delay giữa mỗi tin nhắn (giây):</label>
                    <input type="number" name="delay" placeholder="VD: 2" min="0.5" step="0.1" value="2" required>
                    <div class="info-text">💡 Thời gian chờ giữa mỗi tin nhắn</div>
                </div>

                <button type="submit" {% if not file_exists %}disabled style="opacity: 0.6;"{% endif %}>
                    {% if file_exists %}
                        🔄 Bắt đầu gửi liên tục
                    {% else %}
                        ❌ File so.txt không tồn tại
                    {% endif %}
                </button>
            </form>
        </div>

        <table>
            <tr>
                <th>ID</th>
                <th>User</th>
                <th>Box Chat</th>
                <th>Đã gửi</th>
                <th>Vòng lặp</th>
                <th>Delay (s)</th>
                <th>Trạng thái</th>
                <th>Hành động</th>
            </tr>
            {% for tid, t in tasks.items() %}
            <tr>
                <td>{{tid}}</td>
                <td>{{t.user_id}}</td>
                <td>{{t.box_id}}</td>
                <td>{{t.total_sent}}</td>
                <td class="loop-count">{{t.loop_count}}</td>
                <td>{{t.delay}}</td>
                <td>
                    {% if t.running %}
                        <span class="status-running">🔄 Đang gửi liên tục</span>
                    {% else %}
                        <span class="status-stopped">🔴 Đã dừng</span>
                    {% endif %}
                </td>
                <td>
                    {% if t.running %}
                        <a href="/so/stop/{{tid}}"><button class="action-btn btn-stop">🛑 Dừng</button></a>
                    {% else %}
                        <a href="/so/start/{{tid}}"><button class="action-btn btn-start">▶️ Tiếp tục</button></a>
                    {% endif %}
                    <a href="/so/delete/{{tid}}"><button class="action-btn btn-delete">🗑️ Xóa</button></a>
                </td>
            </tr>
            {% if t.running %}
            <tr>
                <td colspan="8">
                    <div style="text-align: center; color: #00ffff; font-size: 0.9em; margin-top: 5px;">
                        📊 Đang gửi: {{t.total_sent}} tin nhắn • Vòng lặp: {{t.loop_count}} • Tin hiện tại: "{{t.current_message}}"
                    </div>
                </td>
            </tr>
            {% endif %}
            {% endfor %}
        </table>

        <!-- Nút quay về menu chính -->
        <div style="text-align:center;">
            <a href="/menu" class="back-btn">⬅️ Quay về Menu Chính</a>
        </div>
    </div>
</body>
</html>
"""

# ====================== LỚP MESSENGER ======================
class Messenger:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.get_user_id()
        self.fb_dtsg = None
        self.init_params()

    def get_user_id(self):
        try:
            return re.search(r"c_user=(\d+)", self.cookie).group(1)
        except:
            raise Exception("Cookie không hợp lệ")

    def init_params(self):
        headers = {'Cookie': self.cookie, 'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get('https://m.facebook.com', headers=headers)
            match = re.search(r'name="fb_dtsg" value="(.*?)"', response.text)
            if match:
                self.fb_dtsg = match.group(1)
            else:
                raise Exception("Không tìm thấy fb_dtsg")
        except Exception as e:
            raise Exception(f"Lỗi khởi tạo: {str(e)}")

    def send_message(self, recipient_id, message):
        timestamp = int(time.time() * 1000)
        data = {
            'fb_dtsg': self.fb_dtsg,
            '__user': self.user_id,
            'body': message,
            'action_type': 'ma-type:user-generated-message',
            'timestamp': timestamp,
            'offline_threading_id': str(timestamp),
            'message_id': str(timestamp),
            'thread_fbid': recipient_id,
            'source': 'source:chat:web',
            'client': 'mercury'
        }
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            r = requests.post('https://www.facebook.com/messaging/send/', data=data, headers=headers)
            return r.status_code == 200
        except:
            return False

# ====================== TASK LIÊN TỤC ======================
class Task:
    def __init__(self, tid, messenger, box_id, messages, delay):
        self.tid = tid
        self.messenger = messenger
        self.box_id = box_id
        self.messages = messages
        self.delay = delay
        self.running = True
        self.total_sent = 0
        self.loop_count = 0
        self.current_message = ""
        threading.Thread(target=self.run_continuous, daemon=True).start()

    def run_continuous(self):
        print(f"[🚀] Bắt đầu gửi sớ LIÊN TỤC đến box {self.box_id}...")
        
        while self.running:
            self.loop_count += 1
            print(f"[🔄] Bắt đầu vòng lặp thứ {self.loop_count}")
            
            for i, message in enumerate(self.messages):
                if not self.running:
                    print(f"[⏹️] Dừng gửi sớ task {self.tid}")
                    return
                
                self.current_message = message
                print(f"[📨] Đang gửi tin {i+1}/{len(self.messages)} (Vòng {self.loop_count}): {message[:50]}...")
                
                if self.messenger.send_message(self.box_id, message):
                    self.total_sent += 1
                    print(f"[✅] Đã gửi thành công tin {i+1}/{len(self.messages)} (Tổng: {self.total_sent})")
                else:
                    print(f"[❌] Gửi thất bại tin {i+1}/{len(self.messages)}")
                
                # Chờ giữa các tin nhắn (trừ tin cuối của vòng lặp)
                if i < len(self.messages) - 1 and self.running:
                    time.sleep(self.delay)
            
            print(f"[🎯] Hoàn thành vòng lặp {self.loop_count}. Tổng tin đã gửi: {self.total_sent}")
            
            # Chờ một chút trước khi bắt đầu vòng lặp mới
            if self.running:
                time.sleep(1)
        
        print(f"[🛑] Đã dừng gửi sớ task {self.tid}. Tổng: {self.total_sent} tin")

    @property
    def user_id(self):
        return self.messenger.user_id

def load_messages_from_file():
    """Đọc danh sách tin nhắn từ file so.txt"""
    if not os.path.exists(SO_FILE):
        return []
    
    try:
        with open(SO_FILE, 'r', encoding='utf-8') as f:
            messages = [line.strip() for line in f if line.strip()]
        return messages
    except Exception as e:
        print(f"[!] Lỗi đọc file {SO_FILE}: {e}")
        return []

# ====================== ROUTES ======================
@so_bp.route('/')
def index():
    file_exists = os.path.exists(SO_FILE)
    messages = load_messages_from_file() if file_exists else []
    message_count = len(messages)
    
    return render_template_string(HTML, tasks=TASKS, file_exists=file_exists, thread_count=message_count)

@so_bp.route('/add_task', methods=['POST'])
def add_task():
    global TASK_ID_COUNTER
    
    # Kiểm tra file so.txt
    if not os.path.exists(SO_FILE):
        flash("error", f"❌ File '{SO_FILE}' không tồn tại!")
        return redirect(url_for("so.index"))
    
    # Đọc tin nhắn từ file
    messages = load_messages_from_file()
    if not messages:
        flash("error", f"❌ File '{SO_FILE}' trống hoặc không có tin nhắn hợp lệ!")
        return redirect(url_for("so.index"))
    
    cookie = request.form['cookie'].strip()
    box_id = request.form['box_id'].strip()
    delay = float(request.form['delay'])

    if not box_id:
        flash("error", "❌ Vui lòng nhập UID box chat!")
        return redirect(url_for("so.index"))

    try:
        messenger = Messenger(cookie)
    except Exception as e:
        flash("error", f"❌ {str(e)}")
        return redirect(url_for("so.index"))

    tid = str(TASK_ID_COUNTER)
    TASK_ID_COUNTER += 1
    TASKS[tid] = Task(tid, messenger, box_id, messages, delay)
    flash("success", f"🔄 Đã bắt đầu gửi sớ LIÊN TỤC {len(messages)} tin nhắn đến box {box_id}")
    return redirect(url_for("so.index"))

@so_bp.route('/stop/<tid>')
def stop_task(tid):
    if tid in TASKS:
        TASKS[tid].running = False
        flash("error", f"🛑 Dừng gửi sớ #{tid}")
    return redirect(url_for("so.index"))

@so_bp.route('/start/<tid>')
def start_task(tid):
    if tid in TASKS:
        t = TASKS[tid]
        if not t.running:
            t.running = True
            threading.Thread(target=t.run_continuous, daemon=True).start()
            flash("success", f"▶️ Tiếp tục gửi sớ LIÊN TỤC #{tid}")
    return redirect(url_for("so.index"))

@so_bp.route('/delete/<tid>')
def delete_task(tid):
    if tid in TASKS:
        TASKS[tid].running = False
        del TASKS[tid]
        flash("error", f"🗑️ Đã xóa task #{tid}")
    return redirect(url_for("so.index"))
