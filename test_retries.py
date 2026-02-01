#!/usr/bin/env python3
"""
Test para verificar el sistema de reintentos del content generator
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.content_generator import ContentGenerator

def test_retry_system():
    """Test el sistema de reintentos"""
    print("=" * 60)
    print("🧪 PRUEBA: Sistema de Reintentos de Gemini")
    print("=" * 60)
    
    print("\n[1/3] Inicializando ContentGenerator...")
    generator = ContentGenerator()
    
    if not generator.client:
        print("⚠️  GEMINI_API_KEY no está configurada")
        print("   Usando fallback a citas predefinidas")
        print("   Para probar los reintentos, necesitas:")
        print("   1. Una clave API de Gemini")
        print("   2. Facturación activada en el proyecto")
    else:
        print("✅ ContentGenerator inicializado")
        print(f"   API Key: {generator.client}")
        print(f"   Modelo: {generator.model_name}")
        print(f"   Max reintentos: {generator.max_retries}")
        print(f"   Tiempo espera base: {generator.base_wait_time}s")
    
    print("\n[2/3] Generando script de prueba...")
    try:
        script = generator.generate_script_sync("disciplina")
        print("✅ Script generado exitosamente")
        print(f"   Hook: {script.get('hook', 'N/A')}")
        print(f"   Texto: {script.get('text', 'N/A')[:100]}...")
    except Exception as e:
        print(f"❌ Error al generar: {e}")
    
    print("\n[3/3] Probando fallback a citas predefinidas...")
    quote = generator.get_random_quote()
    print(f"✅ Cita obtenida:")
    print(f"   '{quote['text']}'")
    print(f"   - {quote['author']}")
    
    print("\n" + "=" * 60)
    print("📝 RESUMEN DE PRUEBA")
    print("=" * 60)
    
    if generator.client:
        print("""
✅ Sistema de reintentos ACTIVADO
   • Si recibe error 429: Reintentos automáticos
   • Espera automática entre intentos
   • Fallback a citas si todos los reintentos fallan
   
📋 Próximos pasos:
   1. Abre Google Cloud Console: https://console.cloud.google.com
   2. Crea un NUEVO PROYECTO con facturación
   3. Habilita la "Generative Language API"
   4. Crea una nueva clave API
   5. Reemplaza GEMINI_API_KEY en .env
   6. Ejecuta: python3 main.py
        """)
    else:
        print("""
⚠️  Sin clave API configurada
   Usando citas predefinidas como fallback
   
   Para usar Gemini:
   1. Obtén una clave API: https://ai.google.dev/
   2. Asegúrate que tenga facturación activada
   3. Actualiza .env con GEMINI_API_KEY
        """)
    
    print("=" * 60 + "\n")

if __name__ == "__main__":
    test_retry_system()
