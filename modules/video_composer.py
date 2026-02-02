"""
Compositor de Video con MoviePy
Combina video de fondo, audio y subtítulos para crear el Reel final
"""
import os
from moviepy import (
    VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, ColorClip, ImageClip
)
from moviepy.video.fx import FadeIn, FadeOut, Resize
from config import VIDEO_CONFIG, SUBTITLE_CONFIG, OUTPUT_DIR, TEMP_DIR


class VideoComposer:
    """Compositor de videos para Reels/Shorts"""
    
    def __init__(self):
        """Inicializa el compositor"""
        self.width = VIDEO_CONFIG["width"]
        self.height = VIDEO_CONFIG["height"]
        self.fps = VIDEO_CONFIG["fps"]
    
    def create_hook_overlay(self, hook_text: str, duration: float = 2.5) -> TextClip:
        """
        Crea un overlay de texto grande para el hook inicial (primeros 2-3 segundos)
        
        Args:
            hook_text: Texto del hook
            duration: Duración del overlay
            
        Returns:
            TextClip con efecto de zoom y fade
        """
        print(f"🎬 Creando hook visual: '{hook_text[:40]}...'")
        
        try:
            # Texto grande y dramático
            hook_clip = TextClip(
                hook_text.upper(),
                fontsize=85,
                color="white",
                font="Arial-Bold",
                stroke_color="black",
                stroke_width=4,
                method="caption",
                size=(self.width - 100, None),
                align="center"
            )
            
            # Posición centrada
            hook_clip = hook_clip.set_position(("center", "center"))
            hook_clip = hook_clip.set_duration(duration)
            hook_clip = hook_clip.set_start(0)
            
            # Efecto de fade in y fade out
            hook_clip = hook_clip.crossfadein(0.3)
            hook_clip = hook_clip.crossfadeout(0.5)
            
            return hook_clip
            
        except Exception as e:
            print(f"⚠️ Error creando hook overlay: {e}")
            return None
    
    def create_cta_overlay(self, cta_text: str = "Suscríbete y dime qué opinas abajo",
                           username: str = None, duration: float = 3.0,
                           video_duration: float = None) -> list:
        """
        Crea overlay de llamada a la acción al final del video
        
        Args:
            cta_text: Texto del CTA
            username: Username a mostrar (opcional)
            duration: Duración del CTA
            video_duration: Duración total del video
            
        Returns:
            Lista de TextClips para el CTA
        """
        print(f"📱 Creando CTA: '{cta_text}'")
        
        clips = []
        start_time = video_duration - duration if video_duration else 0
        
        try:
            # Texto principal del CTA
            cta_clip = TextClip(
                cta_text,
                fontsize=55,
                color="white",
                font="Arial-Bold",
                stroke_color="black",
                stroke_width=2,
                method="caption",
                size=(self.width - 150, None),
                align="center"
            )
            
            cta_clip = cta_clip.set_position(("center", self.height * 0.80))
            cta_clip = cta_clip.set_duration(duration)
            cta_clip = cta_clip.set_start(start_time)
            cta_clip = cta_clip.crossfadein(0.5)
            
            clips.append(cta_clip)
            
            # Username si se proporciona
            if username:
                username_clip = TextClip(
                    f"@{username}",
                    fontsize=45,
                    color="#00D4FF",  # Cyan llamativo
                    font="Arial-Bold",
                    stroke_color="black",
                    stroke_width=2,
                )
                
                username_clip = username_clip.set_position(("center", self.height * 0.86))
                username_clip = username_clip.set_duration(duration)
                username_clip = username_clip.set_start(start_time)
                username_clip = username_clip.crossfadein(0.7)
                
                clips.append(username_clip)
            
            return clips
            
        except Exception as e:
            print(f"⚠️ Error creando CTA overlay: {e}")
            return []
    
    def create_ken_burns_clip(self, image_path: str, duration: float,
                               zoom_direction: str = "in",
                               pan_direction: str = None) -> VideoFileClip:
        """
        Crea un video a partir de una imagen con efecto Ken Burns (zoom lento)
        
        Args:
            image_path: Ruta a la imagen
            duration: Duración del video en segundos
            zoom_direction: "in" para zoom in, "out" para zoom out
            pan_direction: "left", "right", "up", "down" o None (opcional)
            
        Returns:
            VideoClip con efecto Ken Burns
        """
        print(f"🎞️ Aplicando efecto Ken Burns ({zoom_direction}, pan: {pan_direction or 'center'})...")
        
        # Cargar imagen
        img_clip = ImageClip(image_path)
        
        # Calcular dimensiones iniciales más grandes para permitir zoom y pan
        # REDUCIDO: de 1.4 a 1.15 para zoom más sutil y menos agresivo
        scale_factor = 1.15  # 15% más grande - movimiento suave y profesional
        
        # Redimensionar imagen para que cubra el frame
        img_w, img_h = img_clip.size
        target_ratio = self.width / self.height
        img_ratio = img_w / img_h
        
        if img_ratio > target_ratio:
            # Imagen más ancha - ajustar por altura
            new_h = int(self.height * scale_factor)
            new_w = int(new_h * img_ratio)
        else:
            # Imagen más alta - ajustar por ancho
            new_w = int(self.width * scale_factor)
            new_h = int(new_w / img_ratio)
        
        img_clip = img_clip.resize((new_w, new_h))
        
        # Función para aplicar zoom gradual con pan
        def zoom_pan_effect(get_frame, t):
            progress = t / duration
            
            if zoom_direction == "in":
                zoom = 1 + (scale_factor - 1) * progress
            else:
                zoom = scale_factor - (scale_factor - 1) * progress
            
            # Aplicar zoom y centrar
            frame = get_frame(t)
            h, w = frame.shape[:2]
            
            # Calcular nuevo tamaño
            new_w = int(w / zoom)
            new_h = int(h / zoom)
            
            # Calcular offset base (centro)
            x_offset = (w - new_w) // 2
            y_offset = (h - new_h) // 2
            
            # Aplicar pan si se especifica
            # REDUCIDO: de 50px a 25px para movimiento más suave
            pan_amount = int(25 * progress)  # Movimiento máximo de 25px
            if pan_direction == "left":
                x_offset -= pan_amount
            elif pan_direction == "right":
                x_offset += pan_amount
            elif pan_direction == "up":
                y_offset -= pan_amount
            elif pan_direction == "down":
                y_offset += pan_amount
            
            # Asegurar que no nos salimos del frame
            x_offset = max(0, min(x_offset, w - new_w))
            y_offset = max(0, min(y_offset, h - new_h))
            
            # Recortar y redimensionar
            cropped = frame[y_offset:y_offset+new_h, x_offset:x_offset+new_w]
            
            from PIL import Image
            import numpy as np
            pil_img = Image.fromarray(cropped)
            pil_img = pil_img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            return np.array(pil_img)
        
        # Aplicar efecto
        final_clip = img_clip.fl(zoom_pan_effect, apply_to=['mask'])
        final_clip = final_clip.set_duration(duration)
        final_clip = final_clip.resize((self.width, self.height))
        
        return final_clip
    
    def create_multi_image_video(self, image_paths: list, duration: float, 
                                  crossfade_duration: float = 0.8,
                                  resolution: tuple = None) -> VideoFileClip:
        """
        Crea un video a partir de múltiples imágenes con transiciones crossfade
        
        Args:
            image_paths: Lista de rutas a las imágenes
            duration: Duración total del video
            crossfade_duration: Duración del crossfade entre imágenes
            resolution: Tupla (width, height), usa self.width/height si es None
            
        Returns:
            VideoFileClip con múltiples imágenes y transiciones
        """
        import random
        
        if not image_paths:
            return None
        
        # Usar resolución personalizada o la por defecto
        width = resolution[0] if resolution else self.width
        height = resolution[1] if resolution else self.height
        
        num_images = len(image_paths)
        segment_duration = duration / num_images
        
        print(f"🎬 Creando video multi-imagen ({num_images} imágenes, {segment_duration:.1f}s cada una)...")
        print(f"   📐 Resolución: {width}x{height}")
        
        # Opciones de pan y zoom para variedad
        pan_options = ["left", "right", "up", "down", None]
        zoom_options = ["in", "out"]
        
        clips = []
        for i, img_path in enumerate(image_paths):
            # Variar el efecto para cada imagen
            pan_dir = pan_options[i % len(pan_options)]
            zoom_dir = zoom_options[i % len(zoom_options)]
            
            print(f"  [{i+1}/{num_images}] Procesando imagen (zoom: {zoom_dir}, pan: {pan_dir})...")
            
            # Crear clip Ken Burns para esta imagen
            clip = self.create_ken_burns_clip(
                img_path,
                segment_duration + crossfade_duration,  # Extra para crossfade
                zoom_direction=zoom_dir,
                pan_direction=pan_dir
            )
            
            # Redimensionar si la resolución es diferente
            if resolution:
                clip = clip.resize((width, height))
            
            # Aplicar crossfade excepto en el primero
            if i > 0:
                clip = clip.crossfadein(crossfade_duration)
            
            clip = clip.set_start(i * segment_duration)
            clips.append(clip)
        
        # Combinar todas las imágenes
        from moviepy import CompositeVideoClip
        final = CompositeVideoClip(clips, size=(width, height))
        final = final.set_duration(duration)
        
        print(f"✓ Video multi-imagen creado ({duration:.1f}s)")
        return final
    
    def prepare_background_video(self, video_path: str, duration: float) -> VideoFileClip:
        """
        Prepara el video de fondo al tamaño y duración correctos
        
        Args:
            video_path: Ruta al video de fondo
            duration: Duración deseada en segundos
            
        Returns:
            VideoFileClip preparado
        """
        print(f"📹 Preparando video de fondo...")
        
        clip = VideoFileClip(video_path)
        
        # Ajustar duración (loop si es necesario)
        if clip.duration < duration:
            # Repetir el video hasta alcanzar la duración
            loops_needed = int(duration / clip.duration) + 1
            clips = [clip] * loops_needed
            clip = concatenate_videoclips(clips)
        
        clip = clip.subclip(0, duration)
        
        # Redimensionar al formato vertical (9:16)
        # Calcular el crop/resize necesario
        target_ratio = self.width / self.height
        clip_ratio = clip.w / clip.h
        
        if clip_ratio > target_ratio:
            # Video más ancho que el target - recortar lados
            new_width = int(clip.h * target_ratio)
            x_center = clip.w / 2
            clip = clip.crop(
                x_center=x_center,
                width=new_width,
                height=clip.h
            )
        else:
            # Video más alto que el target - recortar arriba/abajo
            new_height = int(clip.w / target_ratio)
            y_center = clip.h / 2
            clip = clip.crop(
                y_center=y_center,
                width=clip.w,
                height=new_height
            )
        
        # Redimensionar al tamaño final
        clip = clip.resize((self.width, self.height))
        
        return clip
    
    def create_subtitle_clips(self, text: str, duration: float, 
                              words_per_segment: int = 4) -> list:
        """
        Crea clips de subtítulos animados
        
        Args:
            text: Texto completo a mostrar
            duration: Duración total del video
            words_per_segment: Palabras por segmento de subtítulo
            
        Returns:
            Lista de TextClips
        """
        print(f"📝 Creando subtítulos...")
        
        words = text.split()
        segments = []
        
        # Dividir en segmentos
        for i in range(0, len(words), words_per_segment):
            segment = " ".join(words[i:i + words_per_segment])
            segments.append(segment)
        
        if not segments:
            return []
        
        # Calcular duración por segmento
        segment_duration = duration / len(segments)
        
        subtitle_clips = []
        current_time = 0
        
        for segment in segments:
            try:
                txt_clip = TextClip(
                    segment,
                    fontsize=SUBTITLE_CONFIG["fontsize"],
                    color=SUBTITLE_CONFIG["color"],
                    font=SUBTITLE_CONFIG.get("font", "Arial-Bold"),
                    stroke_color=SUBTITLE_CONFIG["stroke_color"],
                    stroke_width=SUBTITLE_CONFIG["stroke_width"],
                    method=SUBTITLE_CONFIG.get("method", "caption"),
                    size=(SUBTITLE_CONFIG["size"][0], None),
                    align="center"
                )
                
                # Posicionar y establecer timing
                position = SUBTITLE_CONFIG["position"]
                y_pos = int(self.height * position[1])
                
                txt_clip = txt_clip.set_position(("center", y_pos))
                txt_clip = txt_clip.set_start(current_time)
                txt_clip = txt_clip.set_duration(segment_duration)
                
                # Añadir fade in/out suave
                txt_clip = txt_clip.crossfadein(0.15)
                txt_clip = txt_clip.crossfadeout(0.15)
                
                subtitle_clips.append(txt_clip)
                
            except Exception as e:
                print(f"⚠️ Error creando subtítulo: {e}")
            
            current_time += segment_duration
        
        return subtitle_clips
    
    def add_text_overlay(self, text: str, position: tuple = ("center", "top"),
                         fontsize: int = 40, duration: float = None) -> TextClip:
        """
        Crea un overlay de texto adicional (ej: autor, watermark)
        """
        try:
            clip = TextClip(
                text,
                fontsize=fontsize,
                color="white",
                font="Arial",
                stroke_color="black",
                stroke_width=1
            )
            clip = clip.set_position(position)
            if duration:
                clip = clip.set_duration(duration)
            return clip
        except Exception as e:
            print(f"⚠️ Error creando overlay: {e}")
            return None
    
    def create_reel(self, background_video: str, audio_path: str,
                    subtitles_text: str, author: str = None,
                    output_name: str = None, hook_text: str = None,
                    cta_text: str = "Suscríbete y dime qué opinas abajo",
                    username: str = None,
                    target_resolution: tuple = None) -> str:
        """
        Crea el video final tipo Reel/Short o YouTube
        
        Args:
            background_video: Ruta al video de fondo
            audio_path: Ruta al audio de narración
            subtitles_text: Texto para los subtítulos
            author: Autor de la cita (opcional)
            output_name: Nombre del archivo de salida
            hook_text: Texto del hook para mostrar al inicio
            cta_text: Texto de llamada a la acción al final
            username: Username para mostrar en el CTA
            target_resolution: Tupla (width, height) para la resolución de salida
            
        Returns:
            Ruta al video generado
        """
        # Usar resolución personalizada o la por defecto
        width = target_resolution[0] if target_resolution else self.width
        height = target_resolution[1] if target_resolution else self.height
        
        print("🎬 Componiendo video final...")
        print(f"   📐 Resolución: {width}x{height}")
        
        # Cargar audio para conocer duración
        audio = AudioFileClip(audio_path)
        duration = audio.duration + 1.5  # Añadir margen
        
        # Preparar video de fondo
        background = VideoFileClip(background_video)
        
        # Ajustar duración si es necesario
        if background.duration < duration:
            loops_needed = int(duration / background.duration) + 1
            background = concatenate_videoclips([background] * loops_needed)
        background = background.subclip(0, duration)
        
        # Redimensionar al tamaño objetivo
        background = background.resize((width, height))
        
        # Crear capa de oscurecimiento para mejor legibilidad (más opacidad = más profesional)
        overlay = ColorClip(
            size=(width, height),
            color=(0, 0, 0)
        ).set_opacity(0.45).set_duration(duration)
        
        # Crear subtítulos si se proporciona texto
        subtitle_clips = []
        if subtitles_text:
            subtitle_clips = self.create_subtitle_clips(subtitles_text, duration)
        
        # Componer todas las capas
        layers = [background, overlay] + subtitle_clips
        
        # 🎬 HOOK VISUAL al inicio (primeros 2.5 segundos)
        if hook_text:
            hook_clip = self.create_hook_overlay(hook_text, duration=2.5)
            if hook_clip:
                layers.append(hook_clip)
        
        # Añadir autor si existe
        if author:
            author_clip = self.add_text_overlay(
                f"- {author}",
                position=("center", height * 0.88),
                fontsize=35,
                duration=duration
            )
            if author_clip:
                author_clip = author_clip.set_start(duration * 0.6)
                author_clip = author_clip.crossfadein(0.5)
                layers.append(author_clip)
        
        # 📱 CTA al final (últimos 4 segundos) - Para TODOS los videos
        # Si no se especifica cta_text, usar uno por defecto
        default_cta = "Suscríbete y dime qué opinas abajo"
        final_cta = cta_text if cta_text else default_cta
        
        cta_clips = self.create_cta_overlay(
            cta_text=final_cta,
            username=None,  # Sin username
            duration=4.0,   # 4 segundos al final
            video_duration=duration
        )
        layers.extend(cta_clips)
        
        # Componer video final
        final = CompositeVideoClip(layers, size=(width, height))
        
        # Añadir audio
        final = final.set_audio(audio)
        
        # Aplicar fade in/out al video completo
        final = fadein(final, 0.5)
        final = fadeout(final, 0.5)
        
        # Generar nombre de salida
        if not output_name:
            import time
            output_name = f"reel_{int(time.time())}"
        
        output_path = os.path.join(OUTPUT_DIR, f"{output_name}.mp4")
        
        # Exportar
        print(f"💾 Exportando video a: {output_path}")
        final.write_videofile(
            output_path,
            fps=self.fps,
            codec=VIDEO_CONFIG["codec"],
            audio_codec=VIDEO_CONFIG["audio_codec"],
            bitrate=VIDEO_CONFIG["bitrate"],
            preset="medium",
            threads=4
        )
        
        # Limpiar
        final.close()
        background.close()
        audio.close()
        
        print(f"✅ Video creado exitosamente: {output_path}")
        return output_path
    
    def create_simple_reel(self, background_video: str, audio_path: str,
                           text: str, output_name: str = None) -> str:
        """
        Versión simplificada para crear un Reel rápido
        """
        return self.create_reel(
            background_video=background_video,
            audio_path=audio_path,
            subtitles_text=text,
            output_name=output_name
        )
    
    def split_youtube_to_shorts(self, youtube_video_path: str, 
                                 num_segments: int = 7,
                                 output_dir: str = None) -> list:
        """
        Divide un video de YouTube horizontal en shorts verticales
        
        Args:
            youtube_video_path: Ruta al video de YouTube (1920x1080)
            num_segments: Número de segmentos a crear
            output_dir: Directorio de salida (usa OUTPUT_DIR por defecto)
            
        Returns:
            Lista de rutas a los shorts generados
        """
        if not os.path.exists(youtube_video_path):
            print(f"❌ Video no encontrado: {youtube_video_path}")
            return []
        
        output_dir = output_dir or OUTPUT_DIR
        
        # Obtener duración con ffprobe
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
             '-of', 'default=noprint_wrappers=1:nokey=1', youtube_video_path],
            capture_output=True, text=True
        )
        total_duration = float(result.stdout.strip())
        
        # Duración fija de 30 segundos por short
        segment_duration = 30.0
        num_segments = int(total_duration / segment_duration)
        
        print(f"\n🔪 Dividiendo video en shorts de 30 segundos...")
        print(f"   ⏱️ Duración total: {total_duration:.1f}s")
        print(f"   📹 Shorts a generar: {num_segments} (30s cada uno)")
        
        shorts_paths = []
        base_name = os.path.splitext(os.path.basename(youtube_video_path))[0]
        
        for i in range(num_segments):
            start_time = i * segment_duration
            duration = segment_duration
            
            print(f"\n  [Short {i+1}/{num_segments}] {start_time:.1f}s - {start_time + duration:.1f}s")
            
            output_path = os.path.join(output_dir, f"{base_name}_short_{i+1:02d}.mp4")
            
            # Usar ffmpeg directamente para cortar, hacer crop y añadir CTA
            # El crop: 1920x1080 -> 607x1080 (centro) -> resize a 1080x1920
            # crop=607:1080:656:0 (ancho:alto:x:y)  x = (1920-607)/2 = 656
            # drawtext añade el CTA en los últimos 4 segundos
            cta_text = "Suscríbete y dime qué opinas abajo"
            
            # Calcular cuando mostrar el CTA (últimos 4 segundos)
            cta_start = duration - 4
            
            # Filtro complejo: crop + scale + CTA text
            vf_filter = f"crop=607:1080:656:0,scale=1080:1920,drawtext=text='{cta_text}':fontsize=45:fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h*0.82:enable='gte(t,{cta_start})'"
            
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start_time),
                '-i', youtube_video_path,
                '-t', str(duration),
                '-vf', vf_filter,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-c:a', 'aac',
                '-b:a', '128k',
                output_path
            ]
            
            subprocess.run(cmd, capture_output=True)
            
            if os.path.exists(output_path):
                shorts_paths.append(output_path)
                print(f"   ✓ Guardado: {output_path}")
            else:
                print(f"   ❌ Error al crear short {i+1}")
        
        print(f"\n✅ {len(shorts_paths)} shorts generados!")
        return shorts_paths


# Test del módulo
if __name__ == "__main__":
    composer = VideoComposer()
    print("VideoComposer listo para usar")
    print(f"Resolución: {composer.width}x{composer.height}")
    print(f"FPS: {composer.fps}")

