from flask import Blueprint, render_template_string, request, jsonify, flash, redirect, url_for
import requests
import time
import threading
import os
import uuid

dis4_bp = Blueprint('dis4', __name__)

# Dictionary để lưu trữ các task
tasks = {}

# ======= CÁC HÀM DISCORD =======
def fake_typing(token, channel_id, duration=3):
    """Hàm fake typing với thời gian tùy chỉnh"""
    try:
        url = f"https://discord.com/api/v9/channels/{channel_id}/typing"
        headers = {"Authorization": token}
        
        # Bắt đầu typing
        requests.post(url, headers=headers, timeout=5)
        
        # Giữ typing trong khoảng thời gian chỉ định
        time.sleep(duration)
        
    except:
        pass

def send_message(token, channel_id, content):
    """Gửi tin nhắn bình thường"""
    try:
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        payload = {"content": content}
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if res.status_code == 200:
            print(f"💬 Đã gửi: {content}")
            return True
        return False
    except:
        return False

def create_thread_from_message(token, channel_id, message_id, thread_name, auto_archive_duration=1440):
    """Tạo thread từ message ID"""
    try:
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/threads"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        payload = {
            "name": thread_name,
            "auto_archive_duration": auto_archive_duration
        }
        
        # Fake typing trước khi tạo thread
        fake_typing(token, channel_id, 2)
        
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if res.status_code == 201:
            thread_data = res.json()
            thread_id = thread_data["id"]
            print(f"✅ Đã tạo thread: '{thread_name}' (ID: {thread_id})")
            return thread_id
        else:
            print(f"❌ Lỗi tạo thread: {res.status_code} - {res.text}")
            return None
    except Exception as e:
        print(f"❌ Lỗi tạo thread: {e}")
        return None

def create_thread_in_channel(token, channel_id, thread_name, auto_archive_duration=1440):
    """Tạo thread trực tiếp trong channel"""
    try:
        url = f"https://discord.com/api/v9/channels/{channel_id}/threads"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        payload = {
            "name": thread_name,
            "type": 11,  # PUBLIC_THREAD
            "auto_archive_duration": auto_archive_duration
        }
        
        # Fake typing trước khi tạo thread
        fake_typing(token, channel_id, 2)
        
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if res.status_code == 201:
            thread_data = res.json()
            thread_id = thread_data["id"]
            print(f"✅ Đã tạo thread: '{thread_name}' (ID: {thread_id})")
            return thread_id
        else:
            print(f"❌ Lỗi tạo thread: {res.status_code} - {res.text}")
            return None
    except Exception as e:
        print(f"❌ Lỗi tạo thread: {e}")
        return None

def send_message_in_thread(token, thread_id, content):
    """Gửi tin nhắn trong thread"""
    try:
        url = f"https://discord.com/api/v9/channels/{thread_id}/messages"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        payload = {"content": content}
        
        # Fake typing trong thread
        fake_typing(token, thread_id, 2)
        
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if res.status_code == 200:
            print(f"💬 Đã gửi trong thread: {content}")
            return True
        else:
            print(f"❌ Lỗi gửi trong thread: {res.status_code}")
            return False
    except Exception as e:
        print(f"❌ Lỗi gửi trong thread: {e}")
        return False

def read_chui_file():
    """Đọc nội dung từ file chui.txt"""
    try:
        if not os.path.exists('chui.txt'):
            return None, "File chui.txt không tồn tại"
        
        with open('chui.txt', 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        if not content:
            return None, "File chui.txt trống"
            
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return lines, None
        
    except Exception as e:
        return None, f"Lỗi đọc file: {str(e)}"

def spam_multiple_threads_task(task_id, token, channel_id, message_id, delay, typing_duration):
    """Hàm chính để tạo nhiều thread, mỗi thread chỉ gửi 1 câu"""
    task = tasks.get(task_id)
    if not task:
        return
    
    # Đọc nội dung từ file chui.txt
    lines, error = read_chui_file()
    if error:
        print(f"❌ {error}")
        task['running'] = False
        task['error'] = error
        return
    
    task['running'] = True
    task['sent_count'] = 0
    task['total_lines'] = len(lines)
    task['error'] = None
    
    try:
        # Tạo thread cho từng dòng trong file
        for i, message in enumerate(lines):
            if not task['running']:
                break
                
            # Tạo tên thread từ nội dung (giới hạn độ dài 100 ký tự theo Discord)
            thread_name = message[:100]
            
            # Tạo thread
            task['is_typing'] = True
            task['last_action'] = f"🔄 Đang tạo thread {i+1}/{len(lines)}: {thread_name}"
            
            thread_id = None
            if message_id:
                # Tạo thread từ message
                thread_id = create_thread_from_message(token, channel_id, message_id, thread_name)
            else:
                # Tạo thread trực tiếp trong channel
                thread_id = create_thread_in_channel(token, channel_id, thread_name)
            
            task['is_typing'] = False
            
            if not thread_id:
                task['error'] = f"Không thể tạo thread {i+1}"
                task['last_action'] = f"❌ Lỗi tạo thread {i+1}"
                continue
            
            task['thread_id'] = thread_id
            task['last_action'] = f"✅ Đã tạo thread {i+1}: {thread_name}"
            
            # Gửi tin nhắn trong thread (tag everyone + nội dung)
            final_message = f"@everyone {message}"
            if send_message_in_thread(token, thread_id, final_message):
                task['sent_count'] += 1
                task['last_action'] = f"💬 Đã gửi trong thread {i+1}"
                print(f"✅ Đã tạo và gửi trong thread {i+1}/{len(lines)}: {message}")
            else:
                task['last_action'] = f"❌ Lỗi gửi trong thread {i+1}"
                print(f"❌ Lỗi gửi trong thread {i+1}")
            
            # Delay giữa các thread (trừ thread cuối)
            if i < len(lines) - 1 and task['running']:
                task['last_action'] = f"⏳ Đang delay {delay}s trước khi tạo thread tiếp theo..."
                for j in range(int(delay)):
                    if not task['running']:
                        break
                    time.sleep(1)
                    
        task['last_action'] = f"✅ Đã hoàn thành tạo {task['sent_count']}/{len(lines)} thread"
        
    except Exception as e:
        print(f"❌ Lỗi trong task: {e}")
        task['error'] = str(e)
    
    task['running'] = False
    task['is_typing'] = False

# ======= ROUTES DIS4 =======
@dis4_bp.route('/')
def dis4_page():
    # Kiểm tra file chui.txt
    chui_exists = os.path.exists('chui.txt')
    chui_info = ""
    
    if chui_exists:
        try:
            with open('chui.txt', 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                chui_info = f"✅ Đã tìm thấy ({len(lines)} dòng)"
        except:
            chui_info = "✅ Đã tìm thấy (lỗi đọc file)"
    else:
        chui_info = "❌ Không tìm thấy file chui.txt"
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>💎 TẠO NHIỀU THREAD & SPAM - XuanThang System</title>
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
            color: #6b6bff;
            text-align: center;
            margin-bottom: 20px;
            font-size: 2rem;
            text-shadow: 0 0 10px rgba(107, 107, 255, 0.5);
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
            border-color: #6b6bff;
            box-shadow: 0 0 0 2px rgba(107, 107, 255, 0.2);
        }
        
        button {
            background: linear-gradient(135deg, #6b6bff, #5757e5);
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
            box-shadow: 0 4px 15px rgba(107, 107, 255, 0.3);
        }
        
        button:hover {
            background: linear-gradient(135deg, #5757e5, #4a4ac7);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(107, 107, 255, 0.4);
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
            color: #6b6bff;
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
            background: linear-gradient(135deg, #3fb950, #2ea043);
            box-shadow: 0 3px 10px rgba(63, 185, 80, 0.3);
        }
        
        .btn-start:hover {
            background: linear-gradient(135deg, #2ea043, #238636);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(46, 160, 67, 0.4);
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
        
        .file-info {
            background: rgba(107, 107, 255, 0.2);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
            border: 1px solid #6b6bff;
            text-align: center;
        }
        
        .file-preview {
            max-height: 200px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 10px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 12px;
            white-space: pre-wrap;
        }
        
        .typing-indicator {
            display: flex;
            align-items: center;
            margin-top: 10px;
            color: #6b6bff;
            font-style: italic;
        }
        
        .typing-dots {
            display: flex;
            margin-left: 5px;
        }
        
        .typing-dot {
            width: 6px;
            height: 6px;
            background-color: #6b6bff;
            border-radius: 50%;
            margin: 0 2px;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(1) {
            animation-delay: 0s;
        }
        
        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-5px);
            }
        }
        
        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(107, 107, 255, 0.7);
            }
            70% {
                box-shadow: 0 0 0 10px rgba(107, 107, 255, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(107, 107, 255, 0);
            }
        }
        
        .instructions {
            background: rgba(107, 107, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            border: 1px solid #6b6bff;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>💎 TẠO NHIỀU THREAD & SPAM</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for cat, msg in messages %}
                    <div class="alert alert-{{cat}}">{{msg}}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="instructions">
            <h3>📖 Hướng dẫn sử dụng:</h3>
            <p>• Tool sẽ tạo <strong>NHIỀU THREAD</strong> - mỗi dòng trong file chui.txt sẽ tạo 1 thread</p>
            <p>• <strong>Tên thread sẽ được lấy tự động từ nội dung mỗi dòng trong file chui.txt</strong></p>
            <p>• Trong mỗi thread chỉ gửi <strong>1 TIN NHẮN DUY NHẤT</strong> với nội dung: @everyone + nội dung dòng</p>
            <p>• Nếu có Message ID: tạo thread từ tin nhắn đó</p>
            <p>• Nếu không có Message ID: tạo thread trực tiếp trong channel</p>
        </div>
        
        <div class="file-info">
            <strong>📁 File chui.txt:</strong> {{ chui_info }}
            {% if chui_exists %}
            <div style="margin-top: 10px;">
                <button onclick="showFilePreview()" style="background: rgba(0,0,0,0.3); padding: 8px 15px; border: 1px solid #6b6bff; border-radius: 5px; color: #6b6bff; cursor: pointer;">
                    👁️ Xem nội dung file
                </button>
            </div>
            <div id="filePreviewContainer" style="display: none; margin-top: 15px;">
                <div class="file-preview" id="filePreview">
                    {% if chui_content %}
                        {{ chui_content }}
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
        
        <form method="POST" action="{{ url_for('dis4.add_task') }}">
            <label>🔑 Token Discord:</label>
            <input type="password" name="token" placeholder="Nhập token Discord..." required>

            <label>📝 Channel ID:</label>
            <input type="text" name="channel_id" placeholder="Nhập Channel ID..." required>

            <label>💬 Message ID (để tạo thread từ tin nhắn - tùy chọn):</label>
            <input type="text" name="message_id" placeholder="Nhập Message ID (để trống nếu tạo thread trực tiếp)...">

            <label>⏱ Delay giữa mỗi thread (giây):</label>
            <input type="number" name="delay" value="5" min="1" step="0.1" required>

            <label>⌨️ Thời gian fake typing (giây):</label>
            <input type="number" name="typing_duration" value="3" min="1" max="10" step="0.1" required>

            <button type="submit" class="pulse" {% if not chui_exists %}disabled title="File chui.txt không tồn tại"{% endif %}>
                🚀 Tạo Nhiều Thread & Spam
            </button>
            
            {% if not chui_exists %}
            <div class="alert alert-error" style="margin-top: 10px;">
                ⚠️ Vui lòng tạo file <strong>chui.txt</strong> trong thư mục chứa code
            </div>
            {% endif %}
        </form>
    </div>

    <table>
        <tr>
            <th>ID</th>
            <th>Channel</th>
            <th>Message ID</th>
            <th>Đã tạo</th>
            <th>Delay</th>
            <th>Typing</th>
            <th>Trạng thái</th>
            <th>Hành động cuối</th>
            <th>Hành động</th>
        </tr>
        {% for tid, t in tasks.items() %}
        <tr>
            <td>{{ tid[:8] }}...</td>
            <td>{{ t.channel_id }}</td>
            <td>{{ t.message_id if t.message_id else "Tạo trực tiếp" }}</td>
            <td>
                {% if t.error %}
                <span style="color: #f85149;">❌ {{ t.error }}</span>
                {% else %}
                {{ t.sent_count }}/{{ t.total_lines if t.total_lines else '?' }} thread
                {% endif %}
            </td>
            <td>{{ t.delay }}s</td>
            <td>{{ t.typing_duration }}s</td>
            <td>
                {% if t.running %}
                    <span class="status-running">🟢 Đang chạy</span>
                    {% if t.is_typing %}
                    <div class="typing-indicator">
                        Đang soạn...
                        <div class="typing-dots">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                    </div>
                    {% endif %}
                {% else %}
                    <span class="status-stopped">🔴 Đã dừng</span>
                {% endif %}
            </td>
            <td style="max-width: 200px; word-wrap: break-word;">
                {{ t.last_action if t.last_action else 'Chưa có' }}
            </td>
            <td>
                {% if t.running %}
                    <a href="{{ url_for('dis4.stop_task', task_id=tid) }}"><button class="action-btn btn-stop">🛑 Dừng</button></a>
                {% else %}
                    <a href="{{ url_for('dis4.start_task_route', task_id=tid) }}"><button class="action-btn btn-start">▶️ Chạy</button></a>
                {% endif %}
                <a href="{{ url_for('dis4.delete_task', task_id=tid) }}"><button class="action-btn btn-delete">🗑️ Xóa</button></a>
            </td>
        </tr>
        {% endfor %}
    </table>

    <div class="center">
        <a href="/menu" class="back-btn">⬅️ Quay về Menu Chính</a>
    </div>

    <script>
        function showFilePreview() {
            const container = document.getElementById('filePreviewContainer');
            if (container.style.display === 'none') {
                container.style.display = 'block';
                // Load nội dung file nếu chưa có
                if (!document.getElementById('filePreview').textContent.trim()) {
                    fetch('/dis4/get_file_content')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                document.getElementById('filePreview').textContent = data.content;
                            } else {
                                document.getElementById('filePreview').textContent = 'Lỗi: ' + data.error;
                            }
                        });
                }
            } else {
                container.style.display = 'none';
            }
        }
    </script>
</body>
</html>
    ''', tasks=tasks, chui_exists=chui_exists, chui_info=chui_info)

@dis4_bp.route('/get_file_content')
def get_file_content():
    """API lấy nội dung file chui.txt"""
    try:
        if os.path.exists('chui.txt'):
            with open('chui.txt', 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'success': True, 'content': content})
        else:
            return jsonify({'success': False, 'error': 'File không tồn tại'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@dis4_bp.route('/add_task', methods=['POST'])
def add_task():
    """Thêm task mới"""
    try:
        token = request.form.get('token')
        channel_id = request.form.get('channel_id')
        message_id = request.form.get('message_id', '').strip()
        delay = float(request.form.get('delay', 5))
        typing_duration = float(request.form.get('typing_duration', 3))
        
        # Kiểm tra file chui.txt
        if not os.path.exists('chui.txt'):
            flash('❌ File chui.txt không tồn tại!', 'error')
            return redirect(url_for('dis4.dis4_page'))
        
        # Tạo task mới
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            'token': token,
            'channel_id': channel_id,
            'message_id': message_id,
            'delay': delay,
            'typing_duration': typing_duration,
            'running': False,
            'is_typing': False,
            'sent_count': 0,
            'total_lines': 0,
            'error': None,
            'last_action': 'Chưa bắt đầu'
        }
        
        # Bắt đầu task
        thread = threading.Thread(
            target=spam_multiple_threads_task,
            args=(task_id, token, channel_id, message_id, delay, typing_duration)
        )
        thread.daemon = True
        thread.start()
        
        flash(f'✅ Đã tạo task {task_id[:8]}... và bắt đầu tạo nhiều thread!', 'success')
        
    except Exception as e:
        flash(f'❌ Lỗi: {str(e)}', 'error')
    
    return redirect(url_for('dis4.dis4_page'))

@dis4_bp.route('/start_task/<task_id>')
def start_task_route(task_id):
    """Bắt đầu lại task"""
    if task_id in tasks:
        task = tasks[task_id]
        if not task['running']:
            thread = threading.Thread(
                target=spam_multiple_threads_task,
                args=(
                    task_id,
                    task['token'],
                    task['channel_id'],
                    task['message_id'],
                    task['delay'],
                    task['typing_duration']
                )
            )
            thread.daemon = True
            thread.start()
            flash('✅ Đã khởi động lại task!', 'success')
        else:
            flash('⚠️ Task đang chạy!', 'error')
    else:
        flash('❌ Task không tồn tại!', 'error')
    
    return redirect(url_for('dis4.dis4_page'))

@dis4_bp.route('/stop_task/<task_id>')
def stop_task(task_id):
    """Dừng task"""
    if task_id in tasks:
        tasks[task_id]['running'] = False
        tasks[task_id]['last_action'] = '🛑 Đã dừng thủ công'
        flash('🛑 Đã dừng task!', 'success')
    else:
        flash('❌ Task không tồn tại!', 'error')
    
    return redirect(url_for('dis4.dis4_page'))

@dis4_bp.route('/delete_task/<task_id>')
def delete_task(task_id):
    """Xóa task"""
    if task_id in tasks:
        tasks[task_id]['running'] = False
        del tasks[task_id]
        flash('🗑️ Đã xóa task!', 'success')
    else:
        flash('❌ Task không tồn tại!', 'error')
    
    return redirect(url_for('dis4.dis4_page'))
