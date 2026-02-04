"""
Módulo de legendas word-by-word para vídeos verticais
Estilo TikTok/Shorts com highlight em cada palavra
Usa FFmpeg diretamente para evitar dependência do ImageMagick
Usa Whisper para sincronização precisa com a voz
"""

import subprocess
import os
import json


def is_keyword(word):
    """
    Determina se uma palavra é palavra-chave (substantivo importante)
    Critérios: 
    - Palavras longas (>5 caracteres)
    - Não é artigo/preposição/conjunção
    """
    # Remover pontuação para análise
    clean_word = word.strip('.,!?;:').lower()
    
    # Lista de palavras comuns que NÃO são keywords (artigos, preposições, etc)
    stop_words = {
        # Espanhol
        'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
        'de', 'del', 'en', 'con', 'por', 'para', 'es', 'son',
        'que', 'como', 'pero', 'sino', 'si', 'cuando', 'donde',
        'entre', 'hasta', 'desde', 'sobre', 'bajo', 'hacia',
        # Inglês
        'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for',
        'and', 'or', 'but', 'if', 'as', 'with', 'from', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would'
    }
    
    # Se está na lista de stop words, não é keyword
    if clean_word in stop_words:
        return False
    
    # Se tem mais de 5 caracteres, provavelmente é importante
    if len(clean_word) > 5:
        return True
    
    # Se tem 4-5 caracteres e é substantivo/verbo (heurística simples)
    if len(clean_word) >= 4:
        return True
    
    return False


def group_words_into_chunks(word_timings, max_words_per_chunk=3):
    """
    Agrupa TODAS as palavras em chunks de 2-3 palavras
    Mantém informação se chunk contém keyword
    """
    if not word_timings:
        return []
    
    chunks = []
    current_chunk = []
    
    for word_timing in word_timings:
        current_chunk.append(word_timing)
        
        # Criar chunk quando atingir max_words ou fim de frase (pontuação)
        word = word_timing['word']
        has_punctuation = any(p in word for p in ['.', '!', '?'])
        
        if len(current_chunk) >= max_words_per_chunk or has_punctuation:
            # Criar chunk com todas as palavras
            chunk_words = [w['word'] for w in current_chunk]
            chunk = {
                'text': ' '.join(chunk_words),
                'start': current_chunk[0]['start'],
                'end': current_chunk[-1]['end'],
                'words': current_chunk
            }
            chunks.append(chunk)
            current_chunk = []
    
    # Adicionar último chunk se sobrou algo
    if current_chunk:
        chunk_words = [w['word'] for w in current_chunk]
        chunk = {
            'text': ' '.join(chunk_words),
            'start': current_chunk[0]['start'],
            'end': current_chunk[-1]['end'],
            'words': current_chunk
        }
        chunks.append(chunk)
    
    return chunks


def has_keyword_in_chunk(chunk):
    """Verifica se há pelo menos uma palavra-chave no chunk"""
    for word_timing in chunk.get('words', []):
        if is_keyword(word_timing['word']):
            return True
    return False


def split_into_words(text):
    """Divide texto em palavras mantendo pontuação"""
    import re
    # Remove múltiplos espaços e quebras de linha
    text = re.sub(r'\s+', ' ', text.strip())
    # Divide em palavras
    words = text.split()
    return words


def get_word_timestamps_from_audio(audio_path, expected_words=None):
    """
    Usa Whisper para extrair timestamps precisos de cada palavra do áudio
    Se expected_words fornecido, mapeia os timestamps para essas palavras
    Retorna lista de dicts com {word, start, end}
    """
    try:
        import whisper
        print("   🎤 Detectando timing de palavras com Whisper...")
        
        # Carregar modelo Whisper (tiny é rápido e suficiente para timing)
        model = whisper.load_model("tiny")
        
        # Transcrever com word timestamps
        result = model.transcribe(
            audio_path,
            word_timestamps=True,
            language=None  # Auto-detect
        )
        
        # Extrair timestamps do Whisper
        whisper_timings = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                whisper_timings.append({
                    'word': word_info['word'].strip(),
                    'start': word_info['start'],
                    'end': word_info['end']
                })
        
        print(f"   ✅ Whisper detectou {len(whisper_timings)} palavras")
        
        # Se temos palavras esperadas, mapear timestamps para elas
        if expected_words and len(expected_words) > 0:
            print(f"   🔄 Mapeando {len(expected_words)} palavras do texto original para os timestamps")
            
            # Se quantidade é similar (±2 palavras), fazer mapeamento 1:1
            if abs(len(expected_words) - len(whisper_timings)) <= 2:
                word_timings = []
                prev_end = 0
                for i, word in enumerate(expected_words):
                    # Usar o timestamp correspondente ou o último disponível
                    idx = min(i, len(whisper_timings) - 1)
                    start = whisper_timings[idx]['start']
                    end = whisper_timings[idx]['end']
                    
                    # Garantir que não há sobreposição - se start < prev_end, ajustar
                    if start < prev_end:
                        start = prev_end
                        # Ajustar end também se necessário
                        if end <= start:
                            end = start + 0.3  # Mínimo 300ms por palavra
                    
                    word_timings.append({
                        'word': word,
                        'start': start,
                        'end': end
                    })
                    prev_end = end
                    
                print(f"   ✅ Mapeamento 1:1 concluído (sem sobreposição)")
                return word_timings
            else:
                print(f"   ⚠️ Diferença grande: {len(expected_words)} esperadas vs {len(whisper_timings)} detectadas")
                print(f"   📝 Palavras esperadas: {' '.join(expected_words[:5])}...")
                print(f"   🎤 Whisper detectou: {' '.join([w['word'] for w in whisper_timings[:5]])}...")
        
        return whisper_timings
        
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
    print(f"   📄 Texto: {text[:100]}...")
    print(f"   🎤 Audio: {audio_path}")
    
    # Dividir texto em palavras ANTES de usar Whisper
    words = split_into_words(text)
    print(f"   📝 Total de palavras no texto: {len(words)}")
    
    # Tentar usar Whisper para timing preciso, mas mantendo nosso texto
    word_timings = None
    if audio_path:
        print(f"   🔍 Verificando audio_path existe: {os.path.exists(audio_path) if audio_path else 'None'}")
        word_timings = get_word_timestamps_from_audio(audio_path, expected_words=words)
    
    # Se Whisper falhar, usar distribuição uniforme
    if not word_timings:
        print("   ⚠️ Whisper não retornou timings, usando distribuição uniforme")
        word_timings = calculate_word_timings(words, audio_duration)
    
    print(f"   ✅ Usando {len(word_timings)} palavras com timing")
    
    # Agrupar todas as palavras em chunks de 2-3 palavras
    chunks = group_words_into_chunks(word_timings, max_words_per_chunk=3)
    print(f"   📦 Agrupadas em {len(chunks)} chunks (texto completo)")
    
    if not chunks:
        print("   ⚠️ Nenhuma palavra para legendar")
        subprocess.run(["cp", video_path, output_path])
        return False
    
    # Criar filtro drawtext do FFmpeg
    # Mostrar grupos de 2-3 palavras juntas como texto único
    # Animação entrada: fade in + slide up (0.2s)
    # Animação saída: fade out (0.15s)
    drawtext_filters = []
    
    # Criar arquivos temporários para textos com caracteres problemáticos
    import tempfile
    temp_text_files = []
    
    # Parâmetros de animação
    FADE_IN_DURATION = 0.2  # Duração do fade in e slide up
    FADE_OUT_DURATION = 0.15  # Duração do fade out
    
    # Iterar sobre chunks (grupos de palavras)
    for chunk_idx, chunk in enumerate(chunks):
        text = chunk['text']  # Texto completo do chunk
        start = chunk['start']
        end = chunk['end']
        
        # Configuração uniforme para todos os chunks
        color = "white"
        fontsize = 60
        borderw = 5
        
        # Animação de entrada: alpha (fade in) + posição Y (slide up)
        fade_in_end = start + FADE_IN_DURATION
        fade_out_start = end - FADE_OUT_DURATION
        
        # Alpha animation (fade in/out)
        alpha_expr = (
            f"if(lt(t,{start}),0,"  # Antes: invisível
            f"if(lt(t,{fade_in_end}),"  # Fade in
            f"(t-{start})/{FADE_IN_DURATION},"  # 0 -> 1
            f"if(lt(t,{fade_out_start}),1,"  # Meio: visível
            f"if(lt(t,{end}),"  # Fade out
            f"1-((t-{fade_out_start})/{FADE_OUT_DURATION}),"  # 1 -> 0
            f"0))))"  # Depois: invisível
        )
        
        # Posição Y animation (slide up na entrada)
        base_y = "(h-text_h)/2"
        slide_distance = 40
        y_expr = (
            f"if(lt(t,{fade_in_end}),"
            f"{base_y}+{slide_distance}-({slide_distance}*(t-{start})/{FADE_IN_DURATION}),"
            f"{base_y})"
        )
        
        # Posição X: centralizado
        x_expr = "(w-text_w)/2"
        
        # Se texto tem apóstrofo ou caracteres especiais, usar textfile
        if "'" in text or '"' in text or '\\' in text:
            # Criar arquivo temporário para o texto
            tf = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
            tf.write(text)
            tf.close()
            temp_text_files.append(tf.name)
            
            filter_str = (
                f"drawtext=textfile='{tf.name}':"
                f"fontfile=/System/Library/Fonts/Supplemental/Impact.ttf:"
                f"fontsize={fontsize}:"
                f"fontcolor={color}:"
                f"borderw={borderw}:"
                f"bordercolor=black:"
                f"shadowcolor=black@0.8:"
                f"shadowx=3:"
                f"shadowy=3:"
                f"alpha='{alpha_expr}':"
                f"x='{x_expr}':"
                f"y='{y_expr}':"
                f"enable='between(t,{start:.3f},{end:.3f})'"
            )
        else:
            # Textos normais podem usar text direto
            text_escaped = text.replace(":", "\\:")
            filter_str = (
                f"drawtext=text='{text_escaped}':"
                f"fontfile=/System/Library/Fonts/Supplemental/Impact.ttf:"
                f"fontsize={fontsize}:"
                f"fontcolor={color}:"
                f"borderw={borderw}:"
                f"bordercolor=black:"
                f"shadowcolor=black@0.8:"
                f"shadowx=3:"
                f"shadowy=3:"
                f"alpha='{alpha_expr}':"
                f"x='{x_expr}':"
                f"y='{y_expr}':"
                f"enable='between(t,{start:.3f},{end:.3f})'"
            )
        drawtext_filters.append(filter_str)
    
    # Concatenar todos os filtros com vírgula
    full_filter = ",".join(drawtext_filters)
    
    # Log do primeiro filtro para debug
    if drawtext_filters:
        print(f"   🔍 Exemplo de filtro (primeiro chunk): {drawtext_filters[0][:150]}...")
    
    # Comando FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", full_filter,
        "-codec:a", "copy",
        output_path
    ]
    
    print(f"   Aplicando {len(chunks)} legendas (grupos de 2-3 palavras)...")
    print(f"   🎬 FFmpeg comando: ffmpeg -y -i {video_path} -vf [filtro] -codec:a copy {output_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Limpar arquivos temporários
    for tf in temp_text_files:
        try:
            os.remove(tf)
        except:
            pass
    
    if result.returncode != 0:
        print(f"⚠️ Erro ao adicionar legendas!")
        # Salvar erro completo em arquivo para debug
        error_log = "/tmp/ffmpeg_subtitle_error.log"
        with open(error_log, 'w') as f:
            f.write("STDERR:\n")
            f.write(result.stderr)
            f.write("\n\nSTDOUT:\n")
            f.write(result.stdout)
            f.write("\n\nFILTRO:\n")
            f.write(full_filter[:2000])
        print(f"   ❌ Log completo salvo em: {error_log}")
        print(f"   Stderr (primeiras linhas): {result.stderr[:300]}")
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
