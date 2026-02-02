#!/usr/bin/env python3
"""
🎬 Generador Automático de Videos - Estoicismo & Crecimiento Personal

Genera videos usando Motion 2.0 Fast de Leonardo AI.

Uso:
    python main.py                        # Genera un reel (~30s)
    python main.py --theme disciplina     # Tema específico
    python main.py --format youtube       # Video largo (~7 min)
    python main.py --batch 5              # 5 videos en lote
    python main.py --test                 # Test de conexión APIs
"""

import os
import sys
import argparse
import time
from datetime import datetime

# Importar módulos
from modules.content_generator import ContentGenerator
from modules.tts_engine import TTSEngine
from modules.video_composer import VideoComposer
from modules.image_generator import ImageGenerator
from config import OUTPUT_DIR, ELEVENLABS_API_KEY, GEMINI_API_KEY


def check_api_keys():
    """Verifica que las API keys estén configuradas"""
    missing = []
    
    if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == "tu_api_key_de_elevenlabs":
        missing.append("ELEVENLABS_API_KEY")
    
    if not GEMINI_API_KEY or GEMINI_API_KEY == "tu_api_key_de_gemini":
        missing.append("GEMINI_API_KEY (opcional, usará citas predefinidas)")
    
    if missing:
        print("⚠️ API Keys faltantes:")
        for key in missing:
            print(f"   - {key}")
        print("\nConfigura las keys en el archivo .env")
        
        if "ELEVENLABS_API_KEY" in missing:
            return False
    
    return True


def test_connections():
    """Prueba las conexiones con todas las APIs"""
    print("=" * 50)
    print("🔍 Probando conexiones con APIs...")
    print("=" * 50)
    
    all_ok = True
    
    # Test ElevenLabs
    print("\n[1/2] ElevenLabs (TTS):")
    try:
        tts = TTSEngine()
        if tts.test_connection():
            print("    ✅ Conexión exitosa")
        else:
            print("    ❌ Error de conexión")
            all_ok = False
    except Exception as e:
        print(f"    ❌ Error: {e}")
        all_ok = False
    
    # Test Gemini
    print("\n[2/2] Google Gemini (Contenido):")
    try:
        generator = ContentGenerator()
        if generator.client:
            script = generator.generate_script_sync("test")
            if script:
                print("    ✅ Conexión exitosa")
        else:
            print("    ⚠️ No configurado (usará citas predefinidas)")
    except Exception as e:
        print(f"    ⚠️ Error: {e}")
    
    print("\n" + "=" * 50)
    return all_ok


def generate_video(theme: str = "estoicismo", voice: str = "carmelo") -> str:
    """
    Genera un video completo con Motion 2.0 Fast
    
    Args:
        theme: Tema del contenido
        voice: Voz a usar (carmelo, brian, etc.)
        
    Returns:
        Ruta al video generado
    """
    print("\n" + "=" * 50)
    print("🎬 GENERADOR DE VIDEOS - ESTOICISMO")
    print("🎥 Motion 2.0 Fast - Videos de alta calidad")
    print("=" * 50)
    
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Inicializar módulos
    print("\n[1/5] Inicializando módulos...")
    content_gen = ContentGenerator()
    tts = TTSEngine(voice=voice)
    image_gen = ImageGenerator()
    composer = VideoComposer()
    
    # Generar contenido
    print("\n[2/5] Generando contenido...")
    script = content_gen.generate_script_sync(theme)
    narration = content_gen.get_full_narration(script)
    
    print(f"    📝 Hook: {script.get('hook', '')}")
    print(f"    📝 Texto: {script.get('text', '')[:60]}...")
    
    # Generar audio
    print("\n[3/5] Generando audio con IA...")
    audio_path = tts.generate_speech(narration, f"audio_{timestamp}")
    
    # Obtener duración del audio
    from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips
    import glob
    import random
    
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration + 1.5
    audio_clip.close()
    
    # USAR BIBLIOTECA DE VIDEOS (no generar nuevos)
    LIBRARY_DIR = os.path.join(os.path.dirname(__file__), "assets", "video_library")
    library_videos = glob.glob(os.path.join(LIBRARY_DIR, "*.mp4"))
    
    print(f"\n[4/5] Seleccionando videos de la biblioteca...")
    print(f"    📚 Videos disponibles: {len(library_videos)}")
    
    if not library_videos:
        print("❌ Biblioteca vacía. Usa: python video_library.py add 6")
        return None
    
    # Seleccionar videos aleatorios hasta cubrir la duración del audio
    random.shuffle(library_videos)
    
    motion_videos = []
    total_video_duration = 0
    
    for v in library_videos:
        if total_video_duration >= audio_duration:
            break
        motion_videos.append(v)
        clip = VideoFileClip(v)
        total_video_duration += clip.duration
        clip.close()
    
    print(f"    ✓ Seleccionados: {len(motion_videos)} videos ({total_video_duration:.1f}s)")
    
    if motion_videos:
        print(f"\n✓ {len(motion_videos)} videos de biblioteca seleccionados")
        
        # Concatenar videos
        print("🎬 Concatenando videos...")
        clips = [VideoFileClip(v) for v in motion_videos]
        
        # Loop videos hasta cubrir duración del audio
        total_motion_duration = sum(c.duration for c in clips)
        if total_motion_duration < audio_duration:
            loops_needed = int(audio_duration / total_motion_duration) + 1
            clips = clips * loops_needed
        
        concat_clip = concatenate_videoclips(clips, method="compose")
        concat_clip = concat_clip.subclip(0, min(audio_duration, concat_clip.duration))
        
        # Resize a 1080x1920
        concat_clip = concat_clip.resize((1080, 1920))
        
        temp_video_path = os.path.join(OUTPUT_DIR, f"temp_motion_{timestamp}.mp4")
        concat_clip.write_videofile(temp_video_path, fps=composer.fps, codec="libx264")
        
        for c in clips:
            c.close()
        concat_clip.close()
        
        video_path = temp_video_path
    else:
        print("❌ No hay videos en la biblioteca")
        return None
    
    # Componer reel final con audio
    print("\n[5/5] Componiendo video final con audio...")
    output_name = f"reel_{theme}_{timestamp}"
        
    output_path = composer.create_reel(
        background_video=video_path,
        audio_path=audio_path,
        subtitles_text=None,
        author=None,
        output_name=output_name,
        hook_text=None,
        cta_text=None,
        username=None
    )
    
    # Limpiar archivos temporales
    if os.path.exists(video_path) and "temp" in video_path:
        os.remove(video_path)
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 50)
    print(f"✅ VIDEO GENERADO EXITOSAMENTE")
    print(f"   📁 Archivo: {output_path}")
    print(f"   ⏱️ Tiempo: {elapsed:.1f} segundos")
    print("=" * 50)
    
    return output_path


def generate_youtube_video(theme: str = "estoicismo", voice: str = "carmelo") -> str:
    """
    Genera un video largo para YouTube (~7 minutos)
    Múltiples segmentos con contenido más desarrollado
    
    Args:
        theme: Tema principal
        voice: Voz para narración
        
    Returns:
        Ruta al video generado
    """
    print("\n" + "=" * 60)
    print("🎬 GENERADOR DE VIDEOS YOUTUBE - ESTOICISMO")
    print("🎥 Motion 2.0 Fast - Videos de alta calidad")
    print("   📐 Formato: 1080x1920 (vertical para YouTube Shorts/Reels)")
    print("   ⏱️ Duración: ~7 segmentos de 1 minuto cada uno")
    print("=" * 60)
    
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Configuración de video largo
    NUM_SEGMENTS = 7  # 7 segmentos de ~1 minuto = ~7 minutos
    
    # Inicializar módulos
    print("\n[1/6] Inicializando módulos...")
    content_gen = ContentGenerator()
    tts = TTSEngine(voice=voice)
    image_gen = ImageGenerator()
    composer = VideoComposer()
    
    # Generar contenido (múltiples segmentos)
    print(f"\n[2/6] Generando {NUM_SEGMENTS} segmentos de contenido...")
    scripts = content_gen.generate_youtube_scripts(theme, NUM_SEGMENTS)
    
    for i, script in enumerate(scripts):
        hook = script.get('hook', '')[:40]
        print(f"    📖 Segmento {i+1}: {hook}...")
    
    # Generar audio completo
    print("\n[3/6] Generando audio (~7 minutos)...")
    full_narration = content_gen.get_youtube_narration(scripts)
    audio_path = tts.generate_speech(full_narration, f"youtube_audio_{timestamp}")
    
    # Obtener duración del audio
    from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration + 2.0
    audio_clip.close()
    
    print(f"    ⏱️ Duración audio: {audio_duration/60:.1f} minutos")
    
    # Calcular videos necesarios
    # Cada video Motion = 10 segundos, necesitamos cubrir ~7 minutos = 420 segundos
    # Se necesitan ~42 videos, pero reutilizamos con loops
    num_videos = min(21, max(7, int(audio_duration / 20)))  # 1 video cada ~20s
    
    print(f"\n[4/6] Generando {num_videos} videos Motion 2.0 Fast...")
    motion_videos = image_gen.get_motion_videos(theme=theme, count=num_videos)
    
    if not motion_videos:
        print("❌ No se pudieron generar videos Motion")
        return None
    
    print(f"\n✓ {len(motion_videos)} videos Motion disponibles")
    
    # Concatenar videos
    print("\n[5/6] Concatenando videos...")
    clips = [VideoFileClip(v) for v in motion_videos]
    
    # Loop videos hasta cubrir duración del audio
    total_motion_duration = sum(c.duration for c in clips)
    if total_motion_duration < audio_duration:
        loops_needed = int(audio_duration / total_motion_duration) + 1
        clips = clips * loops_needed
    
    concat_clip = concatenate_videoclips(clips, method="compose")
    concat_clip = concat_clip.subclip(0, min(audio_duration, concat_clip.duration))
    
    # Resize a 1080x1920 (vertical)
    concat_clip = concat_clip.resize((1080, 1920))
    
    temp_video_path = os.path.join(OUTPUT_DIR, f"temp_youtube_{timestamp}.mp4")
    concat_clip.write_videofile(temp_video_path, fps=composer.fps, codec="libx264")
    
    for c in clips:
        c.close()
    concat_clip.close()
    
    # Componer video final con audio
    print("\n[6/6] Añadiendo audio...")
    output_name = f"youtube_{theme}_{timestamp}"
    
    output_path = composer.create_reel(
        background_video=temp_video_path,
        audio_path=audio_path,
        subtitles_text=None,
        author=None,
        output_name=output_name,
        hook_text=None,
        cta_text=None,
        username=None,
        target_resolution=(1080, 1920)
    )
    
    # Limpiar temporal
    if os.path.exists(temp_video_path):
        os.remove(temp_video_path)
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("✅ VIDEO YOUTUBE GENERADO EXITOSAMENTE")
    print(f"   📁 Archivo: {output_path}")
    print(f"   ⏱️ Duración: {audio_duration/60:.1f} minutos")
    print(f"   🕐 Tiempo de generación: {elapsed/60:.1f} minutos")
    print("=" * 60)
    
    return output_path


# Lista de temas estoicos
STOIC_THEMES = [
    "aceptacion", "adversidad", "autocontrol", "claridad", "control",
    "coraje", "desapego", "determinacion", "disciplina", "enfoque",
    "estoicismo", "fortaleza", "humildad", "mentalidad", "mortalidad",
    "paciencia", "perseverancia", "proposito", "resiliencia", "sabiduria",
    "sacrificio", "silencio", "soledad", "templanza", "tiempo", "virtud"
]


def get_random_theme() -> str:
    """Obtiene un tema aleatorio"""
    import random
    return random.choice(STOIC_THEMES)


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Generador de Videos con Motion 2.0 Fast"
    )
    parser.add_argument(
        "--theme", "-t",
        type=str,
        default="random",
        help="Tema del video (disciplina, coraje, etc.) o 'random'"
    )
    parser.add_argument(
        "--voice", "-v",
        type=str,
        default="carmelo",
        choices=["carmelo", "brian", "clyde", "adam", "rachel", "josh"],
        help="Voz para la narración"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Ejecutar test de conexión con APIs"
    )
    parser.add_argument(
        "--batch", "-b",
        type=int,
        default=0,
        help="Generar múltiples videos en lote"
    )
    parser.add_argument(
        "--format", "-f",
        type=str,
        default="reel",
        choices=["reel", "youtube"],
        help="Formato: reel (~30s) o youtube (~7 min)"
    )
    
    args = parser.parse_args()
    
    # Verificar API keys
    if not check_api_keys():
        print("\n❌ Configura las API keys antes de continuar.")
        sys.exit(1)
    
    # Modo test
    if args.test:
        success = test_connections()
        sys.exit(0 if success else 1)
    
    # Seleccionar tema
    theme = args.theme
    if theme == "random":
        theme = get_random_theme()
        print(f"🎲 Tema aleatorio: {theme}")
    
    # Modo batch
    if args.batch > 0:
        print(f"\n🎬 Generando {args.batch} videos en lote...")
        for i in range(args.batch):
            current_theme = get_random_theme()
            print(f"\n--- Video {i+1}/{args.batch} (Tema: {current_theme}) ---")
            try:
                if args.format == "youtube":
                    generate_youtube_video(theme=current_theme, voice=args.voice)
                else:
                    generate_video(theme=current_theme, voice=args.voice)
            except Exception as e:
                print(f"❌ Error: {e}")
            if i < args.batch - 1:
                time.sleep(5)
        return
    
    # Generar video según formato
    try:
        if args.format == "youtube":
            output = generate_youtube_video(theme=theme, voice=args.voice)
        else:
            output = generate_video(theme=theme, voice=args.voice)
        print(f"\n🎉 ¡Video listo! Ábrelo en: {output}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
