# 🚨 Error Gemini 429 - RESOURCE_EXHAUSTED - Solución Completa

## 🔴 El Problema

Estás recibiendo este error:

```
⚠️ Error Gemini: 429 RESOURCE_EXHAUSTED
{'error': {'code': 429, 'message': 'You exceeded your current quota...'
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests
```

### ¿Por qué sucede?

**Tu clave API está vinculada al plan GRATUITO de Gemini**, aunque creas que tiene facturación. El error específicamente menciona `free_tier`, lo que significa que:

1. ✅ Tu clave API existe y funciona
2. ❌ **PERO** está asociada a un proyecto SIN facturación, O
3. ❌ La facturación no está CORRECTAMENTE activada en el proyecto

---

## ✅ SOLUCIÓN PASO A PASO

### **Paso 1: Verificar la situación actual**

Tu código AHORA tiene **reintentos inteligentes automáticos**. Cuando reciba un 429:
- ✅ Espera automáticamente 10+ segundos
- ✅ Reintenta hasta 3 veces
- ✅ Usa fallback a citas predefinidas si falla
- ℹ️ Te muestra instrucciones claras en la consola

### **Paso 2: GENERAR NUEVA CLAVE API (Recomendado)**

La forma más rápida de resolver esto es crear una **nueva clave API en un proyecto con facturación**:

#### A) Ve a Google Cloud Console
```
https://console.cloud.google.com/
```

#### B) Crea un NUEVO PROYECTO (recomendado)
1. En la esquina superior izquierda, haz clic en el selector de proyecto
2. Haz clic en "Nuevo Proyecto"
3. Nombre: `Videos-IA-Estoicismo` (o el que prefieras)
4. Crear

#### C) Activa la API de Gemini en el NUEVO proyecto
1. Ve a "APIs & Services" → "Library"
2. Busca "Generative Language API" (o "Gemini API")
3. Haz clic en "Enable"

#### D) **ACTIVA FACTURACIÓN en el proyecto**
⚠️ **CRÍTICO**: Sin este paso, seguirás recibiendo error 429
1. Ve a "Billing" en el menú izquierdo
2. Haz clic en "Link Billing Account"
3. Selecciona tu cuenta de facturación (o crea una si no tienes)
4. Confirma que aparezca "Billing is enabled"

#### E) Crea una NUEVA clave API
1. Ve a "APIs & Services" → "Credentials"
2. Haz clic en "+ Create Credentials"
3. Selecciona "API Key"
4. Copia la clave generada

#### F) Actualiza tu archivo `.env`
```
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```
(Reemplaza con tu NUEVA clave)

#### G) Prueba con:
```bash
python main.py --test
```

---

## 📊 Límites de Cuota

### Free Tier (GRATIS)
- ❌ 15 solicitudes por minuto
- ❌ 1 millón de tokens por día
- ❌ **Se agota rápidamente**

### Tier con Facturación (PAGADO)
- ✅ 100+ solicitudes por minuto
- ✅ 50 millones+ de tokens por día
- ✅ Suficiente para tu proyecto

---

## 🛡️ Mejoras Implementadas en el Código

He actualizado `modules/content_generator.py` con:

### 1. **Reintentos automáticos**
```python
def _call_gemini_with_retry(self, prompt: str) -> dict | None:
    # Reintenta hasta 3 veces en caso de 429
    # Espera automáticamente entre intentos
```

### 2. **Detección inteligente de errores 429**
```python
def _handle_api_error(self, error_response: dict, attempt: int) -> bool:
    # Identifica si es un 429
    # Calcula el tiempo de espera correcto
    # Muestra instrucciones útiles
```

### 3. **Fallback a contenido predefinido**
- Si Gemini falla después de reintentos, usa citas predefinidas
- ✅ El video se genera de todas formas
- ✅ No se detiene el proceso

### 4. **Mensajes claros de diagnóstico**
```
⚠️ [Intento 1/3] Error 429 - Límite de cuota excedido
   ⏳ Esperando 10.5s antes de reintentar...
   💡 SOLUCIÓN: Actualiza tu clave API en .env
      - Ve a https://console.cloud.google.com
      - Asegúrate de que tu proyecto tiene FACTURACIÓN ACTIVADA
```

---

## 🧪 Pruebas

### Prueba 1: Verificar conexiones
```bash
python main.py --test
```

### Prueba 2: Generar video (con reintentos automáticos)
```bash
python main.py
```

### Prueba 3: Ver logs detallados
```bash
python main.py -v  # Si tu código lo soporta
```

---

## 🔧 Solución de Problemas

### "Sigue dando 429 después de generar nueva clave"
- ❌ La facturación NO está activada
- ✅ Ve a Google Cloud → Billing y activa facturación

### "Creé facturación pero sigue sin funcionar"
- ❌ Probablemente necesita 5-10 minutos para propagarse
- ✅ Espera 10 minutos y prueba de nuevo

### "¿Cuánto me costará?"
- 💰 Free tier da 2,500 solicitudes/mes GRATIS
- 💰 Después: ~$0.00075 por solicitud (muy barato)
- 💰 Para 100 videos: ~$0.08

---

## 💡 Recomendaciones

### Opción 1: Nueva Clave (RECOMENDADO)
- ✅ Más fácil
- ✅ Garantiza que tienes facturación
- ✅ 5 minutos

### Opción 2: Esperar reintentos automáticos
- ✅ Si ya completaste los pasos anterior
- ✅ El código espera automáticamente
- ✅ Debería funcionar después de la próxima solicitud

### Opción 3: Usar solo citas predefinidas
- ✅ Los videos se generan igualmente
- ❌ Menos contenido personalizado
- ✅ Setear `GEMINI_API_KEY=""` en `.env`

---

## ✨ Próximos Pasos

1. **Ahora**: Sigue los pasos del "Paso 2" arriba
2. **Después**: Ejecuta `python main.py --test`
3. **Si falla**: Espera 10 minutos (propagación de Google Cloud)
4. **Si sigue fallando**: Revisa que la facturación esté activada

---

## 📚 Referencias Útiles

- [Documentación de cuotas de Gemini API](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Console de Billing de Google Cloud](https://console.cloud.google.com/billing)
- [Pricing de Gemini API](https://ai.google.dev/pricing)

---

**¿Preguntas?** Si el problema persiste después de estos pasos, verifica:
1. Que la facturación esté ACTIVADA (no solo configurada)
2. Que sea una **NUEVA clave API** del proyecto con facturación
3. Que hayas actualizado `.env` correctamente
