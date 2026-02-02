import os
import threading
from datetime import datetime
from flask import Flask, request, redirect, send_from_directory, render_template_string

# ========================
# IMPORT DO GERADOR
# ========================
from generar_5_cosas import main as gerar_shorts, generar_solo_guion, crear_video_desde_guion

# ========================
# CONFIG
# ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LIBRARY_DIR = os.path.join(ASSETS_DIR, "video_library")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(LIBRARY_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)

# ========================
# GLOBAL STATUS
# ========================
STATUS = {
    "running": False,
    "message": "Idle",
    "progress": 0,
    "script_preview": None,  # Armazena roteiro para preview
    "video_sequence": None  # Armazena sequência de vídeos selecionados
}

# ========================
# BACKGROUND GENERATOR
# ========================
def run_generator():
    try:
        STATUS["running"] = True
        STATUS["message"] = "Generating videos..."
        STATUS["progress"] = 10

        gerar_shorts()

        STATUS["progress"] = 100
        STATUS["message"] = "✅ Completed successfully"
    except Exception as e:
        STATUS["message"] = f"❌ Error: {e}"
    finally:
        STATUS["running"] = False
        STATUS["progress"] = 0


def listar_videos_biblioteca():
    """List library videos for upload"""
    if os.path.exists(LIBRARY_DIR):
        return sorted(
            [f for f in os.listdir(LIBRARY_DIR) if f.endswith(".mp4")]
        )
    return []


def listar_videos_gerados():
    """List generated videos from output folder sorted by modification date"""
    if os.path.exists(OUTPUT_DIR):
        videos = []
        for f in os.listdir(OUTPUT_DIR):
            if f.endswith(".mp4"):
                file_path = os.path.join(OUTPUT_DIR, f)
                mtime = os.path.getmtime(file_path)
                timestamp = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                videos.append({"name": f, "timestamp": timestamp, "mtime": mtime})
        # Sort by modification date (newest first)
        videos.sort(key=lambda x: x["mtime"], reverse=True)
        return videos
    return []


# ========================
# ROUTES
# ========================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if not STATUS["running"]:
            threading.Thread(target=run_generator).start()
        return redirect("/")

    videos_biblioteca = listar_videos_biblioteca()
    videos_gerados = listar_videos_gerados()

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>🎬 Automatic Shorts Generator</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        h2 { color: #666; margin-top: 30px; }
        .status {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .progress {
            background: #ddd;
            border-radius: 5px;
            height: 25px;
            margin: 10px 0;
        }
        .progress-bar {
            background: #4caf50;
            height: 100%;
            border-radius: 5px;
            transition: width 0.3s;
        }
        button {
            background: #2196F3;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 5px 10px 0;
        }
        button:hover { background: #1976D2; }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .video-list {
            list-style: none;
            padding: 0;
        }
        .video-item {
            background: #f9f9f9;
            padding: 12px;
            margin: 8px 0;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .video-item:hover {
            background: #f0f0f0;
        }
        .download-btn {
            background: #4caf50;
            padding: 8px 16px;
            font-size: 14px;
        }
        .download-btn:hover {
            background: #45a049;
        }
        .delete-btn {
            background: #f44336;
            padding: 8px 16px;
            font-size: 14px;
        }
        .delete-btn:hover {
            background: #da190b;
        }
        input[type="file"] {
            margin: 10px 0;
            padding: 10px;
            border: 2px dashed #2196F3;
            border-radius: 5px;
            cursor: pointer;
            display: block;
            width: calc(100% - 24px);
        }
        input[type="file"]::file-selector-button {
            padding: 10px 20px;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 10px;
        }
        input[type="file"]::file-selector-button:hover {
            background: #1976D2;
        }
        .upload-section {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .upload-btn {
            background: #ff9800;
            margin-top: 10px;
        }
        .upload-btn:hover {
            background: #f57c00;
        }
        .file-info {
            margin: 10px 0;
            padding: 10px;
            background: #e8f5e9;
            border-radius: 5px;
            display: none;
        }
    </style>
</head>
<body>
<div class="container">

    <h1>🎬 Automatic Shorts Generator</h1>

    <div class="status">
        <p><b>Status:</b> {{ status.message }}</p>
        <div class="progress">
            <div class="progress-bar" style="width: {{ status.progress }}%"></div>
        </div>
        <p>Progress: {{ status.progress }}%</p>
    </div>

    {% if status.script_preview %}
    <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
        <h2 style="margin-top: 0;">📝 Script Preview</h2>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div style="background: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd;">
                <h3 style="color: #d32f2f; margin-top: 0;">🇪🇸 Spanish</h3>
                {% for clip_name, clip_data in status.script_preview.short_es.items() %}
                    <div style="margin-bottom: 15px;">
                        <strong>{{ clip_name }}:</strong>
                        <ul style="margin: 5px 0; padding-left: 20px;">
                        {% for segment in clip_data.segments %}
                            <li>{{ segment }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                {% endfor %}
            </div>
            
            <div style="background: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd;">
                <h3 style="color: #1976d2; margin-top: 0;">🇺🇸 English</h3>
                {% for clip_name, clip_data in status.script_preview.short_en.items() %}
                    <div style="margin-bottom: 15px;">
                        <strong>{{ clip_name }}:</strong>
                        <ul style="margin: 5px 0; padding-left: 20px;">
                        {% for segment in clip_data.segments %}
                            <li>{{ segment }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                {% endfor %}
            </div>
        </div>
        
        {% if status.script_preview.image_prompts %}
        <div style="background: #e8f5e9; padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #4caf50;">
            <h3 style="margin-top: 0; color: #2e7d32;">🎨 Image Prompts for Whisk AI</h3>
            {% for clip_name, prompt in status.script_preview.image_prompts.items() %}
                <div style="margin-bottom: 12px; background: white; padding: 12px; border-radius: 4px; position: relative;">
                    <strong style="color: #1976d2;">{{ clip_name }}:</strong>
                    <p style="margin: 8px 0; font-family: monospace; font-size: 13px; color: #333;" id="prompt-{{ loop.index }}">{{ prompt }}</p>
                    <button onclick="copyToClipboard('prompt-{{ loop.index }}')" style="background: #2196F3; color: white; border: none; padding: 6px 12px; font-size: 12px; border-radius: 4px; cursor: pointer; margin-top: 5px;">
                        📋 Copy
                    </button>
                </div>
            {% endfor %}
        </div>
        <script>
        function copyToClipboard(elementId) {
            const element = document.getElementById(elementId);
            const text = element.innerText || element.textContent;
            
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(() => {
                    alert('✅ Prompt copied to clipboard!');
                }).catch(err => {
                    fallbackCopy(text);
                });
            } else {
                fallbackCopy(text);
            }
        }
        
        function fallbackCopy(text) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                alert('✅ Prompt copied to clipboard!');
            } catch (err) {
                alert('❌ Failed to copy. Please copy manually.');
            }
            document.body.removeChild(textarea);
        }
        </script>
        {% endif %}
        
        <!-- Video Sequence Selection -->
        <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #2196F3;">
            <h3 style="margin-top: 0; color: #1565c0;">🎬 Select Video Sequence (2 videos per clip = 6 total)</h3>
            <form method="POST" action="/save-sequence" id="sequence-form">
                {% for clip in ['clip_1', 'clip_2', 'clip_3'] %}
                <div style="background: white; padding: 12px; margin-bottom: 12px; border-radius: 4px;">
                    <strong style="color: #1976d2;">{{ clip }}:</strong>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px;">
                        <div>
                            <label style="font-size: 12px; color: #666;">Video 1:</label>
                            <select name="{{ clip }}_video_1" id="{{ clip }}_video_1" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" onchange="updateThumbnail('{{ clip }}_video_1')">
                                <option value="">Select video...</option>
                                {% for video in videos_biblioteca %}
                                <option value="{{ video }}" {% if status.video_sequence and status.video_sequence[clip][0] == video %}selected{% endif %}>{{ video }}</option>
                                {% endfor %}
                            </select>
                            <img id="thumb_{{ clip }}_video_1" style="width: 100%; margin-top: 8px; border-radius: 4px; display: none;" />
                        </div>
                        <div>
                            <label style="font-size: 12px; color: #666;">Video 2:</label>
                            <select name="{{ clip }}_video_2" id="{{ clip }}_video_2" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" onchange="updateThumbnail('{{ clip }}_video_2')">
                                <option value="">Select video...</option>
                                {% for video in videos_biblioteca %}
                                <option value="{{ video }}" {% if status.video_sequence and status.video_sequence[clip][1] == video %}selected{% endif %}>{{ video }}</option>
                                {% endfor %}
                            </select>
                            <img id="thumb_{{ clip }}_video_2" style="width: 100%; margin-top: 8px; border-radius: 4px; display: none;" />
                        </div>
                    </div>
                </div>
                {% endfor %}
                <button type="submit" style="background: #2196F3; width: 100%;" {% if status.running %}disabled{% endif %}>
                    💾 Save Video Sequence
                </button>
            </form>
        </div>
        <script>
        function updateThumbnail(selectId) {
            const select = document.getElementById(selectId);
            const thumb = document.getElementById('thumb_' + selectId);
            const filename = select.value;
            
            if (filename) {
                thumb.src = '/thumbnail/' + encodeURIComponent(filename);
                thumb.style.display = 'block';
            } else {
                thumb.style.display = 'none';
            }
        }
        
        // Atualiza thumbnails ao carregar página
        document.addEventListener('DOMContentLoaded', function() {
            {% for clip in ['clip_1', 'clip_2', 'clip_3'] %}
            updateThumbnail('{{ clip }}_video_1');
            updateThumbnail('{{ clip }}_video_2');
            {% endfor %}
        });
        </script>
        
        <div style="display: flex; gap: 10px;">
            <form method="POST" action="/create-video" style="display: inline;">
                <button type="submit" style="background: #4caf50;" {% if status.running or not status.video_sequence %}disabled{% endif %}>
                    ✅ Approve & Create Videos
                </button>
            </form>
            <form method="POST" action="/generate-script" style="display: inline;">
                <button type="submit" style="background: #ff9800;" {% if status.running %}disabled{% endif %}>
                    🔄 Regenerate Script
                </button>
            </form>
            <form method="POST" action="/clear-script" style="display: inline;">
                <button type="submit" style="background: #f44336;" {% if status.running %}disabled{% endif %}>
                    🗑️ Discard
                </button>
            </form>
        </div>
    </div>
    {% else %}
    <form method="POST" action="/generate-script">
        <button type="submit" {% if status.running %}disabled{% endif %}>
            📝 Generate Script (Step 1)
        </button>
    </form>
    {% endif %}

    <hr>

    <h2>📥 Generated Videos ({{ videos_gerados|length }})</h2>
    {% if videos_gerados %}
        <ul class="video-list">
        {% for video in videos_gerados %}
            <li class="video-item">
                <div>
                    <div>📹 {{ video.name }}</div>
                    <small style="color: #999;">{{ video.timestamp }}</small>
                </div>
                <a href="/download/{{ video.name }}">
                    <button class="download-btn">⬇️ Download</button>
                </a>
            </li>
        {% endfor %}
        </ul>
    {% else %}
        <p>No videos generated yet</p>
    {% endif %}

    <hr>

    <div class="upload-section">
        <h2>📤 Upload video / asset</h2>
        <form method="POST" action="/upload" enctype="multipart/form-data" id="upload-form">
            <label for="file-input" style="display: block; margin-bottom: 10px; font-weight: bold;">
                Select MP4 video files (multiple):
            </label>
            <input type="file" id="file-input" name="files" accept=".mp4" multiple required>
            <div id="file-info" class="file-info">
                ✅ <strong id="file-count">0</strong> file(s) selected
                <div id="file-list" style="margin-top: 8px; font-size: 12px;"></div>
            </div>
            <button type="submit" class="upload-btn" id="upload-btn">📤 Upload Videos</button>
        </form>
    </div>

    <script>
        // Show selected file names
        document.getElementById('file-input').addEventListener('change', function(e) {
            const fileInfo = document.getElementById('file-info');
            const fileCount = document.getElementById('file-count');
            const fileList = document.getElementById('file-list');
            const uploadBtn = document.getElementById('upload-btn');
            
            if (this.files && this.files.length > 0) {
                fileCount.textContent = this.files.length;
                
                // Show list of files
                let listHTML = '';
                for (let i = 0; i < this.files.length; i++) {
                    listHTML += `<div style="padding: 4px 0;">📹 ${this.files[i].name}</div>`;
                }
                fileList.innerHTML = listHTML;
                
                fileInfo.style.display = 'block';
                uploadBtn.disabled = false;
            } else {
                fileInfo.style.display = 'none';
                uploadBtn.disabled = true;
            }
        });

        // Auto-reload only when generation is running
        const isGenerating = {{ 'true' if status.running else 'false' }};
        if (isGenerating) {
            setTimeout(() => location.reload(), 3000);
        }
    </script>

    <h2>📚 Video Library ({{ videos_biblioteca|length }})</h2>
    {% if videos_biblioteca %}
        <ul class="video-list">
        {% for video in videos_biblioteca %}
            <li class="video-item">
                <span>📁 {{ video }}</span>
                <form method="POST" action="/delete/{{ video }}" style="display: inline;">
                    <button type="submit" class="delete-btn" onclick="return confirm('Delete {{ video }}?');">🗑️ Delete</button>
                </form>
            </li>
        {% endfor %}
        </ul>
    {% else %}
        <p>No videos in library</p>
    {% endif %}

</div>
</body>
</html>
""", videos_gerados=videos_gerados, videos_biblioteca=videos_biblioteca, status=STATUS)


# ========================
# GENERATE SCRIPT (STEP 1)
# ========================
@app.route("/generate-script", methods=["POST"])
def generate_script():
    """Gera apenas o roteiro para preview"""
    if STATUS["running"]:
        return redirect("/")
    
    try:
        STATUS["running"] = True
        STATUS["message"] = "Generating script..."
        STATUS["progress"] = 30
        
        guion = generar_solo_guion()
        
        if guion:
            STATUS["script_preview"] = guion
            STATUS["message"] = "✅ Script ready for preview"
            STATUS["progress"] = 100
        else:
            STATUS["message"] = "❌ Failed to generate script"
            STATUS["script_preview"] = None
            
    except Exception as e:
        STATUS["message"] = f"❌ Error: {e}"
        STATUS["script_preview"] = None
    finally:
        STATUS["running"] = False
        STATUS["progress"] = 0
    
    return redirect("/")


# ========================
# SAVE VIDEO SEQUENCE (STEP 1.5)
# ========================
@app.route("/save-sequence", methods=["POST"])
def save_sequence():
    """Salva a sequência de vídeos selecionados"""
    sequence = {
        "clip_1": [request.form.get("clip_1_video_1"), request.form.get("clip_1_video_2")],
        "clip_2": [request.form.get("clip_2_video_1"), request.form.get("clip_2_video_2")],
        "clip_3": [request.form.get("clip_3_video_1"), request.form.get("clip_3_video_2")]
    }
    STATUS["video_sequence"] = sequence
    STATUS["message"] = "✅ Video sequence saved"
    return redirect("/")


# ========================
# CREATE VIDEO FROM SCRIPT (STEP 2)
# ========================
@app.route("/create-video", methods=["POST"])
def create_video():
    """Cria vídeos a partir do roteiro aprovado"""
    if STATUS["running"] or not STATUS["script_preview"] or not STATUS["video_sequence"]:
        return redirect("/")
    
    def run_creation():
        try:
            STATUS["running"] = True
            STATUS["message"] = "Creating videos..."
            STATUS["progress"] = 50
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            success = crear_video_desde_guion(STATUS["script_preview"], timestamp, STATUS["video_sequence"])
            
            if success:
                STATUS["message"] = "✅ Videos created successfully"
                STATUS["progress"] = 100
                STATUS["script_preview"] = None
            else:
                STATUS["message"] = "❌ Error creating videos"
                
        except Exception as e:
            STATUS["message"] = f"❌ Error: {e}"
        finally:
            STATUS["running"] = False
            STATUS["progress"] = 0
    
    threading.Thread(target=run_creation).start()
    return redirect("/")


# ========================
# CLEAR SCRIPT PREVIEW
# ========================
@app.route("/clear-script", methods=["POST"])
def clear_script():
    """Descarta o roteiro atual"""
    STATUS["script_preview"] = None
    STATUS["video_sequence"] = None
    STATUS["message"] = "Script discarded"
    return redirect("/")


# ========================
# VIDEO THUMBNAIL
# ========================
@app.route("/thumbnail/<filename>")
def thumbnail(filename):
    """Gera e serve thumbnail de um vídeo"""
    import subprocess
    import tempfile
    
    video_path = os.path.join(LIBRARY_DIR, filename)
    if not os.path.exists(video_path):
        return "", 404
    
    # Gera thumbnail temporário
    temp_thumb = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    subprocess.run([
        "ffmpeg", "-i", video_path, "-ss", "00:00:01",
        "-vframes", "1", "-vf", "scale=160:280",
        "-y", temp_thumb.name
    ], capture_output=True)
    
    try:
        with open(temp_thumb.name, 'rb') as f:
            image_data = f.read()
        os.unlink(temp_thumb.name)
        from flask import Response
        return Response(image_data, mimetype='image/jpeg')
    except:
        return "", 404


# ========================
# DOWNLOAD
# ========================
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


# ========================
# UPLOAD
# ========================
@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")
    uploaded_count = 0
    
    for file in files:
        if file and file.filename.endswith('.mp4'):
            path = os.path.join(LIBRARY_DIR, file.filename)
            file.save(path)
            uploaded_count += 1
    
    if uploaded_count > 0:
        STATUS["message"] = f"✅ {uploaded_count} video(s) uploaded successfully"
    
    return redirect("/")


# ========================
# DELETE
# ========================
@app.route("/delete/<filename>", methods=["POST"])
def delete(filename):
    """Delete a video from library"""
    try:
        file_path = os.path.join(LIBRARY_DIR, filename)
        if os.path.exists(file_path) and filename.endswith('.mp4'):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting {filename}: {e}")
    return redirect("/")


# ========================
# START
# ========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
