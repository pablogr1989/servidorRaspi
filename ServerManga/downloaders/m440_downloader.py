from downloaders.base_downloader import BaseDownloader
from database.db_manager import DatabaseManager
import os
import time

class M440Downloader(BaseDownloader):
    
    @staticmethod
    def extract_images(chapter_page, mode_debug=False, logger=None):
        """Extraer URLs de imagenes del capitulo manejando lazy loading"""
        try:
            # Esperar a que cargue el contenedor de imágenes principal
            try:
                chapter_page.wait_for_selector('#all img', timeout=20000)
            except:
                msg = "[WARN] Timeout esperando selector #all img"
                if mode_debug: print(msg)
                if logger: logger.log(msg)

            # Buscar todas las imágenes dentro del div id="all"
            images = chapter_page.query_selector_all('#all img')
            
            image_urls = []
            for img in images:
                # ESTRATEGIA M440:
                # El HTML muestra: src="loading.gif" data-src="URL_REAL"
                # A veces: src="URL_REAL" data-src="URL_REAL"
                # Prioridad absoluta a 'data-src' si existe.
                
                url = img.get_attribute('data-src')
                
                if not url:
                    url = img.get_attribute('src')
                
                # Filtrar nulos y el gif de carga
                if not url or 'loading.gif' in url:
                    continue
                
                # Normalizar URL (por si acaso vienen relativas)
                if url.startswith('//'):
                    url = 'https:' + url
                elif url.startswith('/'):
                    url = 'https://m440.in' + url
                
                if url not in image_urls:
                    image_urls.append(url)
            
            return image_urls

        except Exception as e:
            msg = f"[ERROR] extract_images M440: {e}"
            print(msg)
            if logger: logger.log(msg)
            return []

    @staticmethod
    def download_chapters_list(manga_data, capitulos_lista, browser, mode_debug=False, logger=None):
        """Descargar lista específica de capítulos"""
        if not browser:
            raise Exception("Browser not initialized")
        
        if not capitulos_lista:
            return None
        
        # Ordenar ascendente (del más viejo al más nuevo) para la descarga
        capitulos_ordenados = sorted(capitulos_lista, key=lambda x: float(x['name']) if x['name'].replace('.', '', 1).isdigit() else x['name'])
        
        msg = f"\n{'='*50}\nDescarga M440: {manga_data['title']}\nCapitulos: {len(capitulos_lista)}\n{'='*50}\n"
        if mode_debug: print(msg)
        if logger: logger.log(msg)
        
        local_path = manga_data['local_storage_path']
        content_dir = os.path.join(local_path, 'contenido')
        os.makedirs(content_dir, exist_ok=True)
        
        last_downloaded_chapter = None
        last_chapter_url = None
        db = DatabaseManager()

        for i, cap in enumerate(capitulos_ordenados):
            chapter_num = cap['name']
            chapter_url = cap['url']
            
            msg = f"\n--- Capitulo {chapter_num} ---"
            if mode_debug: print(msg)
            if logger: logger.log(msg)
            
            page = browser.new_page()
            try:
                # Headers para parecer humano
                page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://m440.in/'
                })

                page.goto(chapter_url, timeout=60000, wait_until='domcontentloaded')
                
                # Check simple anti-cloudflare por si acaso
                try:
                    page.wait_for_selector('#all img', timeout=15000)
                except:
                    pass # Si falla, intentamos extraer igual

                msg = "Extrayendo imagenes..."
                if mode_debug: print(msg)
                
                image_urls = M440Downloader.extract_images(page, mode_debug, logger)
                
                if not image_urls:
                    msg = f"[ERROR] No se encontraron imágenes en {chapter_num}"
                    print(msg)
                    if logger: logger.log(msg)
                    page.close()
                    continue
                
                msg = f"[OK] {len(image_urls)} imagenes. Descargando..."
                if mode_debug: print(msg)
                if logger: logger.log(msg)
                
                # Descargar imágenes (Usa método padre)
                image_files = BaseDownloader.download_images(image_urls, chapter_num, content_dir, mode_debug, logger)
                
                if image_files:
                    # Crear HTML
                    prev_file = f"capitulo_{capitulos_ordenados[i-1]['name']}.html" if i > 0 else None
                    next_file = f"capitulo_{capitulos_ordenados[i+1]['name']}.html" if i < len(capitulos_ordenados)-1 else None
                    
                    BaseDownloader.create_chapter_html(chapter_num, image_files, prev_file, next_file, manga_data, content_dir, logger)
                    
                    last_downloaded_chapter = chapter_num
                    last_chapter_url = chapter_url
                    
                    # Actualizar URL de última descarga en DB
                    db.update_last_download_url(manga_data['id'], last_chapter_url)
                
            except Exception as e:
                msg = f"[ERROR] Capitulo {chapter_num}: {e}"
                print(msg)
                if logger: 
                    logger.log(msg)
                    import traceback
                    logger.log(traceback.format_exc())
            finally:
                page.close()
            
            # Pausa entre capítulos
            if i < len(capitulos_ordenados) - 1:
                time.sleep(5)

        # Regenerar índice al final
        if last_downloaded_chapter:
            msg = "\nCreando index..."
            if mode_debug: print(msg)
            BaseDownloader.create_index_html(manga_data, logger)
            
        return last_downloaded_chapter

    @staticmethod
    def download_full_manga(manga_data, start_chapter, browser, mode_debug=False, logger=None):
        """
        Descarga manual desde un punto. 
        Reutiliza el Checker para obtener la lista completa primero.
        """
        # Importación tardía para evitar ciclos circulares
        from checkers.m440_checker import M440Checker
        
        msg = f"[INFO] Obteniendo lista de capítulos via M440Checker..."
        if mode_debug: print(msg)
        if logger: logger.log(msg)
        
        # Obtenemos TODOS los capítulos (pasamos last_checked=None)
        # Esto usará Playwright internamente en el Checker, pero es necesario para obtener los slugs.
        check_result = M440Checker.check_single({**manga_data, 'last_checked_chapter': None}, mode_debug, logger)
        
        if not check_result or not check_result['nuevos_capitulos']:
            msg = "[ERROR] No se pudo obtener la lista de capítulos"
            print(msg)
            return None
            
        all_chapters = check_result['nuevos_capitulos']
        
        # Filtrar desde start_chapter
        chapters_to_download = []
        found_start = False
        
        # Ordenar para búsqueda (Checker suele devolver desc, lo queremos asc para filtrar o iterar)
        # Pero check_single devuelve ordenados desc (nuevos primero).
        # Invertimos para buscar el start_chapter fácilmente si es "RESUME" o número.
        
        if start_chapter == "RESUME":
            last_url = manga_data.get('last_download_url')
            if not last_url:
                msg = "[ERROR] No hay last_download_url para RESUME"
                print(msg)
                return None
            
            # Buscar índice
            start_index = -1
            for idx, cap in enumerate(all_chapters):
                if cap['url'] == last_url:
                    start_index = idx
                    break
            
            if start_index != -1 and start_index > 0:
                # Como la lista del checker suele venir de nuevo a viejo (desc),
                # los capítulos ANTERIORES en la lista (índice menor) son los NUEVOS.
                chapters_to_download = all_chapters[:start_index]
                # Invertimos para descargar en orden cronológico
                chapters_to_download.reverse()
            elif start_index == 0:
                msg = "[INFO] Nada nuevo que descargar"
                print(msg)
                return None
            else:
                # Si no encuentra la URL, descarga todo (o maneja error)
                msg = "[WARN] URL de resume no encontrada, descargando todo"
                chapters_to_download = all_chapters[::-1] # Todo en orden asc
                
        else:
            # Buscar por número
            try:
                start_num = float(start_chapter)
                for cap in all_chapters:
                    try:
                        if float(cap['name']) >= start_num:
                            chapters_to_download.append(cap)
                    except:
                        pass
                # Ordenar ascendente para descarga
                chapters_to_download.sort(key=lambda x: float(x['name']) if x['name'].replace('.', '', 1).isdigit() else x['name'])
            except ValueError:
                msg = f"[ERROR] Número de capítulo inválido: {start_chapter}"
                print(msg)
                return None

        if not chapters_to_download:
            msg = f"[INFO] No se encontraron capítulos desde {start_chapter}"
            print(msg)
            return None

        # Delegar la descarga a download_chapters_list
        return M440Downloader.download_chapters_list(manga_data, chapters_to_download, browser, mode_debug, logger)