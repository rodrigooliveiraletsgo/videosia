#!/usr/bin/env python3
"""
🎬 GENERADOR DE SHORTS BILINGÜES – NARCISISMO & RELAÇÕES TÓXICAS v2.0
Gera 1 roteiro mestre → 2 vídeos (ES + EN)

Nicho:
Conscientização sobre narcisismo, abuso emocional,
relacionamentos tóxicos, manipulação e gaslighting
"""

import os
import json
import random
import subprocess
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from modules.tts_engine import TTSEngine
from config import OUTPUT_DIR, TEMP_DIR, ASSETS_DIR, GEMINI_API_KEY
from google import genai

LIBRARY_DIR = os.path.join(ASSETS_DIR, "video_library")

# ============================================================
# CATEGORIAS – NARCISISMO & RELAÇÕES TÓXICAS
# ============================================================

CATEGORIAS = {
    "A": "Narcisismo e Manipulação Emocional",
    "B": "Gaslighting e Confusão Mental",
    "C": "Ciclo do Abuso Psicológico",
    "D": "Perda de Identidade no Relacionamento",
    "E": "Culpa, Medo e Dependência Emocional",
    "F": "Silêncio, Controle e Punição Emocional",
    "G": "Idealização, Desvalorização e Descarte",
    "H": "Reconhecendo o Abuso Invisível"
}

FORMATOS = {
    "1": "ALERTA PSICOLÓGICO CURTO",
    "2": "VERDADE DURA SOBRE RELAÇÕES TÓXICAS",
    "3": "NÃO É AMOR, É CONTROLE",
    "4": "HISTÓRIA SILENCIOSA DE ABUSO",
    "5": "FRASE DIRETA PARA QUEM ESTÁ CONFUSO",
    "6": "PADRÃO TÓXICO QUE SE REPETE"
}

VILOES = [
    "o narcisista",
    "a manipulação emocional",
    "o gaslighting",
    "a culpa constante",
    "o medo de perder",
    "a dependência emocional",
    "a distorção da realidade",
    "o silêncio punitivo"
]

BLUEPRINTS = {
    "R1": "Alerta direto + quebra de ilusão + comando consciente",
    "R2": "Confusão mental + repetição do abuso + silêncio imposto",
    "R3": "Verdade incômoda + nomeação do abuso + limite",
    "R4": "Padrão invisível + desgaste emocional + despertar"
}

# ============================================================

def get_prompt_gemini(categoria, formato, vilao, blueprint):
    return f'''
Você é um CRIADOR DE CONTEÚDO DE CONSCIENTIZAÇÃO PSICOLÓGICA
especialista em NARCISISMO, RELACIONAMENTOS TÓXICOS e ABUSO EMOCIONAL.

Seu objetivo NÃO é romantizar dor.
Seu objetivo é:
- Dar clareza mental
- Nomear o abuso invisível
- Validar a percepção da vítima
- Incentivar consciência e limites

IMPORTANTE:
NÃO atacar pessoas.
NÃO incentivar vingança.
NÃO romantizar sofrimento.

PÚBLICO:
Pessoas em relacionamentos tóxicos
ou confusas emocionalmente.

DURAÇÃO ALVO: 20–35s por idioma.
WORDCOUNT: 60–85 palavras por idioma.

USE:
- CATEGORIA: {categoria} - {CATEGORIAS[categoria]}
- FORMATO: {formato} - {FORMATOS[formato]}
- VILÃO: {vilao}
- BLUEPRINT: {blueprint} - {BLUEPRINTS[blueprint]}

ESTRUTURA – 3 CLIPS:
clip_1: alerta direto
clip_2: explicação do padrão
clip_3: comando consciente + CTA

ALINHAMENTO 1:1 ES / EN.

REGRAS:
Frases curtas, tom calmo, sem emojis.

SAÍDA JSON ESTRITA no formato exato:
{{
"short_es": {{
"clip_1": {{"segments": ["frase1", "frase2"]}},
"clip_2": {{"segments": ["frase1", "frase2"]}},
"clip_3": {{"segments": ["frase1", "frase2"]}}
}},
"short_en": {{
"clip_1": {{"segments": ["sentence1", "sentence2"]}},
"clip_2": {{"segments": ["sentence1", "sentence2"]}},
"clip_3": {{"segments": ["sentence1", "sentence2"]}}
}}
}}
'''
    

def generar_guion(client):
    categoria = random.choice(list(CATEGORIAS.keys()))
    formato = random.choice(list(FORMATOS.keys()))
    vilao = random.choice(VILOES)
    blueprint = random.choice(list(BLUEPRINTS.keys()))

    print(f"🎲 Categoria: {CATEGORIAS[categoria]}")
    print(f"🎲 Formato: {FORMATOS[formato]}")
    print(f"🎲 Vilão: {vilao}")
    print(f"🎲 Blueprint: {BLUEPRINTS[blueprint]}")

    prompt = get_prompt_gemini(categoria, formato, vilao, blueprint)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "")
        return json.loads(text)
    except Exception as e:
        print(f"⚠️ Erro Gemini: {e}")
        return None


def segments_to_text(short_data):
    segments = []
    for clip in ["clip_1", "clip_2", "clip_3"]:
        segments.extend(short_data[clip]["segments"])
    return " ".join(segments)


def get_audio_duration(audio_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def seleccionar_videos(duracion_objetivo):
    import glob
    videos = glob.glob(os.path.join(LIBRARY_DIR, "*.mp4"))
    random.shuffle(videos)

    selected, total = [], 0
    for v in videos:
        if total >= duracion_objetivo:
            break
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", v],
            capture_output=True, text=True
        )
        try:
            d = float(result.stdout.strip())
            selected.append(v)
            total += d
        except:
            continue
    return selected


def crear_video(audio_path, timestamp, idioma, duracion_audio):
    videos = seleccionar_videos(duracion_audio + 1.0)
    if not videos:
        return None

    list_file = os.path.join(TEMP_DIR, f"concat_{timestamp}_{idioma}.txt")
    with open(list_file, "w") as f:
        for v in videos:
            f.write(f"file '{os.path.abspath(v)}'\n")

    temp_video = os.path.join(TEMP_DIR, f"temp_{timestamp}_{idioma}.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-t", str(duracion_audio + 1.0),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-an", temp_video
    ], capture_output=True)

    output_path = os.path.join(OUTPUT_DIR, f"short_{idioma}_{timestamp}.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-i", temp_video, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-shortest", output_path
    ], capture_output=True)

    os.remove(list_file)
    os.remove(temp_video)
    return output_path


def main():
    print("🎬 GENERADOR DE SHORTS – NARCISISMO & RELAÇÕES TÓXICAS")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    client = genai.Client(api_key=GEMINI_API_KEY)

    guion = generar_guion(client)
    if not guion:
        print("❌ Falha ao gerar roteiro")
        return

    try:
        # ESPANHOL
        text_es = segments_to_text(guion["short_es"])
        tts_es = TTSEngine(voice="carmelo")
        audio_es = tts_es.generate_speech(text_es, f"audio_ES_{timestamp}")
        dur_es = get_audio_duration(audio_es)
        crear_video(audio_es, timestamp, "ES", dur_es)

        # INGLÊS (substitui PT-BR, sem mudar estrutura)
        text_en = segments_to_text(guion["short_en"])
        tts_en = TTSEngine(voice="adam")
        audio_en = tts_en.generate_speech(text_en, f"audio_EN_{timestamp}")
        dur_en = get_audio_duration(audio_en)
        crear_video(audio_en, timestamp, "EN", dur_en)

        print("✅ Shorts gerados com sucesso")
        print(f"📂 Output: {OUTPUT_DIR}")
    except KeyError as e:
        print(f"❌ Erro na estrutura do JSON retornado por Gemini: chave '{e}' não encontrada")
        print("Resposta do Gemini:")
        print(json.dumps(guion, indent=2, ensure_ascii=False))


def gerar_shorts():
    """
    Função pública para execução via interface (Flask, botão, etc.)
    """
    main()


if __name__ == "__main__":
    main()
