"""
Módulo de legendas word-by-word para vídeos verticais
Estilo TikTok/Shorts com highlight em cada palavra
"""

from moviepy.editor import TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip


def split_into_words(text):
    """Divide texto em palavras mantendo pontuação"""
    import re
    # Remove múltiplos espaços e quebras de linha
    text = re.sub(r'\s+', ' ', text.strip())
    # Divide em palavras
    words = text.split()
    return words


def calculate_word_timings(words, total_duration):
    """
    Calcula timestamps para cada palavra
    Distribui o tempo total igualmente entre as palavras
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


def create_word_clip(word_data, video_size):
    """
    Cria um TextClip para uma palavra individual
    Estilo: fonte grande, bold, outline branco, sombra
    """
    word = word_data['word']
    start = word_data['start']
    end = word_data['end']
    duration = end - start
    
    # Configurações de estilo
    fontsize = 70
    color = 'yellow'
    font = 'Impact'  # Fonte bold estilo TikTok (ou Arial-Bold)
    
    try:
        txt_clip = TextClip(
            word,
            fontsize=fontsize,
            color=color,
            font=font,
            stroke_color='black',
            stroke_width=3,
            method='caption',
            size=(video_size[0] - 100, None)  # Largura com margem
        ).set_position(('center', 200)).set_start(start).set_duration(duration)
        
        return txt_clip
    except Exception as e:
        print(f"⚠️ Erro ao criar clip para '{word}': {e}")
        # Fallback sem stroke
        txt_clip = TextClip(
            word,
            fontsize=fontsize,
            color=color,
            font='Arial-Bold',
            method='caption',
            size=(video_size[0] - 100, None)
        ).set_position(('center', 200)).set_start(start).set_duration(duration)
        
        return txt_clip


def add_subtitles_to_video(video_clip, text, audio_duration):
    """
    Adiciona legendas word-by-word ao vídeo
    
    Args:
        video_clip: VideoClip do moviepy
        text: Texto completo do áudio
        audio_duration: Duração do áudio em segundos
    
    Returns:
        CompositeVideoClip com legendas
    """
    print("📝 Gerando legendas word-by-word...")
    
    # Dividir em palavras
    words = split_into_words(text)
    print(f"   Total de palavras: {len(words)}")
    
    # Calcular timings
    word_timings = calculate_word_timings(words, audio_duration)
    
    # Criar clips de texto
    video_size = video_clip.size
    text_clips = []
    
    for word_data in word_timings:
        try:
            clip = create_word_clip(word_data, video_size)
            text_clips.append(clip)
        except Exception as e:
            print(f"⚠️ Erro ao processar palavra '{word_data['word']}': {e}")
            continue
    
    if not text_clips:
        print("⚠️ Nenhuma legenda criada, retornando vídeo original")
        return video_clip
    
    # Compor vídeo + legendas
    print(f"   Adicionando {len(text_clips)} legendas ao vídeo...")
    final_video = CompositeVideoClip([video_clip] + text_clips)
    
    return final_video


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
