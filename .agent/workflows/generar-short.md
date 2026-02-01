---
description: Generar 6 shorts bilingües (3 ES + 3 PT-BR) con un solo comando
---

# Generar Shorts Bilingües (3x2)

Cuando el usuario pida shorts, use `/generar-short`, o pida videos:

// turbo
1. Ejecutar el script:
```bash
cd /Users/alejandrolloverassauras/Desktop/Videos\ IA\ automaticos && source venv/bin/activate && python generar_5_cosas.py
```

2. Esperar a que termine (~2-3 minutos para los 6 videos)

3. Reportar al usuario:
   - 3 videos en español (voz Carmelo - ElevenLabs)
   - 3 videos en portugués (voz Antonio BR - Edge TTS)
   - Hook de cada video
   - Duración de cada uno

Los 2 primeros videos se abren automáticamente para revisar.

## Archivos generados
- `output/short_v1_ES_[timestamp].mp4` - Video 1 español
- `output/short_v1_PT_[timestamp].mp4` - Video 1 portugués
- `output/short_v2_ES_[timestamp].mp4` - Video 2 español
- `output/short_v2_PT_[timestamp].mp4` - Video 2 portugués
- `output/short_v3_ES_[timestamp].mp4` - Video 3 español
- `output/short_v3_PT_[timestamp].mp4` - Video 3 portugués

## Características
- 3 videos DIFERENTES entre sí (tema, hook, formato, CTA distintos)
- Separadores de corte "|" para ritmo
- Sin clichés ni relleno
- Duración: 28-38 segundos cada uno
