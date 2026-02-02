"""
Configuración del Generador de Videos Automáticos
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ==================== API KEYS ====================
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# DEBUG: Verificar arquivo .env e variáveis
print(f"📁 DEBUG - Arquivo .env existe: {os.path.exists('.env')}")
print(f"📁 DEBUG - Diretório atual: {os.getcwd()}")
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        env_content = f.read()
        print(f"📁 DEBUG - Conteúdo .env (primeiras linhas):")
        for line in env_content.split('\n')[:5]:
            if 'GEMINI' in line:
                print(f"     {line[:30]}...")
print(f"🔑 DEBUG config.py - GEMINI_API_KEY: {GEMINI_API_KEY[:20]}...{GEMINI_API_KEY[-4:]}" if GEMINI_API_KEY else "❌ config.py - NENHUMA CHAVE")
print(f"🔑 DEBUG config.py - Tamanho: {len(GEMINI_API_KEY) if GEMINI_API_KEY else 0} caracteres")

# ==================== CONFIGURACIÓN DE VIDEO ====================
# Formato REEL (vertical - Instagram/TikTok)
VIDEO_CONFIG_REEL = {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "format": "mp4",
    "codec": "libx264",
    "audio_codec": "aac",
    "bitrate": "8000k",
    "duration_target": 30,  # ~30 segundos
    "num_segments": 1,      # 1 historia
    "num_images": 3,        # 3 imágenes por video
}

# Formato YOUTUBE (horizontal - YouTube)
VIDEO_CONFIG_YOUTUBE = {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "format": "mp4",
    "codec": "libx264",
    "audio_codec": "aac",
    "bitrate": "12000k",    # Mayor bitrate para YouTube
    "duration_target": 420, # ~7 minutos (420 segundos)
    "num_segments": 7,      # 7 historias (~1 min cada una)
    "num_images": 4,        # 4 imágenes por segmento
}

# Config por defecto (reel)
VIDEO_CONFIG = VIDEO_CONFIG_REEL

# ==================== CONFIGURACIÓN DE VOZ (ElevenLabs) ====================
# Parámetros optimizados para voz NATURAL y NO ROBÓTICA
TTS_CONFIG = {
    "voice_id": "W5JElH3dK1UYYAiHH7uh",  # Carmelo - voz premium
    "model_id": "eleven_multilingual_v2",  # Mejor modelo para español
    "stability": 0.65,  # 0.65 = equilibrio entre consistencia y expresividad natural
    "similarity_boost": 0.60,  # 0.60 = más libertad para sonar humano (menos clonación rígida)
    "style": 0.15,  # 0.15 = sutil, evita exageraciones que suenan artificiales
    "use_speaker_boost": True,  # Mejora claridad sin afectar naturalidad
}

# Voces disponibles en ElevenLabs - ÉPICAS para narración estoica
AVAILABLE_VOICES = {
    # ⭐ VOZ PREMIUM RECOMENDADA
    "carmelo": "W5JElH3dK1UYYAiHH7uh",     # ⭐ Carmelo - Misterioso, profundo, maduro
    # Voces épicas alternativas
    "brian": "nPczCjzI2devNBz1zQrb",       # Narrador épico, profundo, dramático
    "clyde": "2EiwWnXFnvU5JabPnv8n",       # Veterano de guerra, autoritario
    "antoni": "ErXwobaYiN019PkySvjV",      # Masculina, cálida pero firme
    # Voces originales
    "rachel": "21m00Tcm4TlvDq8ikWAM",      # Femenina, clara, profesional
    "adam": "pNInz6obpgDQGcFmaJgB",        # Masculina, profunda, narrador
    "josh": "TxGEqnHWrfWFTfGW9XjX",        # Masculina, joven, dinámica
    "arnold": "VR6AewLTigWG4xSOukaG",      # Masculina, profunda, autoritaria
    "bella": "EXAVITQu4vr4xnSDxMaL",       # Femenina, suave, cálida
}

# ==================== CONFIGURACIÓN DE SUBTÍTULOS ====================
SUBTITLE_CONFIG = {
    "font": "Arial-Bold",
    "fontsize": 70,
    "color": "white",
    "stroke_color": "black",
    "stroke_width": 3,
    "position": ("center", 0.75),  # Centro horizontal, 75% desde arriba
    "method": "caption",
    "size": (900, None),  # Ancho máximo del texto
}

# ==================== KEYWORDS PARA BUSCAR VIDEOS ====================
VIDEO_KEYWORDS = [
    # Estoicismo y filosofía
    "greek statue marble",
    "roman sculpture",
    "ancient columns ruins",
    "marble texture",
    "classical architecture",
    # Naturaleza contemplativa
    "storm clouds dramatic",
    "ocean waves power",
    "mountain peak summit",
    "fire flames dark",
    "rain dark moody",
    # Mentalidad y disciplina
    "man walking alone",
    "silhouette sunset",
    "fog forest mysterious",
    "clock time passing",
    "chess strategy",
]

# ==================== RUTAS DEL PROYECTO ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
CONTENT_DIR = os.path.join(BASE_DIR, "content")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Rutas del Cache de Imágenes
IMAGE_CACHE_DIR = os.path.join(ASSETS_DIR, "image_cache")
PREMIUM_IMAGES_DIR = os.path.join(ASSETS_DIR, "premium_images")

# ==================== CONFIGURACIÓN DEL CACHE ====================
CACHE_CONFIG = {
    "enabled": True,
    "min_cache_before_reuse": 3,  # Mínimo 3 imágenes en cache antes de reutilizar
    "cache_ratio": 0.66,          # Usar 66% del cache, 33% nuevas
    "max_cache_per_theme": 20,    # Máximo 20 imágenes por tema
}

# Temas disponibles
AVAILABLE_THEMES = [
    "disciplina", "estoicismo", "coraje", "resiliencia", 
    "mentalidad", "control", "tiempo", "mortalidad", 
    "proposito", "sabiduria"
]

# Crear directorios si no existen
for dir_path in [OUTPUT_DIR, TEMP_DIR, CONTENT_DIR, ASSETS_DIR, IMAGE_CACHE_DIR, PREMIUM_IMAGES_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Crear subdirectorios del cache por tema
for theme in AVAILABLE_THEMES:
    os.makedirs(os.path.join(IMAGE_CACHE_DIR, theme), exist_ok=True)

