#!/usr/bin/env python3
"""
📚 BIBLIOTECA DE VIDEOS - Sistema de gestión

Comandos:
    python video_library.py list              # Ver videos en biblioteca
    python video_library.py add [N]           # Generar N clips nuevos (default: 3)
    python video_library.py short             # Crear short aleatorio de 30s
    python video_library.py clean             # Limpiar videos temporales
"""
import os
import sys
import glob
import random
import shutil
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from modules.image_generator import ImageGenerator
from config import OUTPUT_DIR, TEMP_DIR, ASSETS_DIR

# Directorio de la biblioteca de videos
LIBRARY_DIR = os.path.join(ASSETS_DIR, "video_library")
os.makedirs(LIBRARY_DIR, exist_ok=True)


def list_library():
    """Lista todos los videos en la biblioteca"""
    videos = glob.glob(os.path.join(LIBRARY_DIR, "*.mp4"))
    
    print("\n📚 BIBLIOTECA DE VIDEOS")
    print("=" * 50)
    
    if not videos:
        print("   (vacía)")
        return
    
    total_duration = 0
    for i, v in enumerate(sorted(videos), 1):
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(v)
        duration = clip.duration
        clip.close()
        total_duration += duration
        
        name = os.path.basename(v)
        print(f"   {i}. {name} ({duration:.1f}s)")
    
    print("=" * 50)
    print(f"   Total: {len(videos)} videos ({total_duration:.0f}s)")
    print(f"   Shorts posibles: {int(total_duration / 30)}")


def add_to_library(count: int = 3):
    """Genera N clips nuevos y los añade a la biblioteca"""
    print(f"\n🎬 Generando {count} clips nuevos para la biblioteca...")
    print("=" * 50)
    
    gen = ImageGenerator()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for i in range(count):
        print(f"\n[{i+1}/{count}] Generando clip...")
        
        prompt = gen.get_random_prompt()
        print(f"   📝 {prompt[:50]}...")
        
        # Generar imagen
        print("   🎨 Generando imagen con Kino XL...")
        image_path = gen._generate_with_leonardo(prompt, theme="epic")
        
        if not image_path:
            print("   ❌ Error generando imagen")
            continue
        
        # Animar
        print("   🔥 Animando con Motion 2.0 Fast...")
        video_path = gen.animate_image_with_motion_fast(image_path, resolution="480p")
        
        if video_path:
            # Guardar en biblioteca
            lib_name = f"epic_{timestamp}_{i+1}.mp4"
            lib_path = os.path.join(LIBRARY_DIR, lib_name)
            shutil.copy2(video_path, lib_path)
            print(f"   ✅ Guardado: {lib_name}")
        else:
            print("   ❌ Error animando")
    
    print("\n" + "=" * 50)
    print(f"✅ Clips añadidos a la biblioteca")
    list_library()


def create_short():
    """Crea un short de 30s con videos aleatorios de la biblioteca"""
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    
    videos = glob.glob(os.path.join(LIBRARY_DIR, "*.mp4"))
    
    if len(videos) < 3:
        print("❌ Necesitas al menos 3 videos en la biblioteca")
        print("   Usa: python video_library.py add 6")
        return
    
    print("\n🎬 Creando SHORT aleatorio de 30 segundos...")
    print("=" * 50)
    
    # Seleccionar videos aleatorios hasta completar ~30s
    random.shuffle(videos)
    
    selected = []
    total_duration = 0
    
    for v in videos:
        if total_duration >= 30:
            break
        selected.append(v)
        clip = VideoFileClip(v)
        total_duration += clip.duration
        clip.close()
    
    print(f"📽️ Videos seleccionados: {len(selected)}")
    
    # Concatenar - resize cada clip individualmente antes
    clips = []
    for v in selected:
        clip = VideoFileClip(v)
        
        # Resize cada clip a 1080x1920 antes de concatenar
        # Calcular el crop necesario para mantener aspect ratio
        target_ratio = 1080 / 1920  # 9:16
        clip_ratio = clip.w / clip.h
        
        if clip_ratio > target_ratio:
            # Video más ancho - recortar lados
            new_width = int(clip.h * target_ratio)
            clip = clip.crop(x_center=clip.w/2, width=new_width, height=clip.h)
        else:
            # Video más alto - recortar arriba/abajo
            new_height = int(clip.w / target_ratio)
            clip = clip.crop(y_center=clip.h/2, width=clip.w, height=new_height)
        
        # Ahora hacer resize al tamaño final
        clip = clip.resize((1080, 1920))
        
        clips.append(clip)
        print(f"   + {os.path.basename(v)}")
    
    final_clip = concatenate_videoclips(clips, method="compose")
    
    # Cortar a 30s si es necesario
    if final_clip.duration > 30:
        final_clip = final_clip.subclip(0, 30)
    
    # Guardar
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_DIR, f"random_short_{timestamp}.mp4")
    
    print(f"\n💾 Guardando short...")
    final_clip.write_videofile(output_path, fps=30, codec="libx264", audio=False)
    
    for c in clips:
        c.close()
    final_clip.close()
    
    print("\n" + "=" * 50)
    print(f"✅ SHORT CREADO: {output_path}")
    print(f"   ⏱️ Duración: ~30 segundos")
    
    os.system(f'open "{output_path}"')


def save_current_clips():
    """Guarda los clips actuales en la biblioteca"""
    videos_dir = os.path.join(TEMP_DIR, "generated_images")
    clips = glob.glob(os.path.join(videos_dir, "motion_fast_*.mp4"))
    
    if not clips:
        print("❌ No hay clips para guardar")
        return
    
    print(f"\n💾 Guardando {len(clips)} clips en la biblioteca...")
    
    for clip in clips:
        name = os.path.basename(clip)
        dest = os.path.join(LIBRARY_DIR, name)
        if not os.path.exists(dest):
            shutil.copy2(clip, dest)
            print(f"   ✅ {name}")
    
    print("\n✅ Clips guardados")
    list_library()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        list_library()
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_library()
    
    elif command == "add":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        add_to_library(count)
    
    elif command == "short":
        create_short()
    
    elif command == "save":
        save_current_clips()
    
    elif command == "clean":
        videos_dir = os.path.join(TEMP_DIR, "generated_images")
        for f in glob.glob(os.path.join(videos_dir, "motion_fast_*.mp4")):
            os.remove(f)
        print("🗑️ Clips temporales eliminados")
    
    else:
        print(f"❌ Comando desconocido: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
