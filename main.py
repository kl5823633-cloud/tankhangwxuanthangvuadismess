from flask import Flask, render_template_string, request, redirect, url_for, session
from datetime import datetime, timedelta
import pytz
import json
import os

app = Flask(__name__)
app.secret_key = 'anhyeuem'

# ======= CẤU HÌNH QUẢN TRỊ =======
ADMIN_PIN = "19022011"
TIMEZONE = pytz.timezone('Asia/Ho_Chi_Minh')

# ======= FILE LƯU TRỮ DỮ LIỆU =======
DATA_FILE = "keys_data.json"

# ======= HÀM LƯU VÀ TẢI DỮ LIỆU =======
def save_keys():
    """Lưu keys và used tasks vào file JSON"""
    try:
        data = {
            'keys': KEYS,
            'used_tasks': USED_TASKS
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ Đã lưu dữ liệu keys vào file")
    except Exception as e:
        print(f"❌ Lỗi khi lưu keys: {e}")

def load_keys():
    """Tải keys và used tasks từ file JSON"""
    global KEYS, USED_TASKS
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                KEYS = data.get('keys', {})
                USED_TASKS = data.get('used_tasks', {})
            print("✅ Đã tải dữ liệu keys từ file")
        else:
            # Khởi tạo dữ liệu mẫu nếu file không tồn tại
            initialize_sample_data()
    except Exception as e:
        print(f"❌ Lỗi khi tải keys: {e}")
        initialize_sample_data()

def initialize_sample_data():
    """Khởi tạo dữ liệu mẫu nếu file không tồn tại"""
    global KEYS, USED_TASKS
    KEYS = {
        "ADMINKEY123": [None, ["treongo", "nhaydz", "so", "two_c", "rename", "dis1", "dis2", "dis3", "dis4", "dis5", "admin", "menu"], {"treongo": 999, "nhaydz": 999, "so": 999, "two_c": 999, "rename": 999, "dis1": 999, "dis2": 999, "dis3": 999, "dis4": 999, "dis5": 999}],
        "USERKEY1": [
            (datetime.now(TIMEZONE) + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), 
            ["treongo", "nhaydz", "two_c", "rename", "dis1", "dis2", "menu"], 
            {"treongo": 5, "nhaydz": 10, "so": 0, "two_c": 15, "rename": 20, "dis1": 10, "dis2": 8, "dis3": 0, "dis4": 0, "dis5": 0}
        ]
    }
    USED_TASKS = {}
    save_keys()
    print("✅ Đã khởi tạo dữ liệu mẫu")

# ======= KHỞI TẠO DỮ LIỆU =======
KEYS = {}
USED_TASKS = {}
CHAT_MESSAGES = []

# Tải dữ liệu khi khởi động server
load_keys()

# ======= TIỆN ÍCH HỖ TRỢ =======
def get_vietnam_time():
    return datetime.now(TIMEZONE)

def make_naive(dt):
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

def get_remaining_tasks(key, tool_type):
    if key not in KEYS:
        return 0
    
    expire, permissions, task_limits = KEYS[key]
    
    if tool_type not in permissions and 'admin' not in permissions:
        return 0
    
    max_tasks = task_limits.get(tool_type, 0)
    used = USED_TASKS.get(key, {}).get(tool_type, 0)
    
    return max(0, max_tasks - used)

def use_task(key, tool_type):
    if key not in USED_TASKS:
        USED_TASKS[key] = {}
    
    if tool_type not in USED_TASKS[key]:
        USED_TASKS[key][tool_type] = 0
    
    USED_TASKS[key][tool_type] += 1
    save_keys()  # Lưu sau mỗi lần sử dụng task
    return get_remaining_tasks(key, tool_type)

def reset_tasks(key=None, tool_type=None):
    if key is None:
        USED_TASKS.clear()
    elif tool_type is None:
        USED_TASKS[key] = {}
    else:
        if key in USED_TASKS and tool_type in USED_TASKS[key]:
            USED_TASKS[key][tool_type] = 0
    save_keys()  # Lưu sau khi reset

# ======= MIDDLEWARE KIỂM TRA KEY =======
@app.before_request
def check_key():
    public_routes = ['login', 'logout', 'static', 'admin_panel', 'generate_key', 'delete_key', 'tool_page', 'reset_tasks_route', 'send_chat', 'get_chat', 'welcome']
    
    if request.endpoint and any(route in request.endpoint for route in public_routes):
        return
    
    if 'key' not in session:
        return redirect(url_for('login'))
    
    key = session['key']
    if key not in KEYS:
        session.pop('key', None)
        return redirect(url_for('login'))
    
    expire, permissions, task_limits = KEYS[key]
    
    if expire:
        expire_dt = datetime.strptime(expire, "%Y-%m-%d %H:%M:%S")
        current_dt = make_naive(get_vietnam_time())
        if current_dt > expire_dt:
            session.pop('key', None)
            return render_template_string("<h1>🔒 Key đã hết hạn!</h1>"), 403
    
    if request.endpoint:
        endpoint_name = request.endpoint
        
        endpoint_to_permission = {
            'menu': 'menu',
            'treongo.treongo_page': 'treongo',
            'nhaydz.nhaydz_page': 'nhaydz',  
            'so.so_page': 'so',
            'two_c.two_c_page': 'two_c',
            'rename.rename_page': 'rename',
            'dis1.dis1_page': 'dis1',
            'dis1.add_task': 'dis1',
            'dis1.start_task_route': 'dis1',
            'dis1.stop_task': 'dis1',
            'dis1.delete_task': 'dis1',
            'dis2.dis2_page': 'dis2',
            'dis2.add_task': 'dis2',
            'dis2.start_task_route': 'dis2',
            'dis2.stop_task': 'dis2',
            'dis2.delete_task': 'dis2',
            'dis3.dis3_page': 'dis3',
            'dis3.add_task': 'dis3',
            'dis3.start_task_route': 'dis3',
            'dis3.stop_task': 'dis3',
            'dis3.delete_task': 'dis3',
            'dis4.dis4_page': 'dis4',
            'dis4.add_task': 'dis4',
            'dis4.start_task_route': 'dis4',
            'dis4.stop_task': 'dis4',
            'dis4.delete_task': 'dis4',
            'dis5.dis5_page': 'dis5',
            'dis5.add_task': 'dis5',
            'dis5.start_task_route': 'dis5',
            'dis5.stop_task': 'dis5',
            'dis5.delete_task': 'dis5',
            'treongo': 'treongo',
            'nhaydz': 'nhaydz',
            'so': 'so',
            'two_c': 'two_c',
            'rename': 'rename',
            'dis1': 'dis1',
            'dis2': 'dis2',
            'dis3': 'dis3',
            'dis4': 'dis4',
            'dis5': 'dis5'
        }
        
        required_permission = endpoint_to_permission.get(endpoint_name)
        
        if required_permission is None:
            return
        
        has_permission = (required_permission in permissions) or ('admin' in permissions)
        
        if not has_permission:
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>🚫 Không có quyền</title>
                <style>
                    body {
                        background: linear-gradient(135deg, #ff6b6b, #c23636);
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        color: white;
                        text-align: center;
                    }
                    .error-box {
                        background: rgba(0, 0, 0, 0.7);
                        padding: 40px;
                        border-radius: 15px;
                        box-shadow: 0 0 20px rgba(0,0,0,0.3);
                    }
                    a {
                        color: #ffcc00;
                        text-decoration: none;
                        display: block;
                        margin-top: 20px;
                        padding: 10px;
                        border: 1px solid #ffcc00;
                        border-radius: 5px;
                    }
                    a:hover {
                        background: #ffcc00;
                        color: black;
                    }
                </style>
            </head>
            <body>
                <div class="error-box">
                    <h1>🚫 Không có quyền truy cập!</h1>
                    <p>Key của bạn không có quyền sử dụng tính năng này.</p>
                    <p><strong>Key:</strong> {{ session.key }}</p>
                    <p><strong>Quyền hiện có:</strong> {{ permissions }}</p>
                    <a href="/menu">↩️ Quay về Menu</a>
                    <a href="/logout">🚪 Đăng xuất</a>
                </div>
            </body>
            </html>
            """, permissions=permissions), 403

# ======= TRANG NHẬP KEY =======
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        key = request.form.get('key', '').strip()
        if key in KEYS:
            expire, permissions, task_limits = KEYS[key]
            if expire:
                expire_dt = datetime.strptime(expire, "%Y-%m-%d %H:%M:%S")
                current_dt = make_naive(get_vietnam_time())
                if current_dt < expire_dt or expire is None:
                    session['key'] = key
                    session['permissions'] = permissions
                    session['task_limits'] = task_limits
                    session['login_time'] = datetime.now().strftime("%H:%M:%S")
                    return redirect(url_for('welcome'))
                else:
                    return render_template_string("<h1>🔒 Key đã hết hạn!</h1>"), 403
            else:
                session['key'] = key
                session['permissions'] = permissions
                session['task_limits'] = task_limits
                session['login_time'] = datetime.now().strftime("%H:%M:%S")
                return redirect(url_for('welcome'))
        return render_template_string("<h1>❌ Key không hợp lệ!</h1>"), 403

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>🔑 Nhập Key Sử Dụng</title>
        <style>
            body {
                background: url('https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExYTlxZmZ4MGR2dWoxeHh1czhkcGlyMndmcjIzYnZzaWJjZHJiNWNpcyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/OpYV9CBVZOb1S/giphy.gif') no-repeat center center fixed;
                background-size: cover;
                font-family: 'Segoe UI', sans-serif;
                color: white;
                text-align: center;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 0;
            }
            .login-box {
                background: rgba(0, 0, 0, 0.8);
                border: 2px solid #00ffff;
                border-radius: 20px;
                padding: 40px;
                width: 380px;
                box-shadow: 0 0 35px #00ffff;
                backdrop-filter: blur(10px);
                animation: fadeIn 1s ease;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: scale(0.9); }
                to { opacity: 1; transform: scale(1); }
            }
            input {
                padding: 15px;
                border-radius: 12px;
                border: 2px solid #00ffff;
                width: 90%;
                text-align: center;
                font-size: 16px;
                background: rgba(0,0,0,0.7);
                color: #00ffff;
                outline: none;
                margin-bottom: 20px;
                transition: all 0.3s ease;
            }
            input:focus {
                border-color: #ff00ff;
                box-shadow: 0 0 15px #ff00ff;
            }
            input::placeholder {
                color: #a0a0a0;
            }
            button {
                padding: 15px 25px;
                border-radius: 12px;
                border: none;
                background: linear-gradient(135deg, #00ffff, #ff00ff);
                color: #000;
                font-weight: bold;
                cursor: pointer;
                width: 100%;
                transition: 0.3s;
                font-size: 16px;
                margin-top: 10px;
            }
            button:hover {
                transform: scale(1.05);
                box-shadow: 0 0 20px #ff00ff;
            }
            h1 {
                color: #00ffff;
                text-shadow: 0 0 20px #00ffff;
                margin-bottom: 20px;
                font-size: 2.2rem;
            }
            footer {
                margin-top: 20px;
                font-size: 14px;
                color: #cccccc;
                opacity: 0.8;
            }
            .admin-link {
                margin-top: 20px;
                display: block;
                color: #ffcc00;
                text-decoration: none;
                padding: 10px;
                border: 1px solid #ffcc00;
                border-radius: 8px;
                transition: 0.3s;
            }
            .admin-link:hover {
                background: #ffcc00;
                color: black;
                transform: scale(1.05);
            }
            .logo {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                border: 3px solid #00ffff;
                margin: 0 auto 20px;
                background: url('https://www.pinterest.com/pin/386676318027687148/') center/cover;
                box-shadow: 0 0 20px #00ffff;
            }
        </style>
    </head>
    <body>
        <div class="login-box">
            <div class="logo"></div>
            <h1>🔐 Xác Thực Key</h1>
            <form method="POST">
                <input type="text" name="key" placeholder="🎯 Nhập key tại đây..." required><br>
                <button type="submit">⚡ Xác Nhận & Tiếp Tục</button>
            </form>
            <a href="/admin" class="admin-link">👑 Khu Vực Quản Trị</a>
            <footer>© 2025 ❄️ XuanThang w DucDai 🌠</footer>
        </div>
    </body>
    </html>
    """)

# ======= TRANG WELCOME SAU KHI LOGIN =======
@app.route('/welcome')
def welcome():
    if 'key' not in session:
        return redirect(url_for('login'))
    
    key = session['key']
    expire, permissions, task_limits = KEYS[key]
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>🎉 Đăng Nhập Thành Công - XuanThangwDucDai</title>
        <style>
            body {
                background: url('https://www.pinterest.com/pin/120119515050791526/') no-repeat center center fixed;
                background-size: cover;
                font-family: 'Segoe UI', sans-serif;
                color: white;
                text-align: center;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 0;
                overflow: hidden;
            }
            .welcome-container {
                background: rgba(0, 0, 0, 0.9);
                border: 3px solid #00ffff;
                border-radius: 25px;
                padding: 40px;
                width: 500px;
                box-shadow: 0 0 50px #00ffff;
                backdrop-filter: blur(15px);
                animation: slideIn 0.8s ease;
            }
            @keyframes slideIn {
                from { opacity: 0; transform: translateY(-50px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .success-icon {
                font-size: 5rem;
                color: #00ff00;
                text-shadow: 0 0 30px #00ff00;
                margin-bottom: 20px;
                animation: pulse 1.5s infinite;
            }
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
            .loading-bar {
                width: 100%;
                height: 8px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                margin: 30px 0;
                overflow: hidden;
            }
            .loading-progress {
                width: 0%;
                height: 100%;
                background: linear-gradient(90deg, #00ffff, #ff00ff);
                border-radius: 4px;
                animation: loading 3s ease-in-out forwards;
            }
            @keyframes loading {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            h1 {
                color: #00ffff;
                text-shadow: 0 0 20px #00ffff;
                margin-bottom: 15px;
                font-size: 2.2rem;
            }
            .welcome-text {
                font-size: 1.2rem;
                color: #ffcc00;
                margin-bottom: 20px;
                text-shadow: 0 0 10px #ffcc00;
            }
            .user-info {
                background: rgba(0, 255, 255, 0.2);
                padding: 15px;
                border-radius: 12px;
                margin: 20px 0;
                border: 1px solid #00ffff;
            }
            .countdown {
                font-size: 1.1rem;
                color: #ff00ff;
                margin-top: 20px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="welcome-container">
            <div class="success-icon">✅</div>
            <h1>ĐĂNG NHẬP THÀNH CÔNG!</h1>
            <div class="welcome-text">🎉 Chào mừng đến với Web by XuanThangwDucDai</div>
            
            <div class="user-info">
                <strong>🔑 Key:</strong> {{ session.key }}<br>
                <strong>⏰ Thời gian:</strong> {{ session.login_time }}<br>
                <strong>📅 Thời hạn:</strong> {{ expire if expire else "Vĩnh viễn" }}
            </div>
            
            <div class="loading-bar">
                <div class="loading-progress"></div>
            </div>
            
            <div class="countdown" id="countdown">Đang chuyển hướng... (3s)</div>
            <div style="margin-top: 10px; font-size: 0.9rem; color: #cccccc;">
                Hệ thống đang chuẩn bị môi trường cho bạn...
            </div>
        </div>

        <script>
            let seconds = 3;
            const countdownElement = document.getElementById('countdown');
            
            const countdownInterval = setInterval(() => {
                seconds--;
                countdownElement.textContent = `Đang chuyển hướng... (${seconds}s)`;
                
                if (seconds <= 0) {
                    clearInterval(countdownInterval);
                    window.location.href = '/menu';
                }
            }, 1000);

            // Tự động chuyển hướng sau 3 giây
            setTimeout(() => {
                window.location.href = '/menu';
            }, 3000);
        </script>
    </body>
    </html>
    """, expire=expire)

# ======= TRANG QUẢN TRỊ =======
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        pin = request.form.get('pin', '').strip()
        if pin != ADMIN_PIN:
            return render_template_string("<h1>❌ PIN admin không đúng!</h1>"), 403
        
        session['admin'] = True
        return redirect(url_for('admin_panel'))
    
    if 'admin' not in session:
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <title>🔧 Admin Panel</title>
            <style>
                body {
                    background: linear-gradient(135deg, #1a2a3a, #2d4a5c);
                    font-family: 'Segoe UI', sans-serif;
                    color: white;
                    text-align: center;
                    padding: 50px;
                }
                .admin-box {
                    background: rgba(0, 0, 0, 0.6);
                    border: 2px solid #ffcc00;
                    border-radius: 15px;
                    padding: 40px;
                    width: 350px;
                    margin: 0 auto;
                    box-shadow: 0 0 25px #ffcc00;
                }
                input {
                    padding: 12px;
                    border-radius: 8px;
                    border: 1px solid #ffcc00;
                    width: 90%;
                    text-align: center;
                    font-size: 16px;
                    background: rgba(0,0,0,0.5);
                    color: #ffcc00;
                    margin-bottom: 15px;
                }
                button {
                    padding: 12px 20px;
                    border-radius: 10px;
                    border: none;
                    background: #ffcc00;
                    color: #000;
                    font-weight: bold;
                    cursor: pointer;
                    width: 100%;
                }
                button:hover {
                    background: #ffaa00;
                }
            </style>
        </head>
        <body>
            <div class="admin-box">
                <h1>🔧 Xác thực Admin</h1>
                <form method="POST">
                    <input type="password" name="pin" placeholder="Nhập PIN admin..." required><br>
                    <button type="submit">🔑 Xác nhận</button>
                </form>
            </div>
        </body>
        </html>
        """)
    
    current_time_naive = make_naive(get_vietnam_time())
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>🔧 Quản lý Key</title>
        <style>
            body {
                background: linear-gradient(135deg, #1a2a3a, #2d4a5c);
                font-family: 'Segoe UI', sans-serif;
                color: white;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 {
                color: #ffcc00;
                text-align: center;
            }
            .section {
                background: rgba(0, 0, 0, 0.6);
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                border: 1px solid #ffcc00;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #444;
            }
            th {
                background: rgba(255, 204, 0, 0.2);
            }
            input, select {
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #ffcc00;
                background: rgba(0,0,0,0.5);
                color: white;
                margin: 5px;
            }
            button {
                padding: 10px 15px;
                border-radius: 5px;
                border: none;
                background: #ffcc00;
                color: #000;
                font-weight: bold;
                cursor: pointer;
                margin: 5px;
            }
            button:hover {
                background: #ffaa00;
            }
            .delete-btn {
                background: #ff4444;
                color: white;
            }
            .delete-btn:hover {
                background: #ff0000;
            }
            .reset-btn {
                background: #44ff44;
                color: black;
            }
            .reset-btn:hover {
                background: #00ff00;
            }
            .nav-links {
                text-align: center;
                margin: 20px 0;
            }
            .nav-links a {
                color: #00ffff;
                text-decoration: none;
                margin: 0 15px;
                padding: 10px 20px;
                border: 1px solid #00ffff;
                border-radius: 5px;
            }
            .nav-links a:hover {
                background: #00ffff;
                color: #000;
            }
            .task-limits {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 10px;
                margin: 15px 0;
            }
            .task-limit-item {
                background: rgba(255, 204, 0, 0.1);
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #ffcc00;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 Quản lý Key hệ thống</h1>
            
            <div class="nav-links">
                <a href="/menu">🏠 Về Menu</a>
                <a href="/admin_chat">💬 Chat với Users</a>
                <a href="/logout">🚪 Đăng xuất</a>
            </div>

            <div class="section">
                <h2>🔄 Quản lý Task Counter</h2>
                <form method="POST" action="/reset_tasks">
                    <button type="submit" name="reset_all" value="true" class="reset-btn">🔄 Reset TẤT CẢ Task Counters</button>
                    <p><small>Reset số lượng task đã sử dụng của tất cả key về 0</small></p>
                </form>
            </div>
            
            <div class="section">
                <h2>🔑 Tạo Key mới</h2>
                <form method="POST" action="/generate_key">
                    <input type="text" name="key_name" placeholder="Tên key (ví dụ: USER001)" required>
                    <select name="duration_type">
                        <option value="hours">Giờ</option>
                        <option value="days">Ngày</option>
                        <option value="months">Tháng</option>
                        <option value="permanent">Vĩnh viễn</option>
                    </select>
                    <input type="number" name="duration" placeholder="Số lượng" min="1" value="1">
                    
                    <h3>📋 Chọn tính năng được phép:</h3>
                    <div>
                        <label><input type="checkbox" name="permissions" value="treongo" checked> Treo Ngôn</label>
                        <label><input type="checkbox" name="permissions" value="nhaydz" checked> Nhây DZ</label>
                        <label><input type="checkbox" name="permissions" value="so" checked> Số</label>
                        <label><input type="checkbox" name="permissions" value="two_c" checked> 2C</label>
                        <label><input type="checkbox" name="permissions" value="rename" checked> Rename</label>
                        <label><input type="checkbox" name="permissions" value="dis1" checked>Treo Ngôn Discord</label>
                        <label><input type="checkbox" name="permissions" value="dis2" checked>Nhây Tag Discord</label>
                        <label><input type="checkbox" name="permissions" value="dis3">Nhây Poll Discord</label>
                        <label><input type="checkbox" name="permissions" value="dis4"> Discord Spam 4</label>
                        <label><input type="checkbox" name="permissions" value="dis5"> Treo Room Discord</label>
                        <label><input type="checkbox" name="permissions" value="admin"> Quyền Admin</label>
                        <label><input type="checkbox" name="permissions" value="menu" checked> Menu Chính</label>
                    </div>

                    <h3>🎯 Giới hạn Task (0 = không có quyền):</h3>
                    <div class="task-limits">
                        <div class="task-limit-item">
                            <label>Treo Ngôn:</label>
                            <input type="number" name="limit_treongo" min="0" value="5" style="width: 80px;">
                        </div>
                        <div class="task-limit-item">
                            <label>Nhây:</label>
                            <input type="number" name="limit_nhaydz" min="0" value="10" style="width: 80px;">
                        </div>
                        <div class="task-limit-item">
                            <label>Sớ:</label>
                            <input type="number" name="limit_so" min="0" value="5" style="width: 80px;">
                        </div>
                        <div class="task-limit-item">
                            <label>2C:</label>
                            <input type="number" name="limit_two_c" min="0" value="15" style="width: 80px;">
                        </div>
                        <div class="task-limit-item">
                            <label>Rename:</label>
                            <input type="number" name="limit_rename" min="0" value="20" style="width: 80px;">
                        </div>
                        <div class="task-limit-item">
                            <label>Treo Ngôn Discord:</label>
                            <input type="number" name="limit_dis1" min="0" value="10" style="width: 80px;">
                       </div>
                        <div class="task-limit-item">
                            <label>Nhây Tag Discord:</label>
                            <input type="number" name="limit_dis2" min="0" value="8" style="width: 80px;">
                       </div>
                        <div class="task-limit-item">
                            <label>Nhây Poll Discord:</label>
                            <input type="number" name="limit_dis3" min="0" value="0" style="width: 80px;">
                       </div>
                        <div class="task-limit-item">
                            <label>Discord Spam 4:</label>
                            <input type="number" name="limit_dis4" min="0" value="0" style="width: 80px;">
                       </div>
                        <div class="task-limit-item">
                            <label>Treo Room Discord:</label>
                            <input type="number" name="limit_dis5" min="0" value="0" style="width: 80px;">
                       </div>
                    </div>
                    
                    <button type="submit">🎯 Tạo Key</button>
                </form>
            </div>
            
            <div class="section">
                <h2>📊 Danh sách Key hiện có</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Key</th>
                            <th>Thời hạn</th>
                            <th>Quyền hạn</th>
                            <th>Giới hạn Task</th>
                            <th>Đã sử dụng</th>
                            <th>Trạng thái</th>
                            <th>Thao tác</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for key, data in keys.items() %}
                        <tr>
                            <td><code>{{ key }}</code></td>
                            <td>{{ data[0] if data[0] else "Vĩnh viễn" }}</td>
                            <td>{{ ", ".join(data[1]) if data[1] else "Không có" }}</td>
                            <td>
                                {% if data[2] %}
                                    {% for tool, limit in data[2].items() %}
                                        {{ tool }}: {{ limit }}<br>
                                    {% endfor %}
                                {% else %}
                                    Không có
                                {% endif %}
                            </td>
                            <td>
                                {% set used_tasks = used_tasks_dict.get(key, {}) %}
                                {% for tool in ['treongo', 'nhaydz', 'so', 'two_c', 'rename', 'dis1', 'dis2', 'dis3', 'dis4', 'dis5'] %}
                                    {{ tool }}: {{ used_tasks.get(tool, 0) }}<br>
                                {% endfor %}
                            </td>
                            <td>
                                {% if data[0] %}
                                    {% set expire_dt = datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S") %}
                                    {% if now < expire_dt %}
                                        <span style="color: #00ff00;">✅ Hoạt động</span>
                                    {% else %}
                                        <span style="color: #ff4444;">❌ Hết hạn</span>
                                    {% endif %}
                                {% else %}
                                    <span style="color: #00ff00;">✅ Vĩnh viễn</span>
                                {% endif %}
                            </td>
                            <td>
                                <form action="/delete_key" method="POST" style="display: inline;">
                                    <input type="hidden" name="key" value="{{ key }}">
                                    <button type="submit" class="delete-btn" onclick="return confirm('Xóa key {{ key }}?')">🗑️ Xóa</button>
                                </form>
                                <form action="/reset_tasks" method="POST" style="display: inline;">
                                    <input type="hidden" name="key" value="{{ key }}">
                                    <button type="submit" class="reset-btn" onclick="return confirm('Reset task counter cho {{ key }}?')">🔄 Reset Task</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """, keys=KEYS, now=current_time_naive, datetime=datetime, used_tasks_dict=USED_TASKS)

# ======= TẠO KEY MỚI =======
@app.route('/generate_key', methods=['POST'])
def generate_key():
    if 'admin' not in session:
        return redirect(url_for('admin_panel'))
    
    key_name = request.form.get('key_name', '').strip().upper()
    duration_type = request.form.get('duration_type')
    duration = int(request.form.get('duration', 1))
    permissions = request.form.getlist('permissions')
    
    # Lấy giới hạn task
    limit_treongo = int(request.form.get('limit_treongo', 0))
    limit_nhaydz = int(request.form.get('limit_nhaydz', 0))
    limit_so = int(request.form.get('limit_so', 0))
    limit_two_c = int(request.form.get('limit_two_c', 0))
    limit_rename = int(request.form.get('limit_rename', 0))
    limit_dis1 = int(request.form.get('limit_dis1', 0))
    limit_dis2 = int(request.form.get('limit_dis2', 0))
    limit_dis3 = int(request.form.get('limit_dis3', 0))
    limit_dis4 = int(request.form.get('limit_dis4', 0))
    limit_dis5 = int(request.form.get('limit_dis5', 0))
    
    if not key_name:
        return "Tên key không được để trống!", 400
    
    if key_name in KEYS:
        return "Key đã tồn tại!", 400
    
    # THÊM QUYỀN MENU MẶC ĐỊNH
    if 'menu' not in permissions:
        permissions.append('menu')
    
    # Tính thời gian hết hạn
    if duration_type == 'permanent':
        expire_time = None
    else:
        now = get_vietnam_time()
        if duration_type == 'hours':
            expire_time = now + timedelta(hours=duration)
        elif duration_type == 'days':
            expire_time = now + timedelta(days=duration)
        elif duration_type == 'months':
            expire_time = now + timedelta(days=duration * 30)
        
        expire_time = expire_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Tạo task limits dictionary
    task_limits = {
        "treongo": limit_treongo,
        "nhaydz": limit_nhaydz,
        "so": limit_so,
        "two_c": limit_two_c,
        "rename": limit_rename,
        "dis1": limit_dis1,
        "dis2": limit_dis2,
        "dis3": limit_dis3,
        "dis4": limit_dis4,
        "dis5": limit_dis5
    }
    
    # Lưu key mới
    KEYS[key_name] = [expire_time, permissions, task_limits]
    save_keys()  # Lưu vào file
    
    return redirect(url_for('admin_panel'))

# ======= XÓA KEY =======
@app.route('/delete_key', methods=['POST'])
def delete_key():
    if 'admin' not in session:
        return redirect(url_for('admin_panel'))
    
    key_to_delete = request.form.get('key')
    if key_to_delete in KEYS:
        del KEYS[key_to_delete]
        if key_to_delete in USED_TASKS:
            del USED_TASKS[key_to_delete]
        save_keys()  # Lưu vào file sau khi xóa
    
    return redirect(url_for('admin_panel'))

# ======= RESET TASK COUNTER =======
@app.route('/reset_tasks', methods=['POST'])
def reset_tasks_route():
    if 'admin' not in session:
        return redirect(url_for('admin_panel'))
    
    if request.form.get('reset_all'):
        USED_TASKS.clear()
    else:
        key = request.form.get('key')
        if key:
            reset_tasks(key)
    
    save_keys()  # Lưu vào file sau khi reset
    return redirect(url_for('admin_panel'))

# ======= CHAT FUNCTIONALITY =======
@app.route('/send_chat', methods=['POST'])
def send_chat():
    if 'key' not in session and 'admin' not in session:
        return {"success": False}, 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if message:
        # Xác định người gửi
        if 'admin' in session:
            sender = 'admin'
            sender_name = '👑 ADMIN'
            sender_key = 'ADMIN'
        else:
            sender = 'user'
            sender_name = f"👤 {session['key'][:8]}..." if len(session['key']) > 8 else f"👤 {session['key']}"
            sender_key = session['key']
        
        CHAT_MESSAGES.append({
            'sender': sender,
            'sender_name': sender_name,
            'sender_key': sender_key,
            'text': message,
            'time': datetime.now().strftime("%H:%M:%S")
        })
        
        # Giữ chỉ 50 tin nhắn gần nhất
        if len(CHAT_MESSAGES) > 50:
            CHAT_MESSAGES.pop(0)
    
    return {"success": True}

@app.route('/get_chat')
def get_chat():
    return json.dumps(CHAT_MESSAGES)

# ======= ADMIN CHAT INTERFACE =======
@app.route('/admin_chat')
def admin_chat():
    if 'admin' not in session:
        return redirect(url_for('admin_panel'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>💬 Admin Chat</title>
        <style>
            body {
                background: linear-gradient(135deg, #1a2a3a, #2d4a5c);
                font-family: 'Segoe UI', sans-serif;
                color: white;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 20px;
            }
            .chat-container {
                background: rgba(0, 0, 0, 0.7);
                border-radius: 15px;
                padding: 20px;
                height: 600px;
                display: flex;
                flex-direction: column;
            }
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                border: 1px solid #ffcc00;
                border-radius: 10px;
                margin-bottom: 15px;
                background: rgba(0, 0, 0, 0.5);
            }
            .message {
                margin-bottom: 15px;
                padding: 12px;
                border-radius: 10px;
                max-width: 80%;
                word-wrap: break-word;
            }
            .message.user {
                background: rgba(0, 255, 255, 0.3);
                margin-left: auto;
                border: 1px solid #00ffff;
            }
            .message.admin {
                background: rgba(255, 204, 0, 0.3);
                margin-right: auto;
                border: 1px solid #ffcc00;
            }
            .message-header {
                font-size: 0.8rem;
                opacity: 0.8;
                margin-bottom: 5px;
                display: flex;
                justify-content: space-between;
            }
            .message-time {
                font-size: 0.7rem;
                color: #cccccc;
            }
            .chat-input {
                display: flex;
                gap: 10px;
            }
            .chat-input input {
                flex: 1;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #ffcc00;
                background: rgba(0,0,0,0.5);
                color: white;
            }
            .chat-input button {
                padding: 12px 20px;
                border-radius: 8px;
                border: none;
                background: #ffcc00;
                color: black;
                font-weight: bold;
                cursor: pointer;
            }
            .close-chat {
                background: none;
                border: none;
                color: white;
                font-size: 1.2rem;
                cursor: pointer;
            }
            .user-list {
                background: rgba(0, 0, 0, 0.6);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                border: 1px solid #00ffff;
            }
            .user-list h3 {
                color: #00ffff;
                margin-bottom: 10px;
            }
            .user-item {
                padding: 8px;
                margin: 5px 0;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
                border-left: 3px solid #00ff00;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💬 Admin Chat Panel</h1>
                <p>Trò chuyện với người dùng hệ thống</p>
            </div>

            <div class="user-list">
                <h3>👥 Người dùng đang online:</h3>
                <div id="onlineUsers">
                    <div class="user-item">Đang tải...</div>
                </div>
            </div>
            
            <div class="chat-container">
                <div class="chat-messages" id="chatMessages">
                    <!-- Messages will be loaded here -->
                </div>
                
                <div class="chat-input">
                    <input type="text" id="chatInput" placeholder="Nhập tin nhắn cho người dùng...">
                    <button onclick="sendMessage()">Gửi</button>
                </div>
            </div>
            
            <div class="nav-buttons">
                <a href="/admin">🔧 Quay về Admin Panel</a>
                <a href="/logout">🚪 Đăng xuất</a>
            </div>
        </div>

        <script>
            function loadChatMessages() {
                fetch('/get_chat')
                    .then(response => response.json())
                    .then(messages => {
                        const chatMessages = document.getElementById('chatMessages');
                        chatMessages.innerHTML = '';
                        messages.forEach(msg => {
                            const messageDiv = document.createElement('div');
                            messageDiv.className = `message ${msg.sender}`;
                            messageDiv.innerHTML = `
                                <div class="message-header">
                                    <strong>${msg.sender_name}</strong>
                                    <span class="message-time">${msg.time}</span>
                                </div>
                                <div>${msg.text}</div>
                                ${msg.sender === 'user' ? `<div style="font-size: 0.7rem; margin-top: 5px; opacity: 0.7;">Key: ${msg.sender_key}</div>` : ''}
                            `;
                            chatMessages.appendChild(messageDiv);
                        });
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    });
            }

            function updateOnlineUsers() {
                // Trong thực tế, bạn sẽ lấy danh sách user từ server
                // Ở đây tôi chỉ minh họa
                const onlineUsers = document.getElementById('onlineUsers');
                onlineUsers.innerHTML = `
                    <div class="user-item">USERKEY1 (Đang hoạt động)</div>
                    <div class="user-item">USERKEY2 (Đang chat)</div>
                `;
            }

            function sendMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                if (message) {
                    fetch('/send_chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ message: message })
                    }).then(() => {
                        input.value = '';
                        loadChatMessages();
                    });
                }
            }

            // Auto refresh every 2 seconds
            setInterval(loadChatMessages, 2000);
            setInterval(updateOnlineUsers, 5000);

            // Enter key to send
            document.getElementById('chatInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            // Load messages on page load
            loadChatMessages();
            updateOnlineUsers();
        </script>
    </body>
    </html>
    ''')

# ======= TRANG MENU CHÍNH =======
@app.route('/menu')
def menu():
    if 'key' not in session:
        return redirect(url_for('login'))

    key = session['key']
    if key not in KEYS:
        session.pop('key', None)
        return redirect(url_for('login'))
    
    expire, permissions, task_limits = KEYS[key]
    
    if expire:
        expire_dt = datetime.strptime(expire, "%Y-%m-%d %H:%M:%S")
        current_dt = make_naive(get_vietnam_time())
        if current_dt > expire_dt:
            session.pop('key', None)
            return "<h1>🔒 Key đã hết hạn!</h1>", 403

    # SỬA LẠI PHẦN NÀY - Sử dụng đúng tên công cụ
    remaining_tasks = {}
    for tool in ['treongo', 'nhaydz', 'so', 'two_c', 'rename', 'dis1', 'dis2', 'dis3', 'dis4', 'dis5']:
        remaining_tasks[tool] = get_remaining_tasks(key, tool)

    # Tạo dictionary tên công cụ tiếng Việt
    tool_names = {
        'treongo': 'Treo Ngôn',
        'nhaydz': 'Nhây', 
        'so': 'Sớ',
        'two_c': '2C',
        'rename': 'Rename Box',
        'dis1': 'Treo Ngôn Discord',
        'dis2': 'Nhây Tag Discord', 
        'dis3': 'Poll Discord',
        'dis4': 'Thread Discord',
        'dis5': 'Treo Room Discord'
    }

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>🌐 Menu Chính - XuanThang System</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                background: url('https://i.pinimg.com/originals/88/93/df/8893dffe4a3258c4f5998bdae9b03d8c.gif') no-repeat center center fixed;
                background-size: cover;
                color: white;
                font-family: 'Segoe UI', sans-serif;
                min-height: 100vh;
                position: relative;
                overflow-x: hidden;
            }
            body::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                z-index: -1;
            }
            .header {
                text-align: center;
                padding: 30px 20px;
                background: rgba(0, 0, 0, 0.8);
                border-bottom: 2px solid #00ffff;
                box-shadow: 0 5px 30px rgba(0, 255, 255, 0.3);
            }
            .user-info {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 20px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }
            .avatar {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                border: 3px solid #00ffff;
                background: url('https://i.imgur.com/3Q1Jj9J.png') center/cover;
                box-shadow: 0 0 25px #00ffff;
                animation: glow 2s infinite alternate;
            }
            @keyframes glow {
                from { box-shadow: 0 0 25px #00ffff; }
                to { box-shadow: 0 0 35px #ff00ff, 0 0 45px #00ffff; }
            }
            .user-details {
                text-align: left;
            }
            .welcome-text {
                font-size: 1.8rem;
                color: #00ffff;
                text-shadow: 0 0 15px #00ffff;
                margin-bottom: 10px;
            }
            .subtitle {
                font-size: 1.1rem;
                color: #ff00ff;
                text-shadow: 0 0 10px #ff00ff;
                font-style: italic;
            }
            .key-display {
                background: rgba(0, 0, 0, 0.6);
                padding: 15px;
                border-radius: 12px;
                border: 1px solid #00ffff;
                margin: 15px auto;
                max-width: 600px;
                backdrop-filter: blur(10px);
            }
            .task-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                padding: 30px;
                max-width: 1400px;
                margin: 0 auto;
            }
            .tool-card {
                background: rgba(0, 0, 0, 0.8);
                border: 2px solid;
                border-radius: 15px;
                padding: 25px;
                text-align: center;
                transition: all 0.3s ease;
                text-decoration: none;
                color: white;
                backdrop-filter: blur(10px);
                position: relative;
                overflow: hidden;
            }
            .tool-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
                transition: 0.5s;
            }
            .tool-card:hover::before {
                left: 100%;
            }
            .tool-card:hover {
                transform: translateY(-10px) scale(1.05);
                box-shadow: 0 15px 30px rgba(0, 255, 255, 0.4);
            }
            .tool-card.treongo { border-color: #00ffff; }
            .tool-card.nhaydz { border-color: #ff00ff; }
            .tool-card.so { border-color: #00ff00; }
            .tool-card.two_c { border-color: #ffff00; }
            .tool-card.rename { border-color: #ff9900; }
            .tool-card.dis1 { border-color: #ff4444; }
            .tool-card.dis2 { border-color: #ff6b6b; }
            .tool-card.dis3 { border-color: #6bff6b; }
            .tool-card.dis4 { border-color: #6b6bff; }
            .tool-card.dis5 { border-color: #ff6bff; }
            .tool-card.disabled {
                opacity: 0.4;
                cursor: not-allowed;
                border-color: #666 !important;
            }
            .tool-card.disabled:hover {
                transform: none;
                box-shadow: none;
            }
            .tool-icon {
                font-size: 2.5rem;
                margin-bottom: 15px;
                display: block;
            }
            .tool-name {
                font-size: 1.3rem;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .tool-stats {
                font-size: 0.9rem;
                color: #cccccc;
            }
            .nav-buttons {
                position: fixed;
                top: 20px;
                right: 20px;
                display: flex;
                gap: 10px;
                z-index: 1000;
            }
            .nav-btn {
                padding: 12px 20px;
                border-radius: 10px;
                text-decoration: none;
                font-weight: bold;
                transition: 0.3s;
                border: 2px solid;
            }
            .logout-btn {
                background: #ff4444;
                color: white;
                border-color: #ff0000;
            }
            .logout-btn:hover {
                background: #ff0000;
                transform: scale(1.1);
            }
            .admin-btn {
                background: #ffcc00;
                color: black;
                border-color: #ffaa00;
            }
            .admin-btn:hover {
                background: #ffaa00;
                transform: scale(1.1);
            }
            .chat-btn {
                background: #00ff00;
                color: black;
                border-color: #00cc00;
            }
            .chat-btn:hover {
                background: #00cc00;
                transform: scale(1.1);
            }
            .chat-box {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 350px;
                height: 400px;
                background: rgba(0, 0, 0, 0.9);
                border: 2px solid #00ffff;
                border-radius: 15px;
                display: none;
                flex-direction: column;
                z-index: 1001;
                box-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
            }
            .chat-header {
                background: rgba(0, 255, 255, 0.2);
                padding: 15px;
                border-radius: 13px 13px 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .chat-messages {
                flex: 1;
                padding: 15px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .message {
                padding: 10px 15px;
                border-radius: 10px;
                max-width: 80%;
                word-wrap: break-word;
            }
            .message.user {
                background: rgba(0, 255, 255, 0.3);
                align-self: flex-end;
                border: 1px solid #00ffff;
            }
            .message.admin {
                background: rgba(255, 204, 0, 0.3);
                align-self: flex-start;
                border: 1px solid #ffcc00;
            }
            .message-header {
                font-size: 0.7rem;
                opacity: 0.8;
                margin-bottom: 3px;
                display: flex;
                justify-content: space-between;
            }
            .chat-input {
                display: flex;
                padding: 15px;
                gap: 10px;
            }
            .chat-input input {
                flex: 1;
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #00ffff;
                background: rgba(0,0,0,0.7);
                color: white;
            }
            .chat-input button {
                padding: 10px 15px;
                border-radius: 8px;
                border: none;
                background: #00ffff;
                color: black;
                cursor: pointer;
                font-weight: bold;
            }
            .close-chat {
                background: none;
                border: none;
                color: white;
                font-size: 1.2rem;
                cursor: pointer;
            }
            .task-summary {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 15px;
                margin: 20px 0;
                padding: 0 30px;
                max-width: 1400px;
                margin: 20px auto;
            }
            .task-item {
                background: rgba(0, 0, 0, 0.6);
                padding: 15px;
                border-radius: 10px;
                border: 1px solid #00ffff;
                text-align: center;
                backdrop-filter: blur(5px);
            }
            .task-remaining {
                font-size: 1.5rem;
                font-weight: bold;
                color: #00ff00;
                text-shadow: 0 0 10px #00ff00;
            }
            .task-used {
                font-size: 0.9rem;
                color: #cccccc;
            }
            footer {
                text-align: center;
                padding: 20px;
                margin-top: 40px;
                background: rgba(0, 0, 0, 0.8);
                border-top: 1px solid #00ffff;
            }
        </style>
    </head>
    <body>
        <div class="nav-buttons">
            {% if 'admin' in permissions %}
            <a href="/admin" class="nav-btn admin-btn">👑 Admin</a>
            {% endif %}
            <a href="#" class="nav-btn chat-btn" onclick="toggleChat()">💬 Chat với Admin</a>
            <a href="/logout" class="nav-btn logout-btn">🚪 Logout</a>
        </div>

        <div class="header">
            <div class="user-info">
                <div class="avatar"></div>
                <div class="user-details">
                    <div class="welcome-text">🎉 Chào Mừng Đến Với Web by XuanThang w Ducdai</div>
                    <div class="subtitle">⚡ "HW LA CAI CN ME MAY AK =)))=)))" ⚡</div>
                </div>
            </div>
            
            <div class="key-display">
                <strong>🔑 Key:</strong> {{ session.key }} | 
                <strong>⏰ Đăng nhập lúc:</strong> {{ session.login_time }} | 
                <strong>📅 Thời hạn:</strong> {{ expire if expire else "Vĩnh viễn" }}
            </div>

            <div class="task-summary">
                {% for tool in ['treongo', 'nhaydz', 'so', 'two_c', 'rename', 'dis1', 'dis2', 'dis3', 'dis4', 'dis5'] %}
                <div class="task-item">
                    <div class="tool-name">{{ tool_names.get(tool, tool) }}</div>
                    <div class="task-remaining">{{ remaining_tasks[tool] }}</div>
                    <div class="task-used">/ {{ task_limits[tool] }} task</div>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="task-grid">
            {% for tool in ['treongo', 'nhaydz', 'so', 'two_c', 'rename', 'dis1', 'dis2', 'dis3', 'dis4', 'dis5'] %}
            <a href="/{{ tool }}" class="tool-card {{ tool }} {{ 'disabled' if tool not in permissions or remaining_tasks[tool] <= 0 else '' }}">
                <span class="tool-icon">
                    {% if tool == 'treongo' %}🔮
                    {% elif tool == 'nhaydz' %}🎭
                    {% elif tool == 'so' %}🔢
                    {% elif tool == 'two_c' %}🔄
                    {% elif tool == 'rename' %}📝
                    {% elif tool == 'dis1' %}💬
                    {% elif tool == 'dis2' %}⚡
                    {% elif tool == 'dis3' %}🎯
                    {% elif tool == 'dis4' %}💎
                    {% elif tool == 'dis5' %}🏠
                    {% endif %}
                </span>
                <div class="tool-name">{{ tool_names.get(tool, tool) }}</div>
                <div class="tool-stats">{{ remaining_tasks[tool] }}/{{ task_limits[tool] }} task</div>
            </a>
            {% endfor %}
        </div>

        <div class="chat-box" id="chatBox">
            <div class="chat-header">
                <strong>💬 Chat với Admin</strong>
                <button class="close-chat" onclick="toggleChat()">×</button>
            </div>
            <div class="chat-messages" id="chatMessages">
                <!-- Chat messages will be loaded here -->
            </div>
            <div class="chat-input">
                <input type="text" id="chatInput" placeholder="Nhập tin nhắn cho admin...">
                <button onclick="sendMessage()">Gửi</button>
            </div>
        </div>

        <footer>
            <div>© 2025 ❄️ XuanThang System - "Where Legends Are Born" 🌠</div>
            <div style="margin-top: 10px; font-size: 0.9rem; color: #ff00ff;">
                ⚡ Powered by Advanced Technology • 🔥 Built for Champions
            </div>
        </footer>

        <script>
            function toggleChat() {
                const chatBox = document.getElementById('chatBox');
                chatBox.style.display = chatBox.style.display === 'flex' ? 'none' : 'flex';
                if (chatBox.style.display === 'flex') {
                    loadChatMessages();
                }
            }

            function loadChatMessages() {
                fetch('/get_chat')
                    .then(response => response.json())
                    .then(messages => {
                        const chatMessages = document.getElementById('chatMessages');
                        chatMessages.innerHTML = '';
                        messages.forEach(msg => {
                            const messageDiv = document.createElement('div');
                            messageDiv.className = `message ${msg.sender}`;
                            messageDiv.innerHTML = `
                                <div class="message-header">
                                    <strong>${msg.sender_name}</strong>
                                    <span>${msg.time}</span>
                                </div>
                                <div>${msg.text}</div>
                            `;
                            chatMessages.appendChild(messageDiv);
                        });
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    });
            }

            function sendMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                if (message) {
                    fetch('/send_chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ message: message })
                    }).then(() => {
                        input.value = '';
                        loadChatMessages();
                    });
                }
            }

            // Auto refresh chat every 3 seconds when chat is open
            setInterval(() => {
                if (document.getElementById('chatBox').style.display === 'flex') {
                    loadChatMessages();
                }
            }, 3000);

            // Enter key to send message
            document.getElementById('chatInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """, expire=expire, permissions=permissions, task_limits=task_limits, remaining_tasks=remaining_tasks, tool_names=tool_names)

# ======= ĐĂNG XUẤT =======
@app.route('/logout')
def logout():
    session.pop('key', None)
    session.pop('admin', None)
    session.pop('permissions', None)
    session.pop('task_limits', None)
    session.pop('login_time', None)
    return redirect(url_for('login'))

# ======= API CHO CÁC TOOL SỬ DỤNG =======
@app.route('/api/use_task/<tool_type>', methods=['POST'])
def api_use_task(tool_type):
    if 'key' not in session:
        return {"success": False, "message": "Chưa đăng nhập"}, 401
    
    key = session['key']
    if key not in KEYS:
        return {"success": False, "message": "Key không hợp lệ"}, 403
    
    remaining = use_task(key, tool_type)
    return {
        "success": True, 
        "remaining_tasks": remaining,
        "message": f"Đã sử dụng 1 task. Còn lại: {remaining}"
    }

@app.route('/api/check_tasks/<tool_type>')
def api_check_tasks(tool_type):
    if 'key' not in session:
        return {"success": False, "message": "Chưa đăng nhập"}, 401
    
    key = session['key']
    if key not in KEYS:
        return {"success": False, "message": "Key không hợp lệ"}, 403
    
    remaining = get_remaining_tasks(key, tool_type)
    return {
        "success": True, 
        "remaining_tasks": remaining
    }

# ======= CÁC BLUEPRINT KHÁC =======
try:
    from tool_treongo import treongo_bp
    from nhaydz import nhaydz_bp
    from so import so_bp
    from two_c_bp import two_c_bp
    from rename import rename_bp
    from dis1 import dis1_bp

    # Import các blueprint mới
    from dis2 import dis2_bp
    from dis3 import dis3_bp
    from dis4 import dis4_bp
    from dis5 import dis5_bp

    # Đăng ký blueprint với URL prefix
    app.register_blueprint(treongo_bp, url_prefix='/treongo')
    app.register_blueprint(nhaydz_bp, url_prefix='/nhaydz')
    app.register_blueprint(so_bp, url_prefix='/so')
    app.register_blueprint(two_c_bp, url_prefix='/two_c')
    app.register_blueprint(rename_bp, url_prefix='/rename')
    app.register_blueprint(dis1_bp, url_prefix='/dis1')
    app.register_blueprint(dis2_bp, url_prefix='/dis2')
    app.register_blueprint(dis3_bp, url_prefix='/dis3')
    app.register_blueprint(dis4_bp, url_prefix='/dis4')
    app.register_blueprint(dis5_bp, url_prefix='/dis5')
    
    print("✅ Đã tải tất cả các blueprint công cụ")
except ImportError as e:
    print(f"⚠️ Có lỗi khi tải blueprint: {e}")
    print("⚠️ Một số công cụ có thể không hoạt động")

if __name__ == "__main__":
    print("🌐 Web chạy tại: http://127.0.0.1:5000")
    print("⚡ XuanThang System - Where Legends Are Born!")
    print("💾 Hệ thống lưu trữ key đã được kích hoạt!")
    app.run(host="0.0.0.0", port=5000, debug=True)
