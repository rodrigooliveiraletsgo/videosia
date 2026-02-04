#!/usr/bin/env python3
"""
Script de teste para legendas animadas
Gera um vídeo curto para testar as animações
"""

import os
import subprocess
from modules.subtitles import add_subtitles_with_ffmpeg

# Configuração
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def test_animated_subtitles():
    """Testa legendas animadas em um vídeo existente"""
    
    # Procura por um vídeo recente para usar como teste
    import glob
    import subprocess
    
    # Buscar vídeos LIMPOS da biblioteca (sem legendas)
    video_files = glob.glob("assets/video_library/*.mp4")
    
    if not video_files:
        print("❌ Nenhum vídeo encontrado")
        print("   Adicione vídeos em assets/video_library/ ou output/")
        return
    
    # Usar o primeiro vídeo disponível
    video_path = video_files[0]
    
    # Primeiro, remover o áudio do vídeo original
    temp_video_no_audio = "temp/video_no_audio.mp4"
    os.makedirs("temp", exist_ok=True)
    
    print(f"\n🔇 Removendo áudio antigo do vídeo base...")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-an",  # Remove todos os streams de áudio
        "-c:v", "copy",
        temp_video_no_audio
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    
    # Usar o vídeo sem áudio como base
    video_path = temp_video_no_audio
    
    # Criar áudio de teste com elevenlabs ou edge-tts
    print("\n🎤 Gerando áudio de teste...")
    test_text = "La disciplina es el puente entre las metas y los logros"
    
    # Tentar ElevenLabs primeiro
    audio_path = None
    try:
        from modules.tts_engine import generate_tts
        audio_path = "temp/test_audio.mp3"
        os.makedirs("temp", exist_ok=True)
        generate_tts(test_text, audio_path, "es")
        print(f"   ✅ Áudio gerado com ElevenLabs")
    except Exception as e:
        print(f"   ⚠️ ElevenLabs falhou: {e}")
        # Fallback: usar Edge TTS
        try:
            import edge_tts
            import asyncio
            audio_path = "temp/test_audio.mp3"
            os.makedirs("temp", exist_ok=True)
            
            async def generate_edge():
                communicate = edge_tts.Communicate(test_text, "es-ES-AlvaroNeural")
                await communicate.save(audio_path)
            
            asyncio.run(generate_edge())
            print(f"   ✅ Áudio gerado com Edge TTS")
        except Exception as e2:
            print(f"   ❌ Não foi possível gerar áudio: {e2}")
            # Usar vídeo sem áudio
            audio_path = None
    
    print(f"\n🎬 Testando animações em: {os.path.basename(video_path)}")
    
    if audio_path:
        print(f"🎤 Usando áudio: {os.path.basename(audio_path)}")
        
        # Pegar duração do áudio
        import subprocess
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path
        ], capture_output=True, text=True)
        audio_duration = float(result.stdout.strip())
    else:
        # Usar duração fixa se não tiver áudio
        audio_duration = 5.0
        print(f"⚠️ Sem áudio, usando duração fixa: {audio_duration}s")
    
    # Gerar vídeo intermediário com legendas (sem áudio ainda)
    temp_video_with_subs = os.path.join("temp", "temp_with_subtitles.mp4")
    os.makedirs("temp", exist_ok=True)
    
    print(f"\n🎨 Gerando legendas animadas...")
    print(f"   ✨ Efeitos: Scale + Color Highlight + Glow")
    print(f"   📝 Texto: {test_text}")
    print(f"   ⏱️  Duração: {audio_duration:.2f}s")
    
    success = add_subtitles_with_ffmpeg(
        video_path=video_path,
        text=test_text,
        audio_duration=audio_duration,
        output_path=temp_video_with_subs,
        audio_path=audio_path
    )
    
    if success and audio_path:
        # Agora adicionar o áudio correto ao vídeo com legendas
        output_path = os.path.join(OUTPUT_DIR, "test_animated_subtitles.mp4")
        print(f"\n🔊 Adicionando áudio de teste ao vídeo...")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", temp_video_with_subs,
            "-i", audio_path,
            "-map", "0:v",  # vídeo do primeiro input
            "-map", "1:a",  # áudio do segundo input
            "-c:v", "copy",  # copiar vídeo sem recodificar
            "-c:a", "aac",   # codificar áudio em aac
            "-shortest",     # duração do menor stream
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ Áudio adicionado com sucesso!")
            success = True
        else:
            print(f"   ⚠️ Erro ao adicionar áudio: {result.stderr[:200]}")
            # Usar vídeo sem áudio como fallback
            subprocess.run(["cp", temp_video_with_subs, output_path])
            success = True
    else:
        output_path = temp_video_with_subs
    
    if success:
        print(f"\n✅ Vídeo de teste criado: {output_path}")
        print(f"   🎬 Abra o arquivo para ver as animações!")
        
        # Tentar abrir automaticamente no macOS
        try:
            subprocess.run(["open", output_path])
            print(f"   👀 Abrindo vídeo automaticamente...")
        except:
            pass
    else:
        print(f"\n❌ Erro ao criar vídeo de teste")


if __name__ == "__main__":
    print("=" * 60)
    print("🎬 TESTE DE LEGENDAS ANIMADAS")
    print("=" * 60)
    test_animated_subtitles()
