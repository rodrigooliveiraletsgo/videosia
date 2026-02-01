"""
Generador de Contenido con Google Gemini
Genera guiones virales de curiosidad y misterios para YouTube Shorts (20–30s)
"""

import os
import json
import random
from google import genai
from config import GEMINI_API_KEY, CONTENT_DIR


class ContentGenerator:
    """Generador de contenido viral usando Gemini AI (Curiosidad + Misterio)"""

    def __init__(self):
        if GEMINI_API_KEY:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            self.model_name = "gemini-2.0-flash"
        else:
            self.client = None
            self.model_name = None
            print("⚠️ GEMINI_API_KEY no configurada. Usando fallback.")

        self.mystery_file = os.path.join(CONTENT_DIR, "mysteries.json")
        self._load_mysteries()

    def _load_mysteries(self):
        try:
            with open(self.mystery_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.mysteries = data.get("mysteries", [])
        except FileNotFoundError:
            self.mysteries = self._get_default_mysteries()
            self._save_mysteries()

    def _save_mysteries(self):
        with open(self.mystery_file, "w", encoding="utf-8") as f:
            json.dump({"mysteries": self.mysteries}, f, ensure_ascii=False, indent=2)

    def _get_default_mysteries(self):
        return [
            {
                "hook": "Esto no debería existir",
                "text": "En 1977, una señal proveniente del espacio duró exactamente 72 segundos. Nunca volvió a repetirse. Nadie ha podido explicar su origen.",
                "final_open_loop": "Algunos creen que no fue natural.",
                "cta_comment": "¿Mensaje extraterrestre o coincidencia?",
                "theme_keywords": "space mystery, deep signal, unknown origin"
            },
            {
                "hook": "Este lugar fue abandonado sin explicación",
                "text": "Cientos de personas dejaron todo atrás en una sola noche. No hubo lucha, ni aviso, ni registros claros de por qué.",
                "final_open_loop": "El motivo real nunca fue revelado.",
                "cta_comment": "¿Huirías sin llevar nada?",
                "theme_keywords": "abandoned town, dark mystery, empty houses"
            }
        ]

    def get_random_mystery(self):
        if self.mysteries:
            return random.choice(self.mysteries)
        return self._get_default_mysteries()[0]

    def generate_script_sync(self, theme: str = "misterio") -> dict:
        if not self.client:
            return self.get_random_mystery()

        listicle_options = [
            ("3 misterios que nadie ha podido explicar", 3),
            ("4 hechos reales que parecen mentira", 4),
            ("5 casos que fueron ocultados al público", 5),
            ("6 lugares donde pasan cosas inexplicables", 6),
            ("7 coincidencias demasiado perfectas", 7),
        ]

        if random.random() < 0.5:
            listicle_title, num_items = random.choice(listicle_options)
            formato = f"""
            Escribe un LISTICLE de exactamente {num_items} puntos.
            Cada punto debe:
            - Presentar un hecho real
            - Añadir un detalle inquietante
            - Terminar con una duda

            NO expliques todo.
            NO cierres el misterio.
            """
        else:
            formato = """
            Escribe un CASO o MISTERIO REAL.
            Escala la rareza progresivamente.
            Termina con una duda inquietante.
            """

        prompt = f"""
Eres un CREADOR DE CONTENIDO VIRAL experto en CURIOSIDADES y MISTERIOS REALES.

OBJETIVO:
- Detener el scroll
- Abrir loops mentales
- Generar teorías en comentarios

TEMA BASE: "{theme}"

PROHIBIDO:
- Moralejas
- Motivación
- Explicaciones completas

FORMATO:
{formato}

=== ESTRUCTURA OBLIGATORIA (Short 20–30s) ===

1. HOOK (impactante, 5–10 palabras)
2. DESARROLLO (hecho + rareza + contradicción)
3. FINAL ABIERTO (NO resolver)
4. CTA DE COMENTARIO (teoría A/B o pregunta directa)

ESTILO:
- Frases cortas
- Lenguaje simple
- Sensación de censura o peligro
- Segunda persona

REQUISITOS:
- 60–90 palabras
- Español neutro
- Ideal para YouTube Shorts

FORMATO JSON ESTRICTO:
{{
    "hook": "Frase inquietante inicial",
    "text": "Narración principal del misterio",
    "final_open_loop": "Frase que deja duda o inquietud",
    "cta_comment": "Pregunta directa para teorías",
    "theme_keywords": "3-5 keywords en inglés para visuales"
}}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            text = response.text.strip()
            if text.startswith("```"):
                text = text.replace("```json", "").replace("```", "")

            return json.loads(text)

        except Exception as e:
            print(f"Error Gemini: {e}")
            return self.get_random_mystery()

    def get_full_narration(self, script: dict) -> str:
        narration = f"{script.get('hook', '')}. {script.get('text', '')} {script.get('final_open_loop', '')}"
        return narration.strip()


# =========================
# TEST
# =========================
if __name__ == "__main__":
    generator = ContentGenerator()

    print("=== TEST SHORT MISTERIO ===")
    script = generator.generate_script_sync("casos inexplicables")
    print(json.dumps(script, indent=2, ensure_ascii=False))

    print("\n=== NARRACIÓN ===")
    print(generator.get_full_narration(script))
