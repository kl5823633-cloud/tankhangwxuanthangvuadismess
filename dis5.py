from flask import Blueprint, render_template_string, request, jsonify, flash, redirect, url_for
import requests
import time
import threading
import uuid
import os
import json
from datetime import datetime

dis5_bp = Blueprint('dis5', __name__)

# Dictionary để lưu trữ các task treo room
room_tasks = {}

# Thư mục lưu file MP3
UPLOAD_FOLDER = 'voice_uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ======= CÁC HÀM DISCORD VOICE =======
def fetch_guild_id_for_channel(token, channel_id):
    """Lấy guild_id từ channel_id"""
    try:
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"https://discord.com/api/v9/channels/{channel_id}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            channel_data = response.json()
            return channel_data.get("guild_id")
        elif response.status_code == 404:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Channel not found (404)")
            return None
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to fetch channel info: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching guild ID: {e}")
        return None

def join_and_spam_voice(task_id, token, channel_id, mp3_file_path, volume_boost, interval, use_custom_audio, mute, deaf, stream):
    """Hàm chính để join voice và spam âm thanh"""
    task = room_tasks.get(task_id)
    if not task:
        return
    
    task['running'] = True
    task['status'] = "🟢 Đang treo room & spam voice"
    task['cycle_count'] = 0
    task['last_action'] = "Đang khởi tạo..."
    
    # Lấy guild_id
    guild_id = fetch_guild_id_for_channel(token, channel_id)
    if not guild_id:
        task['status'] = "🔴 Lỗi: Không lấy được Guild ID"
        task['running'] = False
        return
    
    task['guild_id'] = guild_id
    task['last_action'] = f"Đã lấy Guild ID: {guild_id}"
    
    while task['running']:
        try:
            # Simulate join voice channel
            task['last_action'] = f"Đang join voice channel..."
            
            if use_custom_audio and mp3_file_path and os.path.exists(mp3_file_path):
                # Sử dụng file MP3 custom
                if volume_boost > 1:
                    task['last_action'] = f"🔊 Đang phát FILE MP3 RÈ TO (x{volume_boost}) - Lần {task['cycle_count'] + 1}"
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔊 SPAM FILE MP3 RÈ TO - Volume: x{volume_boost}")
                else:
                    task['last_action'] = f"🔊 Đang phát file MP3 - Lần {task['cycle_count'] + 1}"
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔊 SPAM FILE MP3 - Volume: x{volume_boost}")
            else:
                # Chỉ rè to không cần file
                if volume_boost > 5:
                    task['last_action'] = f"💥 ĐANG RÈ TO TỐI ĐA (x{volume_boost}) - Lần {task['cycle_count'] + 1}"
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 💥 RÈ TO KHỦNG BỐ - Volume: x{volume_boost}")
                else:
                    task['last_action'] = f"🔊 Đang rè to (x{volume_boost}) - Lần {task['cycle_count'] + 1}"
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔊 RÈ TO - Volume: x{volume_boost}")
            
            # Tăng cycle count
            task['cycle_count'] += 1
            task['status'] = "🟢 Đang treo room & spam voice"
            
            # Chờ interval giây trước khi phát lại
            for i in range(interval):
                if not task['running']:
                    break
                time.sleep(1)
                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Lỗi trong spam voice: {e}")
            task['last_action'] = f"❌ Lỗi hệ thống: {str(e)}"
            time.sleep(5)
    
    task['status'] = "🔴 Đã dừng"
    task['last_action'] = "Đã dừng treo room"

def process_audio_file(file_path, volume_boost):
    """Xử lý file audio để tăng volume (simulate)"""
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Đang xử lý file audio - Tăng volume x{volume_boost}")
        
        # Trong thực tế, bạn sẽ dùng thư viện như pydub để xử lý audio
        # Ở đây chúng ta chỉ simulate việc xử lý
        processed_path = file_path
        
        # Ghi log để biết file đã được xử lý
        log_file = file_path + '.processed.log'
        with open(log_file, 'w') as f:
            f.write(f"Processed with volume boost: x{volume_boost}\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            
        return processed_path
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Lỗi xử lý audio: {e}")
        return file_path

# ======= ROUTES DIS5 =======
@dis5_bp.route('/')
def dis5_page():
    return render_template_string('''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>🏠 Treo Room & Spam Voice RÈ TO - XuanThang System</title>
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
            color: #ff6bff;
            text-align: center;
            margin-bottom: 20px;
            font-size: 2rem;
            text-shadow: 0 0 10px rgba(255, 107, 255, 0.5);
        }
        
        label {
            color: #58a6ff;
            display: block;
            margin-top: 15px;
            font-weight: 600;
        }
        
        input, select {
            width: 100%;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid #30363d;
            background: rgba(13, 17, 23, 0.7);
            color: white;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #ff6bff;
            box-shadow: 0 0 0 2px rgba(255, 107, 255, 0.2);
        }
        
        .checkbox-group {
            display: flex;
            gap: 20px;
            margin: 15px 0;
            flex-wrap: wrap;
        }
        
        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .checkbox-item input[type="checkbox"] {
            width: auto;
            transform: scale(1.2);
        }
        
        .file-upload {
            border: 2px dashed #ff6bff;
            padding: 20px;
            text-align: center;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 15px;
        }
        
        .file-upload:hover {
            background: rgba(255, 107, 255, 0.1);
        }
        
        .file-upload input {
            display: none;
        }
        
        .file-name {
            margin-top: 10px;
            color: #ff6bff;
            font-weight: bold;
        }
        
        .volume-slider {
            width: 100%;
            margin: 15px 0;
        }
        
        .volume-value {
            text-align: center;
            font-size: 1.2rem;
            font-weight: bold;
            color: #ff6bff;
            margin: 10px 0;
        }
        
        .volume-preview {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 10px 0;
        }
        
        .volume-bar {
            flex-grow: 1;
            height: 20px;
            background: linear-gradient(90deg, #00ff00, #ffff00, #ff4444);
            border-radius: 10px;
            margin: 0 10px;
            position: relative;
            overflow: hidden;
        }
        
        .volume-fill {
            height: 100%;
            background: rgba(255, 107, 255, 0.5);
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        button {
            background: linear-gradient(135deg, #ff6bff, #e055e0);
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
            box-shadow: 0 4px 15px rgba(255, 107, 255, 0.3);
        }
        
        button:hover {
            background: linear-gradient(135deg, #e055e0, #c43cc4);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 107, 255, 0.4);
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
            color: #ff6bff;
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
        
        .status-error {
            color: #ffcc00;
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
        
        .instructions {
            background: rgba(255, 107, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            border: 1px solid #ff6bff;
        }
        
        .mode-selector {
            display: flex;
            gap: 10px;
            margin: 15px 0;
        }
        
        .mode-btn {
            flex: 1;
            padding: 12px;
            border: 2px solid #ff6bff;
            border-radius: 8px;
            background: rgba(13, 17, 23, 0.7);
            color: #ff6bff;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .mode-btn.active {
            background: #ff6bff;
            color: white;
        }
        
        .mode-btn:hover {
            background: rgba(255, 107, 255, 0.2);
        }
        
        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(255, 107, 255, 0.7);
            }
            70% {
                box-shadow: 0 0 0 10px rgba(255, 107, 255, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(255, 107, 255, 0);
            }
        }
        
        .warning {
            color: #ffcc00;
            text-align: center;
            font-weight: bold;
            margin: 10px 0;
            text-shadow: 0 0 5px rgba(255, 204, 0, 0.5);
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>🏠 Treo Room & Spam Voice RÈ TO</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for cat, msg in messages %}
                    <div class="alert alert-{{cat}}">{{msg}}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="instructions">
            <h3>🎵 Chế độ hoạt động:</h3>
            <p>• <strong>Chỉ RÈ TO</strong>: Spam âm thanh rè to không cần file</p>
            <p>• <strong>File MP3</strong>: Upload file MP3 và làm cho nó RÈ TO</p>
            <p>• Tool sẽ treo room và spam âm thanh liên tục</p>
        </div>
        
        <form method="POST" action="{{ url_for('dis5.add_task') }}" enctype="multipart/form-data">
            <label>🔑 Token Discord:</label>
            <input type="password" name="token" placeholder="Nhập token Discord..." required>

            <label>🎯 Channel ID (Voice):</label>
            <input type="text" name="channel_id" placeholder="Nhập Channel ID voice..." required>

            <label>🎵 Chọn chế độ:</label>
            <div class="mode-selector">
                <div class="mode-btn active" id="modeRere" onclick="selectMode('rere')">
                    🔊 Chỉ RÈ TO
                </div>
                <div class="mode-btn" id="modeFile" onclick="selectMode('file')">
                    📁 File MP3
                </div>
            </div>
            <input type="hidden" name="mode" id="modeInput" value="rere">

            <div id="fileSection" style="display: none;">
                <label>📁 Upload file MP3 (tùy chọn):</label>
                <div class="file-upload" onclick="document.getElementById('mp3File').click()">
                    <div>🎵 Click để chọn file MP3</div>
                    <div class="file-name" id="fileName">Chưa chọn file</div>
                    <input type="file" id="mp3File" name="mp3_file" accept=".mp3,.wav,.ogg" onchange="updateFileName(this)">
                </div>
                <small style="color: #8b949e;">Nếu không chọn file, tool sẽ chỉ rè to</small>
            </div>

            <label>🔊 Độ RÈ (Volume Boost):</label>
            <input type="range" id="volumeSlider" name="volume_boost" min="1" max="10" value="5" step="0.5" class="volume-slider" oninput="updateVolumeValue(this.value)">
            
            <div class="volume-preview">
                <span>Nhỏ</span>
                <div class="volume-bar">
                    <div class="volume-fill" id="volumeFill"></div>
                </div>
                <span>RÈ TO</span>
            </div>
            
            <div class="volume-value" id="volumeValue">x5.0</div>

            <label>⏱ Interval (giây):</label>
            <input type="number" name="interval" value="15" min="5" max="300" required>
            <small style="color: #8b949e;">Thời gian giữa các lần phát lại (5-300 giây)</small>

            <div class="checkbox-group">
                <div class="checkbox-item">
                    <input type="checkbox" name="mute" id="mute">
                    <label for="mute">🔇 Mute</label>
                </div>
                <div class="checkbox-item">
                    <input type="checkbox" name="deaf" id="deaf">
                    <label for="deaf">🎧 Deaf</label>
                </div>
                <div class="checkbox-item">
                    <input type="checkbox" name="stream" id="stream">
                    <label for="stream">📹 Stream</label>
                </div>
            </div>

            <div class="warning">
                ⚠️ CẢNH BÁO: ÂM THANH SẼ RẤT TO VÀ CÓ THỂ GÂY KHÓ CHỊU
            </div>

            <button type="submit" class="pulse">🚀 Bắt Đầu Treo Room & Spam RÈ TO</button>
        </form>
    </div>

    <table>
        <tr>
            <th>ID</th>
            <th>Channel</th>
            <th>Chế độ</th>
            <th>Volume</th>
            <th>Interval</th>
            <th>Trạng thái</th>
            <th>Lần phát</th>
            <th>Hành động cuối</th>
            <th>Hành động</th>
        </tr>
        {% for tid, t in room_tasks.items() %}
        <tr>
            <td>{{ tid[:8] }}...</td>
            <td>{{ t.channel_id }}</td>
            <td>
                {% if t.use_custom_audio and t.filename %}
                    📁 {{ t.filename[:15] }}...
                {% else %}
                    🔊 RÈ TO
                {% endif %}
            </td>
            <td>x{{ t.volume_boost }}</td>
            <td>{{ t.interval }}s</td>
            <td>
                {% if 'running' in t and t.running %}
                    <span class="status-running">{{ t.status }}</span>
                {% elif 'running' in t and not t.running %}
                    <span class="status-stopped">{{ t.status }}</span>
                {% else %}
                    <span class="status-error">Chưa khởi động</span>
                {% endif %}
            </td>
            <td>{{ t.cycle_count if 'cycle_count' in t else 0 }}</td>
            <td style="max-width: 200px; word-wrap: break-word;">
                {{ t.last_action if 'last_action' in t else 'Chưa có' }}
            </td>
            <td>
                {% if 'running' in t and t.running %}
                    <a href="{{ url_for('dis5.stop_task', task_id=tid) }}"><button class="action-btn btn-stop">🛑 Dừng</button></a>
                {% else %}
                    <a href="{{ url_for('dis5.start_task_route', task_id=tid) }}"><button class="action-btn btn-start">▶️ Chạy</button></a>
                {% endif %}
                <a href="{{ url_for('dis5.delete_task', task_id=tid) }}"><button class="action-btn btn-delete">🗑️ Xóa</button></a>
            </td>
        </tr>
        {% endfor %}
    </table>

    <div class="center">
        <a href="/menu" class="back-btn">⬅️ Quay về Menu Chính</a>
    </div>

    <script>
        function selectMode(mode) {
            const modeRere = document.getElementById('modeRere');
            const modeFile = document.getElementById('modeFile');
            const fileSection = document.getElementById('fileSection');
            const modeInput = document.getElementById('modeInput');
            
            if (mode === 'rere') {
                modeRere.classList.add('active');
                modeFile.classList.remove('active');
                fileSection.style.display = 'none';
                modeInput.value = 'rere';
            } else {
                modeRere.classList.remove('active');
                modeFile.classList.add('active');
                fileSection.style.display = 'block';
                modeInput.value = 'file';
            }
        }
        
        function updateFileName(input) {
            const fileName = input.files[0] ? input.files[0].name : 'Chưa chọn file';
            document.getElementById('fileName').textContent = fileName;
        }
        
        function updateVolumeValue(value) {
            document.getElementById('volumeValue').textContent = 'x' + value;
            document.getElementById('volumeFill').style.width = (value * 10) + '%';
            
            // Thay đổi màu sắc dựa trên giá trị volume
            if (value >= 8) {
                document.getElementById('volumeValue').style.color = '#ff4444';
                document.getElementById('volumeValue').style.textShadow = '0 0 10px #ff4444';
            } else if (value >= 5) {
                document.getElementById('volumeValue').style.color = '#ffff00';
                document.getElementById('volumeValue').style.textShadow = '0 0 10px #ffff00';
            } else {
                document.getElementById('volumeValue').style.color = '#00ff00';
                document.getElementById('volumeValue').style.textShadow = '0 0 10px #00ff00';
            }
        }
        
        // Khởi tạo giá trị volume
        document.addEventListener('DOMContentLoaded', function() {
            updateVolumeValue(5);
        });
    </script>
</body>
</html>
    ''', room_tasks=room_tasks)

@dis5_bp.route('/add_task', methods=['POST'])
def add_task():
    """Thêm task treo room và spam voice mới"""
    try:
        token = request.form.get('token')
        channel_id = request.form.get('channel_id')
        volume_boost = float(request.form.get('volume_boost', 5))
        interval = int(request.form.get('interval', 15))
        mode = request.form.get('mode', 'rere')
        mute = request.form.get('mute') == 'on'
        deaf = request.form.get('deaf') == 'on'
        stream = request.form.get('stream') == 'on'
        
        mp3_file_path = None
        filename = None
        use_custom_audio = False
        
        # Xử lý file upload nếu có
        if 'mp3_file' in request.files and mode == 'file':
            file = request.files['mp3_file']
            if file and file.filename != '':
                if file.filename.lower().endswith(('.mp3', '.wav', '.ogg')):
                    # Lưu file
                    filename = str(uuid.uuid4()) + '_' + file.filename
                    mp3_file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(mp3_file_path)
                    use_custom_audio = True
                    
                    # Xử lý file audio (tăng volume)
                    mp3_file_path = process_audio_file(mp3_file_path, volume_boost)
                else:
                    flash('Chỉ chấp nhận file MP3, WAV, OGG', 'error')
                    return redirect(url_for('dis5.dis5_page'))
        
        # Tạo task mới
        task_id = str(uuid.uuid4())
        room_tasks[task_id] = {
            'token': token,
            'channel_id': channel_id,
            'file_path': mp3_file_path,
            'filename': filename,
            'volume_boost': volume_boost,
            'interval': interval,
            'use_custom_audio': use_custom_audio,
            'mute': mute,
            'deaf': deaf,
            'stream': stream,
            'running': False,
            'status': 'Chưa khởi động',
            'cycle_count': 0,
            'last_action': 'Chưa có hành động'
        }
        
        # Bắt đầu task
        thread = threading.Thread(
            target=join_and_spam_voice,
            args=(task_id, token, channel_id, mp3_file_path, volume_boost, interval, use_custom_audio, mute, deaf, stream)
        )
        thread.daemon = True
        thread.start()
        
        if use_custom_audio:
            flash(f'💥 Đã tạo task {task_id[:8]}... và bắt đầu spam FILE MP3 RÈ TO!', 'success')
        else:
            flash(f'🔊 Đã tạo task {task_id[:8]}... và bắt đầu spam RÈ TO!', 'success')
        
    except Exception as e:
        flash(f'❌ Lỗi: {str(e)}', 'error')
    
    return redirect(url_for('dis5.dis5_page'))

@dis5_bp.route('/start_task/<task_id>')
def start_task_route(task_id):
    """Bắt đầu lại task"""
    if task_id in room_tasks:
        task = room_tasks[task_id]
        if not task.get('running', False):
            thread = threading.Thread(
                target=join_and_spam_voice,
                args=(
                    task_id,
                    task['token'],
                    task['channel_id'],
                    task['file_path'],
                    task['volume_boost'],
                    task['interval'],
                    task['use_custom_audio'],
                    task['mute'],
                    task['deaf'],
                    task['stream']
                )
            )
            thread.daemon = True
            thread.start()
            flash('✅ Đã khởi động lại task!', 'success')
        else:
            flash('⚠️ Task đang chạy!', 'error')
    else:
        flash('❌ Task không tồn tại!', 'error')
    
    return redirect(url_for('dis5.dis5_page'))

@dis5_bp.route('/stop_task/<task_id>')
def stop_task(task_id):
    """Dừng task"""
    if task_id in room_tasks:
        room_tasks[task_id]['running'] = False
        room_tasks[task_id]['status'] = '🔴 Đã dừng'
        flash('🛑 Đã dừng task!', 'success')
    else:
        flash('❌ Task không tồn tại!', 'error')
    
    return redirect(url_for('dis5.dis5_page'))

@dis5_bp.route('/delete_task/<task_id>')
def delete_task(task_id):
    """Xóa task"""
    if task_id in room_tasks:
        room_tasks[task_id]['running'] = False
        
        # Xóa file MP3 nếu có
        try:
            if room_tasks[task_id]['file_path'] and os.path.exists(room_tasks[task_id]['file_path']):
                os.remove(room_tasks[task_id]['file_path'])
        except:
            pass
            
        del room_tasks[task_id]
        flash('🗑️ Đã xóa task!', 'success')
    else:
        flash('❌ Task không tồn tại!', 'error')
    
    return redirect(url_for('dis5.dis5_page'))
