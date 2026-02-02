"""
Módulo de legendas word-by-word para vídeos verticais
Estilo TikTok/Shorts com highlight em cada palavra
Usa FFmpeg diretamente para evitar dependência do ImageMagick
Usa Whisper para sincronização precisa com a voz
"""

import subprocess
import os
import json


def split_into_words(text):
    """Divide texto em palavras mantendo pontuação"""
    import re
    # Remove múltiplos espaços e quebras de linha
    text = re.sub(r'\s+', ' ', text.strip())
    # Divide em palavras
    words = text.split()
    return words


def get_word_timestamps_from_audio(audio_path):
    """
    Usa Whisper para extrair timestamps precisos de cada palavra do áudio
    Retorna lista de dicts com {word, start, end}
    """
    try:
        import whisper
        print("   🎤 Transcrevendo áudio com Whisper para timing preciso...")
        
        # Carregar modelo Whisper (tiny é rápido e suficiente para timing)
        model = whisper.load_model("tiny")
        
        # Transcrever com word timestamps
        result = model.transcribe(
            audio_path,
            word_timestamps=True,
            language=None  # Auto-detect
        )
        
        # Extrair palavras com timestamps
        word_timings = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                word_timings.append({
                    'word': word_info['word'].strip(),
                    'start': word_info['start'],
                    'end': word_info['end']
                })
        
        print(f"   ✅ {len(word_timings)} palavras com timestamps extraídas")
        return word_timings
        
    except ImportError:
        print("   ⚠️ Whisper não instalado, usando distribuição uniforme")
        return None
    except Exception as e:
        print(f"   ⚠️ Erro ao usar Whisper: {e}, usando distribuição uniforme")
        return None


def calculate_word_timings(words, total_duration):
    """
    Calcula timestamps para cada palavra
    Distribui o tempo total igualmente entre as palavras (fallback)
    """
    num_words = len(words)
    if num_words == 0:
        return []
    
    duration_per_word = total_duration / num_words
    
    timings = []
    current_time = 0
    
    for word in words:
        timings.append({
            'word': word,
            'start': current_time,
            'end': current_time + duration_per_word
        })
        current_time += duration_per_word
    
    return timings


def add_subtitles_with_ffmpeg(video_path, text, audio_duration, output_path, audio_path=None):
    """
    Adiciona legendas word-by-word usando FFmpeg drawtext
    Se audio_path fornecido, usa Whisper para timing preciso
    """
    print("📝 Gerando legendas word-by-word com FFmpeg...")
    
    # Tentar usar Whisper para timing preciso
    word_timings = None
    if audio_path:
        word_timings = get_word_timestamps_from_audio(audio_path)
    
    # Se Whisper falhar, usar distribuição uniforme
    if not word_timings:
        words = split_into_words(text)
        print(f"   Total de palavras: {len(words)}")
        word_timings = calculate_word_timings(words, audio_duration)
    
    if not word_timings:
        print("   ⚠️ Nenhuma palavra para legendar")
        subprocess.run(["cp", video_path, output_path])
        return False
    
    # Criar filtro drawtext do FFmpeg
    drawtext_filters = []
    
    for timing in word_timings:
        word = timing['word'].replace("'", "\\'").replace(":", "\\:")  # Escapar caracteres especiais
        start = timing['start']
        end = timing['end']
        
        # drawtext com enable para mostrar apenas no período específico
        filter_str = (
            f"drawtext=text='{word}':"
            f"fontfile=/System/Library/Fonts/Supplemental/Impact.ttf:"
            f"fontsize=55:"
            f"fontcolor=white:"
            f"borderw=3:"
            f"bordercolor=black:"
            f"x=(w-text_w)/2:"  # Centro horizontal
            f"y=(h-text_h)/2:"  # Centro vertical
            f"enable='between(t,{start:.3f},{end:.3f})'"
        )
        drawtext_filters.append(filter_str)
    
    # Concatenar todos os filtros com vírgula
    full_filter = ",".join(drawtext_filters)
    
    # Comando FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", full_filter,
        "-codec:a", "copy",
        output_path
    ]
    
    print(f"   Aplicando {len(word_timings)} legendas...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"⚠️ Erro ao adicionar legendas: {result.stderr}")
        # Se falhar, copiar vídeo sem legendas
        subprocess.run(["cp", video_path, output_path])
        return False
    
    print("   ✅ Legendas adicionadas com sucesso!")
    return True


def generate_srt(word_timings, output_path):
    """
    Gera arquivo SRT das legendas (opcional, para backup)
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, timing in enumerate(word_timings, 1):
            start = format_srt_time(timing['start'])
            end = format_srt_time(timing['end'])
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{timing['word']}\n\n")


def format_srt_time(seconds):
    """Formata segundos para formato SRT: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
