from downloaders.base_downloader import BaseDownloader
from database.db_manager import DatabaseManager
import requests
import re
import os

class OlympusNetDownloader(BaseDownloader):
    
    @staticmethod
    def download_full_manga(manga_data, start_chapter, browser, mode_debug=False, logger=None):
        """Descarga capitulos desde olympusbiblioteca.net"""
        if not browser:
            raise Exception("Browser not initialized")
        
        msg = f"\n{'='*50}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"Iniciando descarga: {manga_data['title']}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"{'='*50}\n"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        post_id = manga_data.get('olympus_net_post_id')
        if not post_id:
            msg = f"[ERROR] {manga_data['title']}: post_id no configurado"
            print(msg)
            if logger:
                logger.log(msg)
            return None
        
        local_path = manga_data['local_storage_path']
        content_dir = os.path.join(local_path, 'contenido')
        os.makedirs(content_dir, exist_ok=True)
        
        msg = "[INFO] Obteniendo lista capitulos..."
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        chapters_list = OlympusNetDownloader._get_all_chapters(post_id, logger)
        
        if not chapters_list:
            msg = f"[ERROR] {manga_data['title']}: No se pudieron obtener capitulos"
            print(msg)
            if logger:
                logger.log(msg)
            return None
        
        msg = f"[INFO] {len(chapters_list)} capitulos disponibles"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        start_idx = None
        
        if start_chapter == "RESUME":
            last_url = manga_data.get('last_download_url')
            
            if not last_url:
                msg = f"[ERROR] {manga_data['title']}: No hay last_download_url"
                print(msg)
                if logger:
                    logger.log(msg)
                return None
            
            for i, cap in enumerate(chapters_list):
                if cap['url'] == last_url:
                    if i == 0:
                        msg = f"[INFO] Ya descargado hasta el ultimo capitulo"
                        if mode_debug:
                            print(msg)
                        if logger:
                            logger.log(msg)
                        return None
                    start_idx = i - 1
                    break
            
            if start_idx is None:
                msg = f"[ERROR] {manga_data['title']}: last_download_url no encontrada en lista"
                print(msg)
                if logger:
                    logger.log(msg)
                return None
        
        else:
            for i, cap in enumerate(chapters_list):
                if cap['number'] == str(start_chapter):
                    start_idx = i
                    break
            
            if start_idx is None:
                msg = f"[ERROR] {manga_data['title']}: Capitulo {start_chapter} no existe"
                print(msg)
                if logger:
                    logger.log(msg)
                return None
        
        msg = f"[INFO] Iniciando desde capitulo {chapters_list[start_idx]['number']}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        last_chapter_url = None
        last_downloaded_chapter = None
        
        for i in range(start_idx, -1, -1):
            try:
                cap = chapters_list[i]
                chapter_num = cap['number']
                chapter_url = cap['url']
                
                msg = f"\n--- Capitulo {chapter_num} ---"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                
                msg = f"URL: {chapter_url}"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                
                page = browser.new_page()
                page.goto(chapter_url, timeout=30000)
                page.wait_for_load_state('networkidle')
                
                msg = "Extrayendo imagenes..."
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                
                image_urls = OlympusNetDownloader.extract_images(page, mode_debug, logger)
                
                msg = f"[OK] {len(image_urls)} imagenes encontradas"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                
                msg = "Descargando imagenes..."
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                
                image_files = BaseDownloader.download_images(image_urls, chapter_num, content_dir, mode_debug, logger)
                
                prev_file = f"capitulo_{chapters_list[i+1]['number']}.html" if i < len(chapters_list)-1 else None
                next_file = f"capitulo_{chapters_list[i-1]['number']}.html" if i > 0 else None
                
                BaseDownloader.create_chapter_html(chapter_num, image_files, prev_file, next_file, manga_data, content_dir, logger)
                
                last_downloaded_chapter = chapter_num
                
                page.close()
                
                last_chapter_url = chapter_url
                
            except Exception as e:
                msg = f"[ERROR] {manga_data['title']} Cap {chapter_num}: {e}"
                print(msg)
                if logger:
                    logger.log(msg)
                    import traceback
                    logger.log(traceback.format_exc())
                
                import traceback
                traceback.print_exc()
                break
        
        if last_chapter_url:
            msg = f"\nActualizando last_download_url en DB..."
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
        
        msg = "\nCreando index manga..."
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
        
        msg = "DESCARGA COMPLETADA"
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
    def download_chapters_list(manga_data, capitulos_lista, browser, mode_debug=False, logger=None):
        """Descargar lista especifica de capitulos (optimizado)"""
        if not browser:
            raise Exception("Browser not initialized")
        
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
        
        msg = f"Descarga optimizada: {manga_data['title']}"
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
            
            max_retries = 5
            page = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt > 1:
                        msg = f"[INFO] Intento {attempt}/{max_retries}"
                        if mode_debug:
                            print(msg)
                        if logger:
                            logger.log(msg)
                    
                    page = browser.new_page()
                    page.goto(chapter_url, timeout=30000)
                    page.wait_for_load_state('networkidle')
                    
                    msg = "Extrayendo imagenes..."
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                    
                    image_urls = OlympusNetDownloader.extract_images(page, mode_debug, logger)
                    
                    msg = f"[OK] {len(image_urls)} imagenes"
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                    
                    msg = "Descargando..."
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                    
                    image_files = BaseDownloader.download_images(image_urls, chapter_num, content_dir, mode_debug, logger)
                    
                    prev_file = f"capitulo_{capitulos_ordenados[i-1]['name']}.html" if i > 0 else None
                    next_file = f"capitulo_{capitulos_ordenados[i+1]['name']}.html" if i < len(capitulos_ordenados)-1 else None
                    
                    BaseDownloader.create_chapter_html(chapter_num, image_files, prev_file, next_file, manga_data, content_dir, logger)
                    
                    last_downloaded_chapter = chapter_num
                    page.close()
                    last_chapter_url = chapter_url
                    
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
                        
                        import time
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
                            logger.log(traceback.format_exc())
                        
                        import traceback
                        traceback.print_exc()
                        break
            
            if i < len(capitulos_ordenados) - 1:
                msg = "[INFO] Pausa 30 segundos..."
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                
                import time
                time.sleep(30)
        
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
        
        msg = "DESCARGA COMPLETADA"
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
    def _get_all_chapters(post_id, logger=None):
        """Obtener todos los capitulos via API"""
        try:
            chapters = []
            page = 1
            
            while True:
                api_url = f"https://olympusbiblioteca.net/wp-admin/admin-ajax.php?action=load_chapters&page={page}&per_page=20&post_id={post_id}&reverse=0"
                
                msg = f"[DEBUG] API request page {page}"
                if logger:
                    logger.log(msg)
                
                response = requests.get(api_url, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                if not data or not isinstance(data, list) or len(data) == 0:
                    break
                
                for cap in data:
                    chapter_name = cap.get('chapter_name', '')
                    match = re.search(r'(\d+(?:\.\d+)?)', chapter_name)
                    
                    if not match:
                        continue
                    
                    chapters.append({
                        'number': match.group(1),
                        'url': cap.get('url')
                    })
                
                page += 1
            
            chapters.sort(key=lambda x: float(x['number']), reverse=True)
            
            msg = f"[DEBUG] Total chapters obtenidos: {len(chapters)}"
            if logger:
                logger.log(msg)
            
            return chapters
            
        except Exception as e:
            msg = f"[ERROR] _get_all_chapters: {e}"
            print(msg)
            if logger:
                logger.log(msg)
            return []
    
    @staticmethod
    def extract_images(chapter_page, mode_debug=False, logger=None):
        """Extraer URLs de imagenes del capitulo"""
        try:
            chapter_page.wait_for_selector('img', timeout=15000)
            
            reading_content = chapter_page.query_selector('div.reading-content')
            
            if not reading_content:
                msg = "[ERROR] No se encontro div.reading-content"
                print(msg)
                if logger:
                    logger.log(msg)
                return []
            
            imagenes = reading_content.query_selector_all('img')
            
            if not imagenes:
                msg = "[ERROR] No se encontraron imagenes en reading-content"
                print(msg)
                if logger:
                    logger.log(msg)
                return []
            
            msg = f"[DEBUG] Encontradas {len(imagenes)} imagenes"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            image_urls = []
            for img in imagenes:
                url_imagen = img.get_attribute('src')
                
                if not url_imagen:
                    url_imagen = img.get_attribute('data-src')
                
                if not url_imagen:
                    continue
                
                if url_imagen.startswith('//'):
                    url_imagen = 'https:' + url_imagen
                elif url_imagen.startswith('/'):
                    url_imagen = 'https://olympusbiblioteca.net' + url_imagen
                
                if any(x in url_imagen for x in ['logo', 'icon', 'avatar', 'placeholder']):
                    continue
                
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