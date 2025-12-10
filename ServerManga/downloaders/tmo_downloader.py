from downloaders.base_downloader import BaseDownloader
from database.db_manager import DatabaseManager
import requests
import re
import os
import time
from PIL import Image
import io

class TmoDownloader(BaseDownloader):
    
    @staticmethod
    def download_full_manga(manga_data, start_chapter, browser, mode_debug=False, logger=None):
        """No implementado para TMO (usar download_chapters_list)"""
        msg = "[ERROR] TMO no soporta download_full_manga. Usar download_chapters_list"
        print(msg)
        if logger:
            logger.log(msg)
        return None

    @staticmethod
    def download_chapters_list(manga_data, capitulos_lista, browser, mode_debug=False, logger=None):
        """Descargar lista especifica de capitulos de TMO"""
        if not capitulos_lista:
            msg = f"[INFO] {manga_data['title']}: Lista vacia"
            print(msg)
            if logger:
                logger.log(msg)
            return None
        
        msg = f"\n{'='*50}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"Descarga TMO: {manga_data['title']}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"Capitulos a descargar: {len(capitulos_lista)}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"{'='*50}\n"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        local_path = manga_data['local_storage_path']
        content_dir = os.path.join(local_path, 'contenido')
        os.makedirs(content_dir, exist_ok=True)
        
        capitulos_ordenados = sorted(capitulos_lista, key=lambda x: float(x['name']))
        
        last_chapter_url = None
        last_downloaded_chapter = None
        
        for i, cap in enumerate(capitulos_ordenados):
            chapter_num = cap['name']
            chapter_url = cap['url']
            
            msg = f"\n--- Capitulo {chapter_num} ---"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            # Reintentar hasta 5 veces
            max_retries = 5
            page = None
            success = False
            
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt > 1:
                        msg = f"[INFO] Intento {attempt}/{max_retries}"
                        if mode_debug:
                            print(msg)
                        if logger:
                            logger.log(msg)
                    
                    msg = f"URL inicial: {chapter_url}"
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                    
                    upload_id = chapter_url.split('/')[-1]
                    
                    msg = "Obteniendo URL real del visor..."
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                    
                    real_url = TmoDownloader._get_real_viewer_url(upload_id, logger)
                    
                    if not real_url:
                        raise Exception(f"No se pudo resolver URL real para capitulo {chapter_num}")
                    
                    # FORZAR cambio a cascade
                    real_url = real_url.replace('/paginated', '/cascade')
                    
                    msg = f"URL real (modificada): {real_url}"
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                    
                    msg = f"[DEBUG] Enlace completo a abrir: {real_url}"
                    print(msg)
                    if logger:
                        logger.log(msg)
                    
                    page = browser.new_page()
                    page.goto(real_url, timeout=30000)
                    page.wait_for_load_state('networkidle')
                    
                    msg = "Extrayendo imagenes..."
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                    
                    image_urls = TmoDownloader.extract_images(page, mode_debug, logger)
                    
                    # VALIDAR imagenes ANTES de continuar
                    if not image_urls or len(image_urls) == 0:
                        page.close()
                        raise Exception(f"No se encontraron imagenes en capitulo {chapter_num}")
                    
                    msg = f"[OK] {len(image_urls)} imagenes"
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                    
                    msg = "Descargando imagenes..."
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                    
                    image_files = TmoDownloader.tmo_download_images(image_urls, chapter_num, content_dir, mode_debug, logger)
                    
                    # VALIDAR que descargo imagenes
                    if not image_files or len(image_files) == 0:
                        page.close()
                        raise Exception(f"No se descargaron imagenes en capitulo {chapter_num}")
                    
                    prev_file = f"capitulo_{capitulos_ordenados[i-1]['name']}.html" if i > 0 else None
                    next_file = f"capitulo_{capitulos_ordenados[i+1]['name']}.html" if i < len(capitulos_ordenados)-1 else None
                    
                    BaseDownloader.create_chapter_html(chapter_num, image_files, prev_file, next_file, manga_data, content_dir, logger)
                    
                    page.close()
                    
                    # SOLO si llego aqui sin excepciones
                    last_downloaded_chapter = chapter_num
                    last_chapter_url = chapter_url
                    success = True
                    break
                    
                except Exception as e:
                    if page:
                        page.close()
                    
                    if attempt < max_retries:
                        msg = f"[ERROR] Intento {attempt} fallo: {e}"
                        print(msg)
                        if logger:
                            logger.log(msg)
                        msg = f"[INFO] Esperando 60 segundos antes de reintentar..."
                        print(msg)
                        if logger:
                            logger.log(msg)
                        time.sleep(60)
                    else:
                        msg = f"\n[ERROR FATAL] Manga: {manga_data['title']}"
                        print(msg)
                        if logger:
                            logger.log(msg)
                        msg = f"Capitulo {chapter_num} fallo tras {max_retries} intentos: {e}"
                        print(msg)
                        if logger:
                            logger.log(msg)
                        import traceback
                        traceback.print_exc()
                        if logger:
                            logger.log(traceback.format_exc())
                        break
            
            # Si fallo este capitulo, detener descarga
            if not success:
                msg = f"\n[WARN] Descarga detenida en capitulo {chapter_num}"
                print(msg)
                if logger:
                    logger.log(msg)
                break
            
            # Pausa entre capitulos (si no es el ultimo)
            if i < len(capitulos_ordenados) - 1:
                msg = "[INFO] Pausa 30 segundos..."
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                time.sleep(30)
        
        # Actualizar DB SOLO con ultimo exitoso
        if last_chapter_url:
            msg = f"\nActualizando last_download_url..."
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            db = DatabaseManager()
            db.update_last_download_url(manga_data['id'], last_chapter_url)
            
            msg = "[OK] DB actualizada"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
        
        # Crear index
        msg = "\nCreando index..."
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        BaseDownloader.create_index_html(manga_data, logger)
        
        msg = f"\n{'='*50}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = "DESCARGA COMPLETADA" if last_downloaded_chapter else "DESCARGA FALLIDA"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"{'='*50}\n"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        return last_downloaded_chapter

    @staticmethod
    def tmo_download_images(image_urls, chapter_num, content_dir, mode_debug=True, logger=None):
        """Descargar imagenes a raw_Capitulo_X/. Retorna list[str] filenames"""
        raw_dir = os.path.join(content_dir, f'raw_Capitulo_{chapter_num}')
        os.makedirs(raw_dir, exist_ok=True)
        
        headers = {
            "authority": "cache3.img1tmo.com",
            "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "accept-language": "es-ES,es;q=0.9",
            "referer": "https://zonatmo.com/",
            "sec-ch-ua": '"Chromium";v="142", "Brave";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "image",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        }
        
        LOADING_URL_PART = "loading.gif"
        MIN_DIMENSION_PIXELS = 400
        downloaded = []
        
        for idx, url in enumerate(image_urls, 1):                   
            filename = f'pagina_{idx:03d}.jpg'
            filepath = os.path.join(raw_dir, filename)
            
            # Sin bucle de reintento interno; la excepción la maneja download_chapters_list
            try:                    
                # 1. VERIFICACIÓN DE URL
                if LOADING_URL_PART in url.lower():
                    # Lanza la excepción para reintentar el capítulo completo
                    raise ValueError(f"URL de imagen {idx} contiene '{LOADING_URL_PART}'.")
                
                response = requests.get(url, headers=headers)
                response.raise_for_status() 
                
                # 2. VERIFICACIÓN DE DIMENSIONES (Usando Pillow)
                image_data = io.BytesIO(response.content)
                img = Image.open(image_data)
                width, height = img.size
                
                if width < MIN_DIMENSION_PIXELS and height < MIN_DIMENSION_PIXELS:
                    raise ValueError(f"Dimensión de imagen {idx} ({width}x{height}) es menor que {MIN_DIMENSION_PIXELS}px.")

                # 3. GUARDAR IMAGEN REAL
                # Convertir a JPEG antes de guardar si no lo es, ya que el filename es .jpg
                img.convert('RGB').save(filepath, 'JPEG')

                downloaded.append(filename)
                
                msg = f"  [OK] {filename} (Dim: {width}x{height})"
                print(msg)
                if logger:
                    logger.log(msg)
                
                time.sleep(0.5)
                
            except Exception as e:
                # Relanzar la excepción para que la capture download_chapters_list
                msg = f"  [ERROR] Fallo al descargar la imagen {idx}: {e}"
                print(msg)
                if logger:
                    logger.log(msg)
                raise # Relanzar la excepción para el reintento a nivel de capítulo
        
        return downloaded
 
    @staticmethod
    def _get_real_viewer_url(upload_id, logger=None):
        """Obtener URL real del visor mediante redirect"""
        base_url = f"https://zonatmo.com/view_uploads/{upload_id}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                      "image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9",
            "Referer": "https://zonatmo.com/",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1"
        }
        
        try:
            response = requests.get(
                base_url,
                allow_redirects=False,
                headers=headers,
                timeout=10
            )
            
            if response.status_code not in (301, 302):
                msg = f"[WARN] Respuesta inesperada: {response.status_code}"
                print(msg)
                if logger:
                    logger.log(msg)
                return None
            
            real_url = response.headers.get("Location")
            
            if not real_url:
                msg = "[WARN] No se encontro header Location"
                print(msg)
                if logger:
                    logger.log(msg)
                return None
            
            # Reemplazar /paginated por /cascade
            if '/paginated' in real_url:
                real_url = real_url.replace('/paginated', '/cascade')
            
            return real_url
            
        except Exception as e:
            msg = f"[ERROR] _get_real_viewer_url: {e}"
            print(msg)
            if logger:
                logger.log(msg)
            return None
    

        """Extraer URLs de imagenes del visor TMO"""
        try:
            # Intentar con main-container primero
            try:
                chapter_page.wait_for_selector('#main-container', timeout=15000)
                main_container = chapter_page.query_selector('#main-container.viewer-container')
                
                if main_container:
                    img_containers = main_container.query_selector_all('div.img-container')
                    
                    if img_containers and len(img_containers) > 0:
                        msg = f"[DEBUG] Encontrados {len(img_containers)} contenedores en main-container"
                        if mode_debug:
                            print(msg)
                        if logger:
                            logger.log(msg)
                        
                        image_urls = []
                        for container in img_containers:
                            img = container.query_selector('img.viewer-img')
                            
                            if not img:
                                continue
                            
                            url_imagen = img.get_attribute('src')
                            
                            if not url_imagen:
                                url_imagen = img.get_attribute('data-src')
                            
                            if not url_imagen:
                                continue
                            
                            if url_imagen.startswith('//'):
                                url_imagen = 'https:' + url_imagen
                            elif url_imagen.startswith('/'):
                                url_imagen = 'https://zonatmo.com' + url_imagen
                            
                            image_urls.append(url_imagen)
                        
                        if image_urls:
                            return image_urls
            
            except Exception as e:
                msg = f"[WARN] main-container no encontrado, buscando img-container directamente: {e}"
                print(msg)
                if logger:
                    logger.log(msg)
            
            # Fallback: buscar img-container directamente
            msg = "[INFO] Buscando img-container directamente..."
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            img_containers = chapter_page.query_selector_all('div.img-container')
            
            if not img_containers:
                msg = "[ERROR] No se encontraron div.img-container"
                print(msg)
                if logger:
                    logger.log(msg)
                return []
            
            msg = f"[DEBUG] Encontrados {len(img_containers)} contenedores (fallback)"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            image_urls = []
            for container in img_containers:
                img = container.query_selector('img.viewer-img')
                
                if not img:
                    img = container.query_selector('img')
                
                if not img:
                    continue
                
                url_imagen = img.get_attribute('src')
                
                if not url_imagen:
                    url_imagen = img.get_attribute('data-src')
                
                if not url_imagen:
                    continue
                
                if url_imagen.startswith('//'):
                    url_imagen = 'https:' + url_imagen
                elif url_imagen.startswith('/'):
                    url_imagen = 'https://zonatmo.com' + url_imagen
                
                image_urls.append(url_imagen)
            
            return image_urls
            
        except Exception as e:
            msg = f'[ERROR] extract_images: {e}'
            print(msg)
            if logger:
                logger.log(msg)
                import traceback
                logger.log(traceback.format_exc())
            
            import traceback
            traceback.print_exc()
            return []
        """Extraer URLs de imagenes del visor TMO"""
        try:
            chapter_page.wait_for_selector('#main-container', timeout=15000)
            
            main_container = chapter_page.query_selector('#main-container.viewer-container')
            
            if not main_container:
                msg = "[ERROR] No se encontro #main-container"
                print(msg)
                if logger:
                    logger.log(msg)
                return []
            
            img_containers = main_container.query_selector_all('div.img-container')
            
            if not img_containers:
                msg = "[ERROR] No se encontraron div.img-container"
                print(msg)
                if logger:
                    logger.log(msg)
                return []
            
            msg = f"[DEBUG] Encontrados {len(img_containers)} contenedores"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            image_urls = []
            for container in img_containers:
                img = container.query_selector('img.viewer-img')
                
                if not img:
                    continue
                
                url_imagen = img.get_attribute('src')
                
                if not url_imagen:
                    url_imagen = img.get_attribute('data-src')
                
                if not url_imagen:
                    continue
                
                if url_imagen.startswith('//'):
                    url_imagen = 'https:' + url_imagen
                elif url_imagen.startswith('/'):
                    url_imagen = 'https://zonatmo.com' + url_imagen
                
                image_urls.append(url_imagen)
            
            return image_urls
            
        except Exception as e:
            msg = f'[ERROR] extract_images: {e}'
            print(msg)
            if logger:
                logger.log(msg)
                import traceback
                logger.log(traceback.format_exc())
            
            import traceback
            traceback.print_exc()
            return []
        
    @staticmethod
    def extract_images(chapter_page, mode_debug=True, logger=None):
        """Extraer URLs de imagenes del visor TMO"""
        try:
            
            # 1. ESPERAR AL CONTENEDOR PRINCIPAL
            chapter_page.wait_for_selector('#main-container', timeout=15000)
            main_container = chapter_page.query_selector('#main-container.viewer-container')
            
            if not main_container:
                msg = "[ERROR] No se encontro #main-container"
                print(msg)
                if logger:
                    logger.log(msg)
                # Intenta el Fallback antes de fallar completamente
            
            img_containers = main_container.query_selector_all('div.img-container') if main_container else []

            # 2. ESPERAR A QUE LA ÚLTIMA IMAGEN CARGUE SU URL REAL
            if img_containers and len(img_containers) > 0:
                
                # Selector CSS para el último contenedor de imagen y su imagen interna
                last_img_selector = '#main-container .img-container:last-child img'
                
                # Esperamos hasta 30 segundos a que el atributo 'src' o 'data-src' exista 
                # y NO contenga la cadena 'loading.gif' (la que nos daba problemas).
                chapter_page.wait_for_selector(
                    f'{last_img_selector}[src]:not([src*="loading.gif"]), {last_img_selector}[data-src]:not([data-src*="loading.gif"])', 
                    timeout=30000 
                )
                
                msg = f"[DEBUG] Espera activa por ultima imagen ({len(img_containers)} paginas) OK."
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
            
            # 3. EXTRACCIÓN DE URLS

            # Intentar con main-container primero (lógica original)
            if img_containers and len(img_containers) > 0:
                msg = f"[DEBUG] Encontrados {len(img_containers)} img-contenedores en main-container"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                
                image_urls = []
                for container in img_containers:
                    img = container.query_selector('img.viewer-img')
                    
                    if not img:
                        continue
                    
                    url_imagen = img.get_attribute('data-src')
                    
                    if not url_imagen:
                        url_imagen = img.get_attribute('src')
                    
                    if not url_imagen:
                        continue
                    
                    if url_imagen.startswith('//'):
                        url_imagen = 'https:' + url_imagen
                    elif url_imagen.startswith('/'):
                        url_imagen = 'https://zonatmo.com' + url_imagen
                    
                    image_urls.append(url_imagen)
                
                if image_urls:
                    return image_urls
            
            # FALLBACK: buscar img-container directamente (si el contenedor principal falló o no dio resultados)
            msg = "[INFO] Buscando img-container directamente (fallback)..."
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            img_containers_fallback = chapter_page.query_selector_all('div.img-container')
            
            if not img_containers_fallback:
                msg = "[ERROR] No se encontraron div.img-container"
                print(msg)
                if logger:
                    logger.log(msg)
                return []
            
            msg = f"[DEBUG] Encontrados {len(img_containers_fallback)} contenedores (fallback)"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            image_urls = []
            for container in img_containers_fallback:
                img = container.query_selector('img.viewer-img')
                
                if not img:
                    img = container.query_selector('img')
                
                if not img:
                    continue
                
                url_imagen = img.get_attribute('src')
                
                if not url_imagen:
                    url_imagen = img.get_attribute('data-src')
                
                if not url_imagen:
                    continue
                
                if url_imagen.startswith('//'):
                    url_imagen = 'https:' + url_imagen
                elif url_imagen.startswith('/'):
                    url_imagen = 'https://zonatmo.com' + url_imagen
                
                image_urls.append(url_imagen)
            
            return image_urls
            
        except Exception as e:
            msg = f'[ERROR] extract_images: {e}'
            print(msg)
            if logger:
                logger.log(msg)
                import traceback
                logger.log(traceback.format_exc())
            
            import traceback
            traceback.print_exc()
            return []