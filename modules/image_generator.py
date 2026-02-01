"""
Generador de Imágenes con Leonardo AI y fallbacks
Genera imágenes IA estoicas para videos + Sistema de Cache
"""
import os
import time
import asyncio
import requests
import random
import shutil
from PIL import Image
from config import TEMP_DIR, IMAGE_CACHE_DIR, PREMIUM_IMAGES_DIR, CACHE_CONFIG, AVAILABLE_THEMES

# API Key de Leonardo AI (se configura en .env)
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY", "")


class ImageGenerator:
    """Generador de imágenes usando Leonardo AI con sistema de cache"""
    
    def __init__(self):
        """Inicializa el generador de imágenes"""
        self.api_key = LEONARDO_API_KEY
        self.output_dir = os.path.join(TEMP_DIR, "generated_images")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Configuración del cache
        self.cache_enabled = CACHE_CONFIG.get("enabled", True)
        self.min_cache = CACHE_CONFIG.get("min_cache_before_reuse", 3)
        self.cache_ratio = CACHE_CONFIG.get("cache_ratio", 0.66)
        self.max_cache = CACHE_CONFIG.get("max_cache_per_theme", 20)
        
        if self.api_key:
            print("🎨 Leonardo AI configurado")
        else:
            print("⚠️ LEONARDO_API_KEY no configurada (usando fallbacks)")
        
        # Modelos de Leonardo AI para diferentes estilos
        self.leonardo_models = {
            # Kino XL - Look cinematográfico (épico, dramático)
            "kino": "aa77f04e-3eec-4034-9c07-d0f619684628",
            # Phoenix 1.0 - Detallado y realista
            "phoenix": "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3",
            # Diffusion XL - Artístico y estilizado
            "diffusion": "1e60896f-3c26-4296-8ecc-53e2afecc132",
        }
        
        # Mapeo de temas a modelos óptimos
        self.theme_to_model = {
            "disciplina": "kino",      # Cinematográfico para guerreros
            "coraje": "kino",          # Épico para batallas
            "resiliencia": "phoenix",  # Detallado para Atlas
            "control": "diffusion",    # Artístico para filósofos
            "tiempo": "diffusion",     # Artístico para Chronos
            "mortalidad": "diffusion", # Oscuro y artístico para Hades
            "propósito": "phoenix",    # Detallado para Athena
            "estoicismo": "kino",      # Cinematográfico para Marco Aurelio
            "mentalidad": "phoenix",   # Detallado para Zeus
            "sabiduría": "diffusion",  # Artístico para Sócrates
        }
        
        # Lista de prompts: ESPARTANOS Y EMPERADORES - Estatuas épicas con fuego
        # Estilo: Bronce/mármol, fuego naranja, iluminación azul cinematográfica, Kino XL
        self.stoic_prompts_pool = [
            # === GUERREROS ESPARTANOS ===
            "Epic Spartan warrior statue in bronze finish, muscular body with Corinthian helmet, holding burning spear, dramatic fire and flames surrounding him, dark blue atmospheric background with orange fire contrast, cinematic lighting, hyper realistic 8k, 300 movie style",
            "Spartan king Leonidas statue in fighting stance, bronze skin sheen, red cape flowing in flames, lambda shield, burning battlefield behind, chromatic aberration, dark moody sky with fire glow, epic cinematic composition, 8k ultra detailed",
            "Close-up of Spartan warrior face with helmet, bronze statue texture, intense stoic expression, flames reflecting on metal surface, dark blue shadows with orange fire highlights, cinematographic lighting, hyper detailed 8k",
            "Spartan soldier statue holding torch with burning flame, muscular bronze body, war scars, dark atmospheric void behind, fire illuminating the figure, blue rim lighting, epic dramatic shot, 8k cinematic realism",
            "Two Spartan warriors statues in battle formation, bronze finish, spears and shields, massive fire explosion behind them, dark stormy sky, golden sparks floating, chromatic aberration effect, epic wide shot, 8k",
            
            # === EMPERADORES ROMANOS ===
            "Roman Emperor Marcus Aurelius statue in bronze, stoic philosopher expression, laurel wreath crown, toga draped over muscular body, flames burning around him, dark blue atmosphere with fire contrast, cinematic lighting, 8k hyper realistic",
            "Emperor Julius Caesar bronze statue, powerful stance with arm raised, imperial armor, Rome burning in background, dramatic fire and smoke, dark moody atmosphere, blue and orange color palette, epic cinematographic, 8k",
            "Augustus Caesar statue in divine pose, bronze skin texture, imperial toga, sacred fire burning at his feet, dark void background with flames, godlike lighting, chromatic aberration, cinematic epic, 8k detailed",
            "Roman Emperor statue close-up, bronze face with weathered texture, stoic expression, flames dancing around, blue shadows and orange fire highlights, intense atmospheric lighting, 8k ultra realistic portrait",
            "Nero Emperor watching Rome burn, bronze statue silhouette, massive inferno behind, dramatic fire reflections on metal skin, dark apocalyptic sky, cinematic wide shot, epic scale, 8k",
            
            # === GLADIADORES Y LEGIONARIOS ===
            "Roman gladiator statue in arena pose, bronze muscular body, holding flaming sword, fire pit burning below, dark colosseum background, blue moonlight with fire contrast, cinematic composition, 8k hyper detailed",
            "Roman Centurion statue commanding legions, bronze armor gleaming, red cape on fire, torches burning around him, dark battlefield atmosphere, chromatic aberration, epic military scene, 8k",
            "Gladiator champion statue with flames, bronze skin scarred from battle, victorious pose, arena on fire behind, dark dramatic lighting, orange and blue contrast, cinematic 8k",
            
            # === FILÓSOFOS ESTOICOS ===
            "Seneca philosopher statue in bronze, contemplative pose with scroll, ring of fire around him, dark void background, stoic wisdom in his eyes, blue atmospheric lighting with fire glow, cinematic portrait, 8k",
            "Epictetus bronze statue in meditation, flames as metaphor for inner fire, dark moody atmosphere, stoic expression of peace, chromatic aberration edges, cinematographic lighting, 8k detailed",
            "Zeno of Citium founder of Stoicism, bronze statue with robes, sacred flame burning beside him, dark philosophical atmosphere, blue and orange lighting contrast, epic portrait, 8k"
        ]
        
        # Mantener compatibilidad con temas específicos (pero usar pool aleatorio)
        self.stoic_prompts = {
            "default": self.stoic_prompts_pool[0]  # Fallback
        }
    
    def get_random_prompt(self) -> str:
        """Obtiene un prompt aleatorio de la lista de prompts estoicos"""
        return random.choice(self.stoic_prompts_pool)
    
    # ==================== SISTEMA DE CACHE ====================
    
    def get_cache_path(self, theme: str) -> str:
        """Obtiene la ruta del cache para un tema"""
        # Normalizar tema (quitar acentos para nombres de carpeta)
        theme_normalized = theme.lower().replace("ó", "o").replace("í", "i").replace("á", "a")
        if theme_normalized not in AVAILABLE_THEMES:
            theme_normalized = "estoicismo"  # Default
        return os.path.join(IMAGE_CACHE_DIR, theme_normalized)
    
    def get_cached_images(self, theme: str) -> list:
        """Obtiene lista de imágenes en cache para un tema"""
        cache_path = self.get_cache_path(theme)
        if not os.path.exists(cache_path):
            return []
        
        images = []
        for f in os.listdir(cache_path):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.mp4')):
                images.append(os.path.join(cache_path, f))
        return images
    
    def save_to_cache(self, image_path: str, theme: str) -> str:
        """Guarda una imagen en el cache del tema"""
        if not os.path.exists(image_path):
            return None
            
        cache_path = self.get_cache_path(theme)
        os.makedirs(cache_path, exist_ok=True)
        
        # Verificar límite de cache
        existing = self.get_cached_images(theme)
        if len(existing) >= self.max_cache:
            # Eliminar la más antigua
            oldest = sorted(existing, key=os.path.getmtime)[0]
            os.remove(oldest)
            print(f"   🗑️ Cache lleno, eliminada imagen antigua")
        
        # Copiar al cache
        filename = os.path.basename(image_path)
        cache_file = os.path.join(cache_path, f"cache_{int(time.time())}_{filename}")
        shutil.copy2(image_path, cache_file)
        print(f"   💾 Imagen guardada en cache: {theme}/")
        
        return cache_file
    
    def validate_image(self, image_path: str, min_size: int = 512) -> bool:
        """Valida que una imagen sea de calidad aceptable"""
        if not os.path.exists(image_path):
            return False
            
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                # Verificar tamaño mínimo
                if width < min_size or height < min_size:
                    print(f"   ⚠️ Imagen muy pequeña: {width}x{height}")
                    return False
                # Verificar que no esté corrupta
                img.verify()
            return True
        except Exception as e:
            print(f"   ⚠️ Imagen inválida: {e}")
            return False
    
    def get_images_smart(self, theme: str, count: int = 3, use_cache: bool = True) -> list:
        """
        Obtiene imágenes de forma inteligente:
        - Mezcla de cache (ahorra tokens) + nuevas (variedad)
        
        Args:
            theme: Tema de las imágenes
            count: Número de imágenes necesarias
            use_cache: Si usar el cache o generar todas nuevas
            
        Returns:
            Lista de rutas a imágenes
        """
        images = []
        
        if use_cache and self.cache_enabled:
            cached = self.get_cached_images(theme)
            
            # Solo usar cache si hay suficientes imágenes
            if len(cached) >= self.min_cache:
                # Calcular cuántas del cache vs nuevas
                from_cache = int(count * self.cache_ratio)
                from_new = count - from_cache
                
                # Seleccionar aleatorias del cache
                if from_cache > 0 and cached:
                    selected = random.sample(cached, min(from_cache, len(cached)))
                    images.extend(selected)
                    print(f"   📦 Usando {len(selected)} imágenes del cache")
                
                # Generar las nuevas
                if from_new > 0:
                    new_images = self.generate_multiple_images(theme, from_new)
                    images.extend(new_images)
                    # Guardar nuevas en cache
                    for img in new_images:
                        self.save_to_cache(img, theme)
                
                return images
        
        # Sin cache o cache insuficiente: generar todas nuevas
        new_images = self.generate_multiple_images(theme, count)
        
        # Guardar en cache para futuro uso
        if self.cache_enabled:
            for img in new_images:
                self.save_to_cache(img, theme)
        
        return new_images

    
    def generate_stoic_image(self, theme: str = None, custom_prompt: str = None) -> str:
        """
        Genera una imagen con temática estoica (prompt ALEATORIO)
        
        Args:
            theme: Tema específico (ya no se usa, prompts son aleatorios)
            custom_prompt: Prompt personalizado
            
        Returns:
            Ruta a la imagen generada
        """
        # Obtener prompt ALEATORIO (más variedad en las imágenes)
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self.get_random_prompt()  # Siempre aleatorio
        
        print(f"🎨 Generando imagen: '{prompt[:60]}...'")
        
        # Intentar Leonardo AI primero
        if self.api_key:
            image_path = self._generate_with_leonardo(prompt, theme)
            if image_path:
                return image_path
        
        # Fallback a Pexels imágenes (no videos)
        image_path = self._get_pexels_image(theme)
        if image_path:
            return image_path
        
        # Último fallback: gradiente
        return self.create_gradient_background()
    
    def generate_multiple_images(self, theme: str = None, count: int = 3) -> list:
        """
        Genera múltiples imágenes para un video con mayor variedad visual
        
        Args:
            theme: Tema específico (ignorado, siempre usa prompts de guerra)
            count: Número de imágenes a generar (2-3)
            
        Returns:
            Lista de rutas a las imágenes generadas
        """
        print(f"[IMG] Generando {count} imagenes para mayor variedad visual...")
        
        images = []
        
        for i in range(count):
            print(f"\n  [{i+1}/{count}] Generando imagen...")
            
            # Usar prompt ALEATORIO del pool de guerra
            prompt = self.get_random_prompt()
            print(f"   🎯 Prompt: {prompt[:50]}...")
            
            if self.api_key:
                image_path = self._generate_with_leonardo(prompt, theme)
                if image_path:
                    images.append(image_path)
                    continue
            
            # Fallback a Pexels si Leonardo falla
            pexels_img = self._get_pexels_image(theme)
            if pexels_img:
                images.append(pexels_img)
        
        # Si no se generaron suficientes, usar gradiente
        while len(images) < 2:
            images.append(self.create_gradient_background())
        
        print(f"\n[OK] {len(images)} imagenes generadas correctamente")
        return images
    
    def get_motion_videos(self, theme: str = None, count: int = 3) -> list:
        """
        Obtiene videos Motion 2.0 Fast (cache + nuevos)
        
        Args:
            theme: Tema para los videos
            count: Número de videos necesarios
            
        Returns:
            Lista de rutas a videos Motion
        """
        import random
        import glob
        
        # Directorio de cache de videos Motion
        motion_cache_dir = os.path.join(self.output_dir, "motion_cache")
        os.makedirs(motion_cache_dir, exist_ok=True)
        
        # Buscar videos en cache
        cached_videos = glob.glob(os.path.join(motion_cache_dir, "*.mp4"))
        
        print(f"🎬 Videos Motion en cache: {len(cached_videos)}")
        
        # Calcular cuántos necesitamos del cache vs nuevos
        # 50% cache, 50% nuevos (para variedad)
        from_cache = min(len(cached_videos), count // 2)
        to_generate = count - from_cache
        
        result_videos = []
        
        # Seleccionar videos del cache (aleatorio)
        if from_cache > 0 and cached_videos:
            selected_cache = random.sample(cached_videos, min(from_cache, len(cached_videos)))
            result_videos.extend(selected_cache)
            print(f"   📦 Usando {len(selected_cache)} videos del cache")
        
        # Generar nuevos videos
        if to_generate > 0:
            print(f"   🆕 Generando {to_generate} videos nuevos...")
            
            # Primero generar imágenes
            new_images = self.generate_multiple_images(theme=theme, count=to_generate)
            
            # Convertir cada imagen a video con Motion 2.0 Fast
            for i, img_path in enumerate(new_images):
                print(f"\n   [{i+1}/{len(new_images)}] Animando imagen...")
                video_path = self.animate_image_with_motion_fast(img_path)
                
                if video_path:
                    # Copiar al cache
                    cache_filename = f"motion_{int(time.time())}_{random.randint(1000,9999)}.mp4"
                    cache_path = os.path.join(motion_cache_dir, cache_filename)
                    
                    import shutil
                    shutil.copy2(video_path, cache_path)
                    
                    result_videos.append(video_path)
                    print(f"   ✓ Video guardado en cache")
        
        print(f"\n✓ Total: {len(result_videos)} videos Motion disponibles")
        return result_videos
    
    def generate_leonardo_motion_video(self, image_path: str) -> str:
        """
        Convierte una imagen local en un video animado usando Leonardo Motion SVD
        """
        if not self.api_key:
            return None
            
        print("🎬 Iniciando Leonardo Motion (Imagen -> Video)...")
        
        try:
            import time as time_module
            
            # 1. Subir imagen init (Necesitamos obtener URL firmada primero si es local, 
            # pero Leonardo Motion puede aceptar generationId de una imagen previa generada por ellos)
            # Para simplificar, usaremos el generationId de la imagen que acabamos de crear si es posible.
            # Como image_path es local, vamos a asumir que necesitamos subirla o usar generationId.
            # REVISIÓN: La API de Motion SVD Requiere un imageId de Leonardo.
            # En _generate_with_leonardo guardamos la imagen pero no retornamos el ID.
            # Necesitamos guardar el image_id también.
            
            # Por ahora, para este MVP rápido, si no tenemos el ID, no podemos usar Motion fácilmente sin subirla.
            # Vamos a implementar una versión que asume que la imagen FUE generada recién y 
            # modificaremos _generate_with_leonardo para guardar el 'leonardo_image_id'.
            
            print("⚠️ Funcionalidad Motion en desarrollo: Requiere Image ID de Leonardo.")
            return None
            
        except Exception as e:
            print(f"⚠️ Error Leonardo Motion: {e}")
            return None

    def _generate_with_leonardo(self, prompt: str, theme: str = None) -> tuple:
        """
        Genera imagen usando Leonardo AI API directamente
        Retorna: (path_local, leonardo_image_id)
        """
        try:
            import time as time_module
            
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": f"Bearer {self.api_key}"
            }
            
            # Paso 1: Seleccionar modelo según tema
            model_key = self.theme_to_model.get(theme, "kino")  # Kino XL por defecto - más cinematográfico
            model_id = self.leonardo_models.get(model_key, self.leonardo_models["phoenix"])
            print(f"🎨 Usando modelo Leonardo: {model_key.upper()}")
            
            # Paso 2: Crear generación
            payload = {
                "height": 1024,
                "width": 576,
                "modelId": model_id,
                "prompt": prompt,
                "num_images": 1,
                "guidance_scale": 7,
                "negative_prompt": "blurry, low quality, cartoon, anime, text, watermark, signature"
            }
            
            response = requests.post(
                "https://cloud.leonardo.ai/api/rest/v1/generations",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"⚠️ Leonardo API error: {response.status_code}")
                return None
            
            generation_id = response.json().get("sdGenerationJob", {}).get("generationId")
            
            if not generation_id:
                return None
            
            print(f"🎨 Generando imagen... (ID: {generation_id[:8]}...)")
            
            # Paso 2: Esperar y obtener resultado
            for attempt in range(12):
                time_module.sleep(5)
                
                get_response = requests.get(
                    f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}",
                    headers=headers,
                    timeout=30
                )
                
                if get_response.status_code == 200:
                    gen_data = get_response.json()
                    images = gen_data.get("generations_by_pk", {}).get("generated_images", [])
                    
                    if images:
                        image_data = images[0]
                        image_url = image_data.get("url")
                        image_id = image_data.get("id") # NECESARIO PARA MOTION
                        
                        if image_url:
                            # Descargar imagen
                            img_response = requests.get(image_url, timeout=30)
                            
                            timestamp = int(time.time())
                            output_path = os.path.join(self.output_dir, f"leonardo_{timestamp}.jpg")
                            
                            with open(output_path, 'wb') as f:
                                f.write(img_response.content)
                            
                            print(f"✓ Imagen Leonardo AI guardada: {output_path}")
                            
                            # RETORNAMOS TUPLA (PATH, ID)
                            # Para mantener compatibilidad con codigo viejo que espera str,
                            # guardaremos el ID en un archivo sidecar o atributo de clase si fuera persistente.
                            # Hack: Retornamos path, pero guardamos el ID en un archivo temporal mapeado
                            
                            id_map_path = os.path.join(self.output_dir, f"{os.path.basename(output_path)}.id")
                            with open(id_map_path, "w") as f:
                                f.write(image_id)
                                
                            return output_path
                
            return None
            
        except Exception as e:
            print(f"⚠️ Error con Leonardo AI: {e}")
            return None

    def animate_image_with_leonardo(self, image_path: str) -> str:
        """
        Anima una imagen previamente generada usando Leonardo Motion
        """
        if not self.api_key or not os.path.exists(image_path):
            return None
            
        # Intentar recuperar el ID de Leonardo
        id_map_path = image_path + ".id"
        if not os.path.exists(id_map_path):
            print("⚠️ No se encontró ID de Leonardo para esta imagen (no se puede animar)")
            return None
            
        with open(id_map_path, "r") as f:
            image_id = f.read().strip()
            
        print(f"🎬 Animando imagen (Motion SVD)... Leonardo ID: {image_id}")
        
        try:
            import time as time_module
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": f"Bearer {self.api_key}"
            }
            
            # 1. Crear Motion SVD Generation
            payload = {
                "imageId": image_id,
                "motionStrength": 5, # 1-10
                "isPublic": False
            }
            
            response = requests.post(
                "https://cloud.leonardo.ai/api/rest/v1/generations-motion-svd",
                headers=headers,
                json=payload,
                timeout=90
            )
            
            if response.status_code != 200:
                print(f"⚠️ Error iniciando Motion: {response.text}")
                return None
                
            motion_generation_id = response.json().get("motionSvdGenerationJob", {}).get("generationId")
            if not motion_generation_id:
                return None
                
            print(f"⏳ Renderizando video Motion... (ID: {motion_generation_id[:8]})")
            print(f"   (Esto puede tardar 1-2 minutos...)")
            
            # 2. Esperar video - USAR ENDPOINT CORRECTO: /generations/{id}
            for attempt in range(60): # ~300 segundos max (5 min)
                time_module.sleep(5)
                
                try:
                    # ENDPOINT CORRECTO para consultar Motion
                    get_response = requests.get(
                        f"https://cloud.leonardo.ai/api/rest/v1/generations/{motion_generation_id}",
                        headers=headers,
                        timeout=90
                    )
                    
                    if get_response.status_code == 200:
                        data = get_response.json()
                        gen_data = data.get("generations_by_pk", {})
                        status = gen_data.get("status")
                        
                        if attempt % 6 == 0:  # Cada 30 segundos mostrar progreso
                            print(f"   ... Status: {status} (intento {attempt+1}/60)")
                        
                        if status == "COMPLETE":
                            # Buscar motionMP4URL en generated_images
                            images = gen_data.get("generated_images", [])
                            if images:
                                video_url = images[0].get("motionMP4URL")
                                if video_url:
                                    # Descargar video
                                    vid_response = requests.get(video_url, timeout=120)
                                    
                                    timestamp = int(time.time())
                                    output_video_path = os.path.join(self.output_dir, f"leonardo_motion_{timestamp}.mp4")
                                    
                                    with open(output_video_path, 'wb') as f:
                                        f.write(vid_response.content)
                                        
                                    print(f"✓ Video Motion guardado: {output_video_path}")
                                    return output_video_path
                                
                        elif status == "FAILED":
                            print("❌ La generación de video falló.")
                            return None
                except requests.exceptions.Timeout:
                    print(f"   ... Timeout en intento {attempt+1}, reintentando...")
                    continue
                except Exception as poll_error:
                    print(f"   ... Error polling: {poll_error}")
                    continue
                        
            print("⚠️ Timeout esperando Motion video (5 min)")
            return None

        except Exception as e:
            print(f"⚠️ Error en Motion: {e}")
            return None
    
    def animate_image_with_motion_fast(self, image_path: str, resolution: str = "480p") -> str:
        """
        Anima una imagen usando Motion 2.0 Fast de Leonardo AI
        Mejor calidad que Motion SVD, más económico que Kling
        
        Args:
            image_path: Ruta a la imagen generada por Leonardo
            resolution: "480p" (200 créditos) o "720p" (300 créditos)
            
        Returns:
            Ruta al video generado o None si falla
        """
        if not self.api_key or not os.path.exists(image_path):
            return None
            
        # Intentar recuperar el ID de Leonardo
        id_map_path = image_path + ".id"
        if not os.path.exists(id_map_path):
            print("⚠️ No se encontró ID de Leonardo para esta imagen (no se puede animar)")
            return None
            
        with open(id_map_path, "r") as f:
            image_id = f.read().strip()
        
        # Configurar resolución
        if resolution == "720p":
            width, height = 720, 1280  # 9:16 vertical
            credits_info = "~300 créditos"
        else:
            width, height = 480, 854  # 9:16 vertical  
            credits_info = "~200 créditos"
            
        print(f"🎬 Animando imagen con Motion 2.0 Fast ({resolution})...")
        print(f"   💰 Consumo estimado: {credits_info}")
        
        try:
            import time as time_module
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": f"Bearer {self.api_key}"
            }
            
            # Payload para Motion 2.0 Fast (Image-to-Video)
            # IMPORTANTE: Motion 2.0 requiere un prompt para guiar la animación
            # Prompt optimizado para fuego, llamas y movimiento épico
            payload = {
                "imageId": image_id,
                "imageType": "GENERATED",
                "prompt": "Intense fire and flames dancing and flickering, burning embers and sparks floating upward, dramatic cape flowing in hot wind, smoke rising, lightning flickering in stormy sky, epic cinematic slow motion, god-like atmosphere, powerful movement",
                "duration": 10,  # 10 segundos por video
                "width": width,
                "height": height,
                "isPublic": False
            }
            
            response = requests.post(
                "https://cloud.leonardo.ai/api/rest/v1/generations-image-to-video",
                headers=headers,
                json=payload,
                timeout=90
            )
            
            if response.status_code != 200:
                print(f"❌ Error iniciando Motion 2.0 Fast: {response.text}")
                return None
                
            response_data = response.json()
            # La API devuelve 'motionVideoGenerationJob' (no 'videoGenerationJob')
            generation_id = response_data.get("motionVideoGenerationJob", {}).get("generationId")
            
            if not generation_id:
                print(f"❌ No se recibió generationId: {response_data}")
                return None
                
            print(f"⏳ Renderizando video Motion 2.0 Fast... (ID: {generation_id[:8]})")
            print(f"   (Esto puede tardar 1-2 minutos...)")
            
            # Esperar video - polling del status
            for attempt in range(60):  # ~300 segundos max (5 min)
                time_module.sleep(5)
                
                try:
                    get_response = requests.get(
                        f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}",
                        headers=headers,
                        timeout=90
                    )
                    
                    if get_response.status_code == 200:
                        data = get_response.json()
                        gen_data = data.get("generations_by_pk", {})
                        status = gen_data.get("status")
                        
                        if attempt % 6 == 0:  # Cada 30 segundos mostrar progreso
                            print(f"   ... Status: {status} (intento {attempt+1}/60)")
                        
                        if status == "COMPLETE":
                            # Buscar videoUrl en generated_images
                            images = gen_data.get("generated_images", [])
                            if images:
                                video_url = images[0].get("videoUrl") or images[0].get("motionMP4URL")
                                if video_url:
                                    # Descargar video
                                    vid_response = requests.get(video_url, timeout=120)
                                    
                                    timestamp = int(time.time())
                                    output_video_path = os.path.join(self.output_dir, f"motion_fast_{timestamp}.mp4")
                                    
                                    with open(output_video_path, 'wb') as f:
                                        f.write(vid_response.content)
                                        
                                    print(f"✓ Video Motion 2.0 Fast guardado: {output_video_path}")
                                    return output_video_path
                                    
                        elif status == "FAILED":
                            print("❌ La generación de video Motion 2.0 Fast falló.")
                            return None
                            
                except requests.exceptions.Timeout:
                    print(f"   ... Timeout en intento {attempt+1}, reintentando...")
                    continue
                except Exception as poll_error:
                    print(f"   ... Error polling: {poll_error}")
                    continue
                        
            print("⚠️ Timeout esperando video Motion 2.0 Fast (5 min)")
            return None

        except Exception as e:
            print(f"⚠️ Error en Motion 2.0 Fast: {e}")
            return None
    
    def animate_image_with_kling(self, image_path: str, duration: int = 5) -> str:
        """
        Anima una imagen usando Kling 2.5 Turbo a través de Leonardo AI
        Mejor calidad que Motion SVD, videos más cinematográficos
        
        Args:
            image_path: Ruta a la imagen generada por Leonardo
            duration: Duración del video (5 o 10 segundos)
            
        Returns:
            Ruta al video generado o None si falla
        """
        if not self.api_key or not os.path.exists(image_path):
            return None
            
        # Intentar recuperar el ID de Leonardo
        id_map_path = image_path + ".id"
        if not os.path.exists(id_map_path):
            print("⚠️ No se encontró ID de Leonardo para esta imagen (no se puede animar)")
            return None
            
        with open(id_map_path, "r") as f:
            image_id = f.read().strip()
            
        print(f"🎬 Animando imagen con Kling 2.5 Turbo... Leonardo ID: {image_id}")
        print(f"   ⏱️ Duración: {duration}s")
        
        try:
            import time as time_module
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": f"Bearer {self.api_key}"
            }
            
            # Payload para Kling 2.5 Turbo (Image-to-Video)
            payload = {
                "imageId": image_id,
                "imageType": "GENERATED",
                "model": "Kling2_5",  # Kling 2.5 Turbo
                "duration": duration,  # 5 o 10 segundos
                "width": 1080,
                "height": 1920,  # 9:16 vertical para reels
                "isPublic": False
            }
            
            response = requests.post(
                "https://cloud.leonardo.ai/api/rest/v1/generations-image-to-video",
                headers=headers,
                json=payload,
                timeout=90
            )
            
            if response.status_code != 200:
                print(f"⚠️ Error iniciando Kling 2.5: {response.text}")
                # Fallback a Motion SVD si Kling falla
                print("   Intentando fallback a Motion SVD...")
                return self.animate_image_with_leonardo(image_path)
                
            response_data = response.json()
            generation_id = response_data.get("videoGenerationJob", {}).get("generationId")
            
            if not generation_id:
                print(f"⚠️ No se recibió generationId: {response_data}")
                return None
                
            print(f"⏳ Renderizando video Kling 2.5 Turbo... (ID: {generation_id[:8]})")
            print(f"   (Esto puede tardar 2-4 minutos para {duration}s de video...)")
            
            # Esperar video - polling del status
            for attempt in range(90):  # ~450 segundos max (7.5 min)
                time_module.sleep(5)
                
                try:
                    get_response = requests.get(
                        f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}",
                        headers=headers,
                        timeout=90
                    )
                    
                    if get_response.status_code == 200:
                        data = get_response.json()
                        gen_data = data.get("generations_by_pk", {})
                        status = gen_data.get("status")
                        
                        if attempt % 6 == 0:  # Cada 30 segundos mostrar progreso
                            print(f"   ... Status: {status} (intento {attempt+1}/90)")
                        
                        if status == "COMPLETE":
                            # Buscar videoUrl en generated_images
                            images = gen_data.get("generated_images", [])
                            if images:
                                # Kling devuelve videoUrl o motionMP4URL
                                video_url = images[0].get("videoUrl") or images[0].get("motionMP4URL")
                                if video_url:
                                    # Descargar video
                                    vid_response = requests.get(video_url, timeout=180)
                                    
                                    timestamp = int(time.time())
                                    output_video_path = os.path.join(self.output_dir, f"kling25_{timestamp}.mp4")
                                    
                                    with open(output_video_path, 'wb') as f:
                                        f.write(vid_response.content)
                                        
                                    print(f"✓ Video Kling 2.5 Turbo guardado: {output_video_path}")
                                    return output_video_path
                                    
                        elif status == "FAILED":
                            print("❌ La generación de video Kling falló.")
                            print("   Intentando fallback a Motion SVD...")
                            return self.animate_image_with_leonardo(image_path)
                            
                except requests.exceptions.Timeout:
                    print(f"   ... Timeout en intento {attempt+1}, reintentando...")
                    continue
                except Exception as poll_error:
                    print(f"   ... Error polling: {poll_error}")
                    continue
                        
            print("⚠️ Timeout esperando video Kling (7.5 min)")
            return None

        except Exception as e:
            print(f"⚠️ Error en Kling 2.5: {e}")
            return None
    
    def _get_pexels_image(self, theme: str = None) -> str:
        """Obtiene imagen de Pexels como fallback"""
        from config import PEXELS_API_KEY
        
        if not PEXELS_API_KEY:
            return None
        
        # Keywords para buscar en Pexels
        keywords = {
            "disciplina": "greek statue marble",
            "coraje": "warrior statue",
            "resiliencia": "broken statue art",
            "control": "meditation statue",
            "mortalidad": "skull dark",
            "estoicismo": "roman statue",
        }
        query = keywords.get(theme, "greek statue marble")
        
        try:
            headers = {"Authorization": PEXELS_API_KEY}
            url = f"https://api.pexels.com/v1/search?query={query}&per_page=10&orientation=portrait"
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            photos = data.get("photos", [])
            
            if photos:
                import random
                photo = random.choice(photos)
                image_url = photo["src"]["large2x"]  # Alta resolución
                
                # Descargar
                img_response = requests.get(image_url, timeout=30)
                img_response.raise_for_status()
                
                timestamp = int(time.time())
                output_path = os.path.join(self.output_dir, f"pexels_{timestamp}.jpg")
                
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)
                
                print(f"✓ Imagen Pexels guardada: {output_path}")
                return output_path
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error obteniendo imagen de Pexels: {e}")
            return None
    
    def create_gradient_background(self, color1: tuple = (20, 20, 40), 
                                    color2: tuple = (60, 40, 80)) -> str:
        """Crea un fondo degradado como último recurso"""
        from PIL import ImageDraw
        
        width, height = 1080, 1920
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        for y in range(height):
            r = int(color1[0] + (color2[0] - color1[0]) * y / height)
            g = int(color1[1] + (color2[1] - color1[1]) * y / height)
            b = int(color1[2] + (color2[2] - color1[2]) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        timestamp = int(time.time())
        output_path = os.path.join(self.output_dir, f"gradient_{timestamp}.png")
        img.save(output_path)
        
        print(f"✓ Fondo degradado creado: {output_path}")
        return output_path


# Test del módulo
if __name__ == "__main__":
    generator = ImageGenerator()
    
    print("=== Test: Generar imagen estoica ===")
    image_path = generator.generate_stoic_image(theme="disciplina")
    print(f"Imagen: {image_path}")
