from flask import Blueprint, render_template_string, request, redirect, url_for, flash
import threading, time, requests, re, random, os

# ======== BLUEPRINT ========
rename_bp = Blueprint("rename", __name__, url_prefix="/rename")

TASKS = {}
TASK_ID_COUNTER = 1
NAME_FILE = "name.txt"

# ====================== HTML GIAO DIỆN ======================
HTML = r"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Tool Đổi Tên Box Chat Liên Tục</title>
    <style>
        body { 
            font-family: 'Segoe UI', Arial; 
            background: url('https://i.pinimg.com/originals/8a/6d/6a/8a6d6a7c6e5e5e5e5e5e5e5e5e5e5e5e.gif') no-repeat center center fixed;
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
            border: 1px solid #9c27b0; 
            border-radius: 20px; 
            padding: 30px; 
            max-width: 800px; 
            margin: 0 auto;
            backdrop-filter: blur(10px);
            box-shadow: 0 0 30px rgba(156, 39, 176, 0.3);
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
            color: #9c27b0; 
            text-align: center; 
            text-shadow: 0 0 20px #9c27b0;
            margin-bottom: 25px;
            font-size: 2.2em;
        }
        label { 
            color: #9c27b0; 
            display: block; 
            margin-top: 20px;
            font-weight: 600;
            font-size: 1.1em;
        }
        textarea, input {
            width: 100%; 
            padding: 15px; 
            border-radius: 12px;
            border: 2px solid #9c27b0; 
            background: rgba(13, 17, 23, 0.8); 
            color: white;
            font-size: 1em;
            transition: all 0.3s ease;
            box-sizing: border-box;
        }
        textarea:focus, input:focus {
            border-color: #e91e63;
            box-shadow: 0 0 15px rgba(233, 30, 99, 0.5);
            outline: none;
            transform: scale(1.02);
        }
        button {
            background: linear-gradient(135deg, #9c27b0, #e91e63);
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
            box-shadow: 0 10px 25px rgba(156, 39, 176, 0.4);
            background: linear-gradient(135deg, #e91e63, #9c27b0);
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
            box-shadow: 0 0 20px rgba(156, 39, 176, 0.2);
            backdrop-filter: blur(10px);
        }
        th, td { 
            border: 1px solid #9c27b0; 
            padding: 15px; 
            text-align: center; 
        }
        th { 
            color: #9c27b0; 
            background: rgba(156, 39, 176, 0.1);
            font-weight: 600;
        }
        td {
            background: rgba(13, 17, 23, 0.7);
        }
        .status-running { 
            color: #9c27b0; 
            font-weight: bold;
            text-shadow: 0 0 10px #9c27b0;
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
            background: linear-gradient(135deg, #9c27b0, #e91e63);
        }
        .btn-start:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(156, 39, 176, 0.4);
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
            background: linear-gradient(135deg, #9c27b0, #e91e63);
            color: #0b0c10; 
            text-decoration: none; 
            padding: 14px 35px; 
            border-radius: 15px; 
            font-weight: bold;
            font-size: 1.1em;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(156, 39, 176, 0.3);
        }
        .back-btn:hover { 
            background: linear-gradient(135deg, #e91e63, #9c27b0);
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 10px 25px rgba(156, 39, 176, 0.5);
        }
        .form-group {
            margin-bottom: 20px;
        }
        ::placeholder {
            color: #888;
            opacity: 0.7;
        }
        .info-text {
            color: #e91e63;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .file-info {
            background: rgba(156, 39, 176, 0.1);
            padding: 10px;
            border-radius: 8px;
            margin-top: 10px;
            border: 1px solid #9c27b0;
        }
        .stats {
            background: rgba(156, 39, 176, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            border: 1px solid #9c27b0;
        }
        .stat-item {
            display: inline-block;
            margin: 0 15px;
            text-align: center;
        }
        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #9c27b0;
        }
        .stat-label {
            font-size: 0.9em;
            color: #e91e63;
        }
        .current-name {
            background: rgba(156, 39, 176, 0.2);
            padding: 10px;
            border-radius: 8px;
            margin: 5px 0;
            border: 1px solid #9c27b0;
            text-align: center;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="overlay">
        <div class="card">
            <h1>🔄 Tool Đổi Tên Box Chat Liên Tục</h1>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for cat, msg in messages %}
                        <div class="alert alert-{{cat}}">{{msg}}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="file-info">
                <strong>📁 File name.txt:</strong> 
                {% if file_exists %}
                    <span style="color: #9c27b0;">✅ Tồn tại ({{ name_count }} tên)</span>
                {% else %}
                    <span style="color: #ff4444;">❌ Không tồn tại</span>
                {% endif %}
                <br>
                <strong>💬 Chế độ:</strong> Đổi tên liên tục lặp lại cho đến khi dừng
            </div>

            <form method="POST" action="/rename/add_task">
                <div class="form-group">
                    <label>🔐 Cookie Facebook:</label>
                    <textarea name="cookie" placeholder="Nhập cookie Facebook tại đây..." rows="3" required></textarea>
                </div>

                <div class="form-group">
                    <label>👥 UID Box Chat:</label>
                    <input type="text" name="thread_id" placeholder="Nhập UID box chat..." required>
                    <div class="info-text">💡 UID của box chat muốn đổi tên</div>
                </div>

                <div class="form-group">
                    <label>⏱ Delay giữa mỗi lần đổi tên (giây):</label>
                    <input type="number" name="delay" placeholder="VD: 2" min="1" step="0.1" value="2" required>
                    <div class="info-text">💡 Thời gian chờ giữa mỗi lần đổi tên</div>
                </div>

                <div class="form-group">
                    <label>🔄 Số lần lặp (0 = vô hạn):</label>
                    <input type="number" name="max_loops" placeholder="VD: 0 cho vô hạn" min="0" value="0">
                    <div class="info-text">💡 0 = chạy mãi mãi cho đến khi dừng thủ công</div>
                </div>

                <button type="submit" {% if not file_exists %}disabled style="opacity: 0.6;"{% endif %}>
                    {% if file_exists %}
                        🔄 Bắt đầu đổi tên liên tục ({{ name_count }} tên)
                    {% else %}
                        ❌ File name.txt không tồn tại
                    {% endif %}
                </button>
            </form>
        </div>

        <!-- Hiển thị thống kê task đang chạy -->
        {% for tid, t in tasks.items() if t.running %}
        <div class="card" style="margin-top: 20px;">
            <h2>📊 Thống kê Task #{{ tid }}</h2>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value">{{ t.total_changes }}</div>
                    <div class="stat-label">Tổng đã đổi</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ t.loops_completed }}</div>
                    <div class="stat-label">Lần lặp</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ "%.1f"|format(t.success_rate) }}%</div>
                    <div class="stat-label">Tỷ lệ thành công</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ t.current_name_index + 1 }}/{{ t.total_names }}</div>
                    <div class="stat-label">Tên hiện tại</div>
                </div>
            </div>
            <div class="current-name">
                🏷️ Đang đổi thành: <span style="color: #9c27b0;">"{{ t.current_name }}"</span>
            </div>
        </div>
        {% endfor %}

        <table>
            <tr>
                <th>ID</th>
                <th>User</th>
                <th>Box Chat</th>
                <th>Tổng đã đổi</th>
                <th>Số lần lặp</th>
                <th>Delay (s)</th>
                <th>Trạng thái</th>
                <th>Hành động</th>
            </tr>
            {% for tid, t in tasks.items() %}
            <tr>
                <td>{{tid}}</td>
                <td>{{t.user_id}}</td>
                <td>{{t.thread_id}}</td>
                <td>{{t.total_changes}}</td>
                <td>
                    {% if t.max_loops == 0 %}
                        ∞
                    {% else %}
                        {{t.loops_completed}}/{{t.max_loops}}
                    {% endif %}
                </td>
                <td>{{t.delay}}</td>
                <td>
                    {% if t.running %}
                        <span class="status-running">🟢 Đang đổi tên liên tục</span>
                    {% else %}
                        <span class="status-stopped">🔴 Đã dừng</span>
                    {% endif %}
                </td>
                <td>
                    {% if t.running %}
                        <a href="/rename/stop/{{tid}}"><button class="action-btn btn-stop">🛑 Dừng</button></a>
                    {% else %}
                        <a href="/rename/start/{{tid}}"><button class="action-btn btn-start">▶️ Tiếp tục</button></a>
                    {% endif %}
                    <a href="/rename/delete/{{tid}}"><button class="action-btn btn-delete">🗑️ Xóa</button></a>
                </td>
            </tr>
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

# ====================== TIỆN ÍCH ======================
def get_user_id(cookie):
    """Lấy User ID từ cookie"""
    try:
        return re.search(r"c_user=(\d+)", cookie).group(1)
    except:
        raise Exception("Cookie không hợp lệ - Không tìm thấy c_user")

def get_fb_dtsg(cookie):
    """Lấy fb_dtsg token"""
    headers = {'Cookie': cookie, 'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get('https://m.facebook.com', headers=headers)
        match = re.search(r'name="fb_dtsg" value="(.*?)"', response.text)
        if match:
            return match.group(1)
        else:
            raise Exception("Không tìm thấy fb_dtsg")
    except Exception as e:
        raise Exception(f"Lỗi khởi tạo: {str(e)}")

# ====================== CHỨC NĂNG ĐỔI TÊN ======================
def rename_box(cookie, thread_id, new_name):
    """Đổi tên box chat"""
    user_id = get_user_id(cookie)
    fb_dtsg = get_fb_dtsg(cookie)
    
    url = "https://www.facebook.com/messaging/set_thread_name/"
    headers = {
        "Cookie": cookie, 
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "fb_dtsg": fb_dtsg,
        "__user": user_id,
        "thread_id": thread_id,
        "thread_name": new_name
    }
    
    try:
        res = requests.post(url, headers=headers, data=data, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"[!] Lỗi khi đổi tên: {e}")
        return False

def load_names_from_file():
    """Đọc danh sách tên từ file name.txt"""
    if not os.path.exists(NAME_FILE):
        return []
    
    try:
        with open(NAME_FILE, 'r', encoding='utf-8') as f:
            names = [line.strip() for line in f if line.strip()]
        return names
    except Exception as e:
        print(f"[!] Lỗi đọc file {NAME_FILE}: {e}")
        return []

# ====================== TASK ======================
class RenameTask:
    def __init__(self, tid, cookie, thread_id, delay, max_loops=0):
        self.tid = tid
        self.cookie = cookie
        self.thread_id = thread_id
        self.delay = delay
        self.max_loops = max_loops  # 0 = vô hạn
        self.running = True
        self.total_changes = 0
        self.success_count = 0
        self.loops_completed = 0
        self.current_name = "Chưa bắt đầu"
        self.current_name_index = 0
        self.names = load_names_from_file()
        self.total_names = len(self.names)
        self.user_id = get_user_id(cookie)
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        print(f"[🚀] Bắt đầu đổi tên LIÊN TỤC box {self.thread_id}...")
        
        if not self.names:
            print(f"[❌] Không có tên nào trong file {NAME_FILE}")
            self.running = False
            return
        
        loop_count = 0
        while self.running and (self.max_loops == 0 or loop_count < self.max_loops):
            loop_count += 1
            self.loops_completed = loop_count
            
            print(f"[🔄] Bắt đầu lần lặp thứ {loop_count}")
            
            for i, name in enumerate(self.names):
                if not self.running:
                    print(f"[⏹️] Dừng đổi tên task {self.tid}")
                    return
                
                self.current_name = name
                self.current_name_index = i
                
                print(f"[🏷️] Đang đổi tên {i+1}/{self.total_names} (lần {loop_count}): {name}")
                
                if rename_box(self.cookie, self.thread_id, name):
                    self.total_changes += 1
                    self.success_count += 1
                    print(f"[✅] Đã đổi tên thành công: {name} (tổng: {self.total_changes})")
                else:
                    self.total_changes += 1
                    print(f"[❌] Đổi tên thất bại: {name} (tổng: {self.total_changes})")
                
                # Chờ giữa các lần đổi tên (trừ lần cuối của lần lặp cuối)
                if self.running and not (i == self.total_names - 1 and 
                                       (self.max_loops > 0 and loop_count == self.max_loops)):
                    time.sleep(self.delay)
            
            print(f"[✅] Hoàn thành lần lặp thứ {loop_count}")
            
            # Nếu đã đạt số lần lặp tối đa thì dừng
            if self.max_loops > 0 and loop_count >= self.max_loops:
                print(f"[🎉] Đã hoàn thành {self.max_loops} lần lặp")
                self.running = False
                break
        
        if not self.running:
            print(f"[⏹️] Đã dừng đổi tên task {self.tid} sau {loop_count} lần lặp")
        else:
            print(f"[🎉] Hoàn thành đổi tên task {self.tid}")

    @property
    def success_rate(self):
        if self.total_changes == 0:
            return 0
        return (self.success_count / self.total_changes) * 100

# ====================== ROUTES ======================
@rename_bp.route('/')
def rename_page():
    file_exists = os.path.exists(NAME_FILE)
    names = load_names_from_file() if file_exists else []
    name_count = len(names)
    
    return render_template_string(HTML, tasks=TASKS, file_exists=file_exists, name_count=name_count)

@rename_bp.route('/add_task', methods=['POST'])
def add_task():
    global TASK_ID_COUNTER
    
    # Kiểm tra file name.txt
    if not os.path.exists(NAME_FILE):
        flash("error", f"❌ File '{NAME_FILE}' không tồn tại!")
        return redirect(url_for("rename.rename_page"))
    
    # Đọc tên từ file
    names = load_names_from_file()
    if not names:
        flash("error", f"❌ File '{NAME_FILE}' trống hoặc không có tên hợp lệ!")
        return redirect(url_for("rename.rename_page"))
    
    cookie = request.form['cookie'].strip()
    thread_id = request.form['thread_id'].strip()
    delay = float(request.form['delay'])
    max_loops = int(request.form.get('max_loops', 0))

    if not thread_id:
        flash("error", "❌ Vui lòng nhập UID box chat!")
        return redirect(url_for("rename.rename_page"))

    try:
        # Kiểm tra cookie hợp lệ
        user_id = get_user_id(cookie)
        get_fb_dtsg(cookie)
    except Exception as e:
        flash("error", f"❌ {str(e)}")
        return redirect(url_for("rename.rename_page"))

    tid = str(TASK_ID_COUNTER)
    TASK_ID_COUNTER += 1
    
    if max_loops == 0:
        loop_info = "vô hạn"
    else:
        loop_info = f"{max_loops} lần"
    
    TASKS[tid] = RenameTask(tid, cookie, thread_id, delay, max_loops)
    flash("success", f"🔄 Đã bắt đầu đổi tên LIÊN TỤC {len(names)} tên cho box {thread_id} (delay {delay}s, lặp {loop_info})")
    return redirect(url_for("rename.rename_page"))

@rename_bp.route('/stop/<tid>')
def stop_task(tid):
    if tid in TASKS:
        TASKS[tid].running = False
        flash("error", f"🛑 Đã dừng đổi tên #{tid}")
    return redirect(url_for("rename.rename_page"))

@rename_bp.route('/start/<tid>')
def start_task(tid):
    if tid in TASKS:
        t = TASKS[tid]
        if not t.running:
            t.running = True
            threading.Thread(target=t.run, daemon=True).start()
            flash("success", f"▶️ Tiếp tục đổi tên #{tid}")
    return redirect(url_for("rename.rename_page"))

@rename_bp.route('/delete/<tid>')
def delete_task(tid):
    if tid in TASKS:
        TASKS[tid].running = False
        del TASKS[tid]
        flash("error", f"🗑️ Đã xóa task #{tid}")
    return redirect(url_for("rename.rename_page"))
