"""
Motor de Text-to-Speech
Soporta ElevenLabs (con API key) y Edge TTS (gratuito, sin API key)
"""
import os
import asyncio
import requests
from config import ELEVENLABS_API_KEY, TTS_CONFIG, TEMP_DIR, AVAILABLE_VOICES

# Voces de Edge TTS (Microsoft) en español
EDGE_VOICES = {
    "pablo": "es-ES-AlvaroNeural",      # Masculino español (profundo)
    "carmelo": "es-ES-AlvaroNeural",    # Masculino español
    "elena": "es-ES-ElviraNeural",      # Femenino español
    "jorge": "es-MX-JorgeNeural",       # Masculino mexicano
    "dalia": "es-MX-DaliaNeural",       # Femenino mexicano
    # Voces en inglés
    "adam": "en-US-GuyNeural",          # Masculino US (narrador)
    "adam_en": "en-US-GuyNeural",       # Alias
    "rachel": "en-US-JennyNeural",      # Femenino US
    "rachel_en": "en-US-JennyNeural",   # Alias
    # Voces en portugués brasileño
    "antonio_br": "pt-BR-AntonioNeural",  # Masculino brasileño (profundo, épico)
    "francisca_br": "pt-BR-FranciscaNeural",  # Femenino brasileño
}


class TTSEngine:
    """Motor de Text-to-Speech con ElevenLabs y Edge TTS"""
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self, voice: str = "adam", use_edge: bool = None):
        """
        Inicializa el motor TTS
        
        Args:
            voice: Nombre de la voz
            use_edge: Forzar Edge TTS. None = auto-detectar
        """
        self.api_key = ELEVENLABS_API_KEY
        self.voice_name = voice
        
        # Auto-detectar si usar Edge TTS
        if use_edge is None:
            self.use_edge = not self._test_elevenlabs()
        else:
            self.use_edge = use_edge
        
        if self.use_edge:
            # Mapear voz a Edge TTS
            self.edge_voice = EDGE_VOICES.get(voice, EDGE_VOICES.get("adam"))
            print(f"🔊 Usando Edge TTS (voz: {voice} → {self.edge_voice})")
        else:
            self.voice_id = AVAILABLE_VOICES.get(voice, AVAILABLE_VOICES["adam"])
            self.headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            print(f"🔊 Usando ElevenLabs (voz: {voice})")
    
    def _test_elevenlabs(self) -> bool:
        """Verifica si ElevenLabs está disponible"""
        if not self.api_key or self.api_key == "tu_api_key_de_elevenlabs":
            return False
        
        try:
            url = f"{self.BASE_URL}/voices"
            headers = {"xi-api-key": self.api_key}
            response = requests.get(url, headers=headers, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_speech(self, text: str, output_filename: str = None) -> str:
        """
        Genera audio a partir de texto
        """
        if self.use_edge:
            return self._generate_with_edge(text, output_filename)
        else:
            return self._generate_with_elevenlabs(text, output_filename)
    
    def _generate_with_edge(self, text: str, output_filename: str = None) -> str:
        """Genera audio con Edge TTS (gratuito)"""
        import edge_tts
        
        if not output_filename:
            output_filename = f"speech_{hash(text) % 10000}"
        
        output_path = os.path.join(TEMP_DIR, f"{output_filename}.mp3")
        
        print(f"🎙️ Generando audio con Edge TTS: '{text[:50]}...'")
        
        async def generate():
            communicate = edge_tts.Communicate(text, self.edge_voice)
            await communicate.save(output_path)
        
        asyncio.run(generate())
        
        print(f"✓ Audio guardado: {output_path}")
        return output_path
    
    def _generate_with_elevenlabs(self, text: str, output_filename: str = None) -> str:
        """Genera audio con ElevenLabs"""
        url = f"{self.BASE_URL}/text-to-speech/{self.voice_id}"
        
        payload = {
            "text": text,
            "model_id": TTS_CONFIG["model_id"],
            "voice_settings": {
                "stability": TTS_CONFIG["stability"],
                "similarity_boost": TTS_CONFIG["similarity_boost"],
                "style": TTS_CONFIG.get("style", 0),
                "use_speaker_boost": TTS_CONFIG.get("use_speaker_boost", True)
            }
        }
        
        print(f"🎙️ Generando audio con ElevenLabs: '{text[:50]}...'")
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            if not output_filename:
                output_filename = f"speech_{hash(text) % 10000}"
            
            output_path = os.path.join(TEMP_DIR, f"{output_filename}.mp3")
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ Audio guardado: {output_path}")
            return output_path
            
        except requests.exceptions.HTTPError as e:
            print(f"⚠️ ElevenLabs falló, usando Edge TTS...")
            self.use_edge = True
            self.edge_voice = EDGE_VOICES.get(self.voice_name, EDGE_VOICES.get("adam"))
            return self._generate_with_edge(text, output_filename)
    
    def test_connection(self) -> bool:
        """Verifica la conexión"""
        if self.use_edge:
            print("✓ Edge TTS disponible (gratuito, sin API key)")
            return True
        
        try:
            url = f"{self.BASE_URL}/voices"
            headers = {"xi-api-key": self.api_key}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                voices = response.json().get("voices", [])
                print(f"✓ ElevenLabs conectado. {len(voices)} voces disponibles")
                return True
            else:
                print(f"⚠️ ElevenLabs no disponible, usando Edge TTS")
                return True  # Edge TTS siempre funciona
        except Exception as e:
            print(f"⚠️ ElevenLabs no disponible: {e}")
            print("✓ Edge TTS disponible como alternativa")
            return True


# Test del módulo
if __name__ == "__main__":
    engine = TTSEngine(voice="pablo")
    
    print("=== Test de conexión ===")
    if engine.test_connection():
        print("\n=== Generando audio de prueba ===")
        text = "La disciplina es el puente entre tus metas y tus logros."
        audio_path = engine.generate_speech(text, "test_audio")
        print(f"Audio generado: {audio_path}")
