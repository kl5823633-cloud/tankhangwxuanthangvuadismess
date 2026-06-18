from flask import Blueprint, render_template_string, request, flash, redirect, url_for
import requests
import time
import threading
from datetime import datetime
import os

# Tạo blueprint
dis1_bp = Blueprint('dis1', __name__)

# Các biến toàn cục cho blueprint
tasks = {}
task_id_counter = 1

# HTML TEMPLATE cho Discord Spammer
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Discord - Spam File Content với Fake Typing</title>
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
            color: #5865f2;
            text-align: center;
            margin-bottom: 20px;
            font-size: 2rem;
            text-shadow: 0 0 10px rgba(88, 101, 242, 0.5);
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
            background: linear-gradient(135deg, #5865f2, #4752c4);
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
            box-shadow: 0 4px 15px rgba(88, 101, 242, 0.3);
        }
        
        button:hover {
            background: linear-gradient(135deg, #4752c4, #3c45a5);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(88, 101, 242, 0.4);
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
        
        .file-upload {
            border: 2px dashed #5865f2;
            padding: 20px;
            text-align: center;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 15px;
        }
        
        .file-upload:hover {
            background: rgba(88, 101, 242, 0.1);
        }
        
        .file-upload input {
            display: none;
        }
        
        .file-name {
            margin-top: 10px;
            color: #58a6ff;
            font-weight: bold;
        }
        
        .file-preview {
            max-height: 150px;
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
            color: #58a6ff;
            font-style: italic;
        }
        
        .typing-dots {
            display: flex;
            margin-left: 5px;
        }
        
        .typing-dot {
            width: 6px;
            height: 6px;
            background-color: #58a6ff;
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
                box-shadow: 0 0 0 0 rgba(88, 101, 242, 0.7);
            }
            70% {
                box-shadow: 0 0 0 10px rgba(88, 101, 242, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(88, 101, 242, 0);
            }
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>📁TREO NGÔN DISCORD</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for cat, msg in messages %}
                    <div class="alert alert-{{cat}}">{{msg}}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="POST" action="{{ url_for('dis1.add_task') }}" enctype="multipart/form-data">
            <label>Token Discord:</label>
            <input type="password" name="token" placeholder="Nhập token Discord..." required>

            <label>Channel ID:</label>
            <input type="text" name="channel_id" placeholder="Nhập Channel ID..." required>

            <label>Upload file .txt:</label>
            <div class="file-upload" onclick="document.getElementById('fileInput').click()">
                <div>📁 Click để chọn file .txt</div>
                <div class="file-name" id="fileName">Chưa chọn file</div>
                <input type="file" id="fileInput" name="file" accept=".txt" required onchange="updateFileName(this)">
            </div>

            <div id="filePreviewContainer" style="display: none;">
                <label>Xem trước nội dung file:</label>
                <div class="file-preview" id="filePreview"></div>
            </div>

            <label>⏱ Delay giữa mỗi lần gửi (giây):</label>
            <input type="number" name="delay" value="5" min="1" step="0.1" required>

            <label>Thời gian fake typing (giây):</label>
            <input type="number" name="typing_duration" value="3" min="1" max="10" step="0.1" required>

            <button type="submit" class="pulse">🚀 Bắt đầu spam với fake typing</button>
        </form>
    </div>

    <table>
        <tr>
            <th>ID</th>
            <th>Channel</th>
            <th>File</th>
            <th>Đã gửi</th>
            <th>Delay</th>
            <th>Typing</th>
            <th>Trạng thái</th>
            <th>Hành động</th>
        </tr>
        {% for tid, t in tasks.items() %}
        <tr>
            <td>{{ tid }}</td>
            <td>{{ t.channel_id }}</td>
            <td>{{ t.filename }}</td>
            <td>{{ t.sent_count }}</td>
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
            <td>
                {% if t.running %}
                    <a href="{{ url_for('dis1.stop_task', task_id=tid) }}"><button class="action-btn btn-stop">🛑 Dừng</button></a>
                {% else %}
                    <a href="{{ url_for('dis1.start_task_route', task_id=tid) }}"><button class="action-btn btn-start">▶️ Chạy</button></a>
                {% endif %}
                <a href="{{ url_for('dis1.delete_task', task_id=tid) }}"><button class="action-btn btn-delete">🗑️ Xóa</button></a>
            </td>
        </tr>
        {% endfor %}
    </table>

    <div class="center">
        <a href="/menu" class="back-btn">⬅️ Quay về Menu Chính</a>
    </div>

    <script>
        function updateFileName(input) {
            const fileName = input.files[0] ? input.files[0].name : 'Chưa chọn file';
            document.getElementById('fileName').textContent = fileName;
            
            if (input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const content = e.target.result;
                    document.getElementById('filePreview').textContent = content;
                    document.getElementById('filePreviewContainer').style.display = 'block';
                };
                reader.readAsText(input.files[0]);
            } else {
                document.getElementById('filePreviewContainer').style.display = 'none';
            }
        }
    </script>
</body>
</html>
'''

def send_discord_message(token, channel_id, message):
    """Gửi tin nhắn Discord"""
    try:
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        data = {"content": message, "tts": False, "flags": 0}
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code in [200, 201, 204]:
            return True, "Gửi thành công"
        elif response.status_code == 429:
            retry_after = response.json().get('retry_after', 1)
            time.sleep(retry_after)
            return send_discord_message(token, channel_id, message)
        else:
            return False, f"Lỗi {response.status_code}"
            
    except Exception as e:
        return False, f"Lỗi: {str(e)}"

def start_typing_indicator(token, channel_id):
    """Bật indicator đang soạn tin nhắn"""
    try:
        typing_url = f"https://discord.com/api/v9/channels/{channel_id}/typing"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.post(typing_url, headers=headers, timeout=5)
        return response.status_code in [200, 204]
    except:
        return False

def spam_file_worker(task_id):
    """Worker function để spam nội dung file với fake typing"""
    task = tasks[task_id]
    
    try:
        task['running'] = True
        task['start_time'] = datetime.now().strftime("%H:%M:%S")
        
        count = 0
        
        while task['running']:
            try:
                # Bật typing indicator
                task['is_typing'] = True
                task['last_log'] = "⌨️ Đang soạn tin nhắn..."
                
                # Giữ typing indicator trong khoảng thời gian chỉ định
                typing_start = time.time()
                while time.time() - typing_start < task['typing_duration'] and task['running']:
                    start_typing_indicator(task['token'], task['channel_id'])
                    time.sleep(1)
                
                # Tắt typing indicator
                task['is_typing'] = False
                
                # Gửi tin nhắn
                success, result = send_discord_message(
                    task['token'], 
                    task['channel_id'], 
                    task['file_content']
                )
                
                if success:
                    count += 1
                    task['sent_count'] = count
                    task['last_log'] = f"✅ [{count}] Đã gửi file content"
                else:
                    task['last_log'] = f"❌ {result}"
                
                # Lưu log
                task['logs'].append({
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'message': task['last_log'],
                    'success': success
                })
                
                # Giữ log tối đa 50 dòng
                if len(task['logs']) > 50:
                    task['logs'] = task['logs'][-50:]
                
                # Delay giữa các lần gửi
                if task['running']:
                    time.sleep(task['delay'])
                
            except Exception as e:
                task['is_typing'] = False
                task['last_log'] = f"⚠️ Lỗi: {str(e)}"
                task['logs'].append({
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'message': task['last_log'],
                    'success': False
                })
                if task['running']:
                    time.sleep(task['delay'])
                
    except Exception as e:
        task['is_typing'] = False
        task['last_log'] = f"💥 Lỗi hệ thống: {str(e)}"
        task['logs'].append({
            'time': datetime.now().strftime("%H:%M:%S"),
            'message': task['last_log'],
            'success': False
        })
    finally:
        task['running'] = False
        task['is_typing'] = False

# Routes của blueprint - SỬA LẠI CÁC ROUTE
@dis1_bp.route('/')
def dis1_page():
    return render_template_string(HTML_TEMPLATE, tasks=tasks)

@dis1_bp.route('/add_task', methods=['POST'])
def add_task():
    global task_id_counter
    
    try:
        token = request.form.get('token', '').strip()
        channel_id = request.form.get('channel_id', '').strip()
        delay = float(request.form.get('delay', 5))
        typing_duration = float(request.form.get('typing_duration', 3))
        
        if not token or not channel_id:
            flash('Vui lòng điền đầy đủ token và channel ID', 'error')
            return redirect(url_for('dis1.dis1_page'))
        
        if 'file' not in request.files:
            flash('Vui lòng chọn file .txt', 'error')
            return redirect(url_for('dis1.dis1_page'))
        
        file = request.files['file']
        if file.filename == '':
            flash('Vui lòng chọn file .txt', 'error')
            return redirect(url_for('dis1.dis1_page'))
        
        if file and file.filename.endswith('.txt'):
            # Đọc nội dung file
            try:
                file_content = file.read().decode('utf-8').strip()
                if not file_content:
                    flash('File .txt trống', 'error')
                    return redirect(url_for('dis1.dis1_page'))
            except Exception as e:
                flash(f'Lỗi đọc file: {str(e)}', 'error')
                return redirect(url_for('dis1.dis1_page'))
            
            # Tạo task mới
            task_id = task_id_counter
            task_id_counter += 1
            
            task = {
                'id': task_id,
                'token': token,
                'channel_id': channel_id,
                'file_content': file_content,
                'filename': file.filename,
                'delay': delay,
                'typing_duration': typing_duration,
                'running': False,
                'is_typing': False,
                'sent_count': 0,
                'start_time': '',
                'last_log': '',
                'logs': [],
                'thread': None
            }
            
            tasks[task_id] = task
            
            # Bắt đầu task
            start_task(task_id)
            
            flash(f'🚀 Đã tạo task #{task_id} với fake typing!', 'success')
            
        else:
            flash('Vui lòng chọn file .txt hợp lệ', 'error')
        
    except Exception as e:
        flash(f'Lỗi khi tạo task: {str(e)}', 'error')
    
    return redirect(url_for('dis1.dis1_page'))

def start_task(task_id):
    """Bắt đầu task"""
    if task_id not in tasks:
        return False
    
    task = tasks[task_id]
    
    if task['running']:
        return True
    
    task['running'] = True
    task['is_typing'] = False
    
    # Tạo thread mới
    thread = threading.Thread(target=spam_file_worker, args=(task_id,))
    thread.daemon = True
    thread.start()
    
    task['thread'] = thread
    return True

@dis1_bp.route('/start/<int:task_id>')
def start_task_route(task_id):
    if start_task(task_id):
        flash(f'Đã tiếp tục task #{task_id}', 'success')
    else:
        flash('Không tìm thấy task', 'error')
    return redirect(url_for('dis1.dis1_page'))

@dis1_bp.route('/stop/<int:task_id>')
def stop_task(task_id):
    if task_id in tasks:
        tasks[task_id]['running'] = False
        tasks[task_id]['is_typing'] = False
        flash(f'Đã dừng task #{task_id}', 'success')
    else:
        flash('Không tìm thấy task', 'error')
    return redirect(url_for('dis1.dis1_page'))

@dis1_bp.route('/delete/<int:task_id>')
def delete_task(task_id):
    if task_id in tasks:
        tasks[task_id]['running'] = False
        tasks[task_id]['is_typing'] = False
        del tasks[task_id]
        flash(f'Đã xóa task #{task_id}', 'success')
    else:
        flash('Không tìm thấy task', 'error')
    return redirect(url_for('dis1.dis1_page'))
