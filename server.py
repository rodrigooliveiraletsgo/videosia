import os
import threading
from flask import Flask, request, redirect, url_for, render_template_string

# IMPORTA O GERADOR
from generar_5_cosas import main as gerar_shorts

# ========================
# CONFIG
# ========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LIBRARY_DIR = os.path.join(ASSETS_DIR, "video_library")

os.makedirs(LIBRARY_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"mp4"}

app = Flask(__name__)

# ========================
# STATUS GLOBAL
# ========================

STATUS = {
    "running": False,
    "message": "Aguardando comando"
}

# ========================
# HELPERS
# ========================

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def gerar_com_status():
    global STATUS
    STATUS["running"] = True
    STATUS["message"] = "🎬 Gerando shorts..."

    try:
        gerar_shorts()
        STATUS["message"] = "✅ Finalizado com sucesso"
    except Exception as e:
        STATUS["message"] = f"❌ Erro: {e}"
    finally:
        STATUS["running"] = False


def listar_videos():
    return sorted(
        [f for f in os.listdir(LIBRARY_DIR) if f.endswith(".mp4")]
    )


# ========================
# ROUTE PRINCIPAL
# ========================

@app.route("/", methods=["GET", "POST"])
def home():
    global STATUS

    # UPLOAD
    if request.method == "POST" and "video" in request.files:
        file = request.files["video"]
        if file and allowed_file(file.filename):
            path = os.path.join(LIBRARY_DIR, file.filename)
            file.save(path)
        return redirect(url_for("home"))

    # GERAR
    if request.method == "POST" and "gerar" in request.form:
        if not STATUS["running"]:
            thread = threading.Thread(target=gerar_com_status)
            thread.start()
        return redirect(url_for("home"))

    videos = listar_videos()

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>🎬 Gerador de Shorts</title>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial; max-width: 800px; margin: auto;">

    <h1>🎥 Biblioteca de Vídeos</h1>

    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="video" required>
        <button type="submit">📤 Upload</button>
    </form>

    <h3>📚 Vídeos disponíveis ({{ videos|length }})</h3>
    <ul>
        {% for v in videos %}
            <li>{{ v }}</li>
        {% endfor %}
    </ul>

    <hr>

    <h2>📊 Status</h2>
    <p><b>{{ status }}</b></p>

    <form method="POST">
        <button type="submit" name="gerar" {% if running %}disabled{% endif %}>
            🚀 GERAR SHORTS
        </button>
    </form>

    <script>
        setTimeout(() => location.reload(), 3000);
    </script>

</body>
</html>
""", videos=videos, status=STATUS["message"], running=STATUS["running"])


# ========================
# START
# ========================

if __name__ == "__main__":
    app.run(debug=True)
