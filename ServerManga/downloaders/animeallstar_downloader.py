from downloaders.base_downloader import BaseDownloader
from bs4 import BeautifulSoup
import os
import re

class AnimeAllStarDownloader(BaseDownloader):
    
    @staticmethod
    def download_full_manga(manga_data, start_chapter, browser, mode_debug=False, logger=None):
        """Descarga no soportada para animeallstar (usar download_chapters_list)"""
        msg = "[ERROR] download_full_manga no soportado para animeallstar"
        print(msg)
        if logger:
            logger.log(msg)
        return None
    
    @staticmethod
    def download_chapters_list(manga_data, capitulos_lista, browser, mode_debug=False, logger=None):
        """Descargar lista de capitulos"""
        from database.db_manager import DatabaseManager
        
        if not capitulos_lista:
            return None

        # Ordenar ascendente para descarga (del mas viejo al mas nuevo)
        def sort_key(cap):
            try:
                return float(cap['name'])
            except ValueError:
                return 0

        capitulos_lista.sort(key=sort_key)

        msg = f"[INFO] Descargando {len(capitulos_lista)} capitulos: {capitulos_lista[0]['name']} -> {capitulos_lista[-1]['name']}"
        print(msg)
        if logger:
            logger.log(msg)
        
        local_path = manga_data['local_storage_path']
        content_dir = os.path.join(local_path, 'contenido')
        os.makedirs(content_dir, exist_ok=True)
        
        ultimo_capitulo = None
        db = DatabaseManager()
        
        for idx, cap_info in enumerate(capitulos_lista, 1):
            cap_num = cap_info['name']
            cap_url = cap_info['url']
            
            msg = f"\n[{idx}/{len(capitulos_lista)}] Descargando capitulo {cap_num}"
            print(msg)
            if logger:
                logger.log(msg)
            
            try:
                page = browser.new_page()
                page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'es-ES,es;q=0.9',
                    'Referer': 'https://animeallstar30.com/',
                    'Referrer-Policy': 'strict-origin-when-cross-origin'
                })
                
                page.goto(cap_url, timeout=60000, wait_until='domcontentloaded')
                
                # Detectar avisos antes de extraer
                es_aviso, mensaje_aviso = AnimeAllStarDownloader._detectar_aviso(page, mode_debug, logger)
                
                if es_aviso:
                    msg = f"  [AVISO] {mensaje_aviso}"
                    print(msg)
                    if logger:
                        logger.log(msg)
                    msg = f"  [SKIP] Capitulo {cap_num} saltado (es un aviso)"
                    print(msg)
                    if logger:
                        logger.log(msg)
                    page.close()
                    continue
                
                # Extraer imagenes
                image_urls = AnimeAllStarDownloader.extract_images(page, mode_debug, logger)
                
                if not image_urls:
                    msg = f"  [ERROR] No se encontraron imagenes en {cap_url}"
                    print(msg)
                    if logger:
                        logger.log(msg)
                    page.close()
                    continue
                
                msg = f"  [OK] {len(image_urls)} imagenes encontradas"
                print(msg)
                if logger:
                    logger.log(msg)
                
                page.close()
                
                # Descargar imagenes
                downloaded = BaseDownloader.download_images(
                    image_urls, cap_num, content_dir, mode_debug, logger
                )
                
                if not downloaded:
                    msg = f"  [ERROR] Fallo descarga de imagenes"
                    print(msg)
                    continue
                
                # Crear HTML
                prev_cap = f"capitulo_{capitulos_lista[idx-2]['name']}.html" if idx > 1 else None
                next_cap = f"capitulo_{capitulos_lista[idx]['name']}.html" if idx < len(capitulos_lista) else None
                
                BaseDownloader.create_chapter_html(
                    cap_num, downloaded, prev_cap, next_cap,
                    manga_data, content_dir, logger
                )
                
                ultimo_capitulo = cap_num
                db.update_last_download_url(manga_data['id'], cap_url)
                
                msg = f"  [OK] Capitulo {cap_num} completado"
                print(msg)
                if logger:
                    logger.log(msg)
                
            except Exception as e:
                msg = f"  [ERROR] Capitulo {cap_num}: {e}"
                print(msg)
                if logger:
                    logger.log(msg)
                try:
                    page.close()
                except:
                    pass
        
        if ultimo_capitulo:
            BaseDownloader.create_index_html(manga_data, logger)
        
        return ultimo_capitulo
    
    @staticmethod
    def extract_images(chapter_page, mode_debug=False, logger=None):
        """Extraer URLs de imagenes del capitulo"""
        html = chapter_page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Buscar el contenedor principal por ID (sin importar si es main o div)
        main_content = soup.find(id='main')
        
        if not main_content:
            msg = "  [WARN] No se encontro etiqueta con id='main'"
            if mode_debug: print(msg)
            return []
        
        # 2. Buscar el contenedor de contenido DIRECTO: div.entry-content
        # Segun tu HTML, las imagenes estan dentro de <div class="entry-content clear" ...>
        content_div = main_content.find('div', class_='entry-content')
            
        if not content_div:
            # Fallback: intentar buscar por ast-post-format si entry-content falla
            content_div = main_content.find('div', class_=re.compile(r'ast-post-format-'))
            
        if not content_div:
            msg = "  [WARN] No se encontro div.entry-content ni ast-post-format"
            if mode_debug: print(msg)
            return []
        
        image_urls = []
        
        # 3. Buscar todas las imagenes
        imgs = content_div.find_all('img')
        
        for img in imgs:
            src = img.get('src', '')
            if not src:
                src = img.get('data-src', '') 
            
            if not src:
                continue
                
            # Filtrar imagenes irrelevantes (iconos sociales, avatar, etc)
            if any(x in src.lower() for x in ['gravatar', 'logo', 'icon', 'button', 'share', 'facebook', 'twitter', 'whatsapp']):
                continue
            
            # Lógica para imágenes de blogger (Google)
            if 'blogger.googleusercontent' in src:
                # Reemplazar sXXXX-rw o similares por s1600 (alta calidad)
                src = re.sub(r'/s\d+(-rw)?/', '/s1600/', src)
                if src not in image_urls:
                    image_urls.append(src)
            
            # Lógica para imágenes alojadas en animeallstar30 (wp-content)
            elif 'wp-content/uploads' in src:
                 if src not in image_urls:
                    image_urls.append(src)
            
            # Fallback para otras imagenes largas que parezcan contenido
            elif len(src) > 50: 
                 if src not in image_urls:
                    image_urls.append(src)
        
        return image_urls
    
    @staticmethod
    def _detectar_aviso(page, mode_debug=False, logger=None):
        """Detectar si el capitulo es un aviso"""
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Buscar contenedor principal agnóstico a etiqueta
        main_content = soup.find(id='main')
        if not main_content:
            return (False, "")

        # Buscar contenido
        content_div = main_content.find('div', class_='entry-content')
        if not content_div:
            content_div = main_content.find('div', class_=re.compile(r'ast-post-format-'))
            
        if not content_div:
            return (False, "")
            
        # 1. Deteccion por texto en headers
        headers = content_div.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b'])
        for header in headers:
            texto = header.get_text(strip=True).lower()
            if 'aviso' in texto or 'información' in texto or 'importante' in texto:
                mensaje = header.get_text(strip=True)
                siguiente = header.find_next(['p', 'div'])
                if siguiente:
                    mensaje += " - " + siguiente.get_text(strip=True)[:100] + "..."
                return (True, mensaje)
        
        # 2. Deteccion por escasez de imagenes
        imgs = content_div.find_all('img')
        # Filtramos imagenes reales (ignorando iconos)
        imgs_reales = [i for i in imgs if 'blogger.googleusercontent' in i.get('src', '') or 'wp-content/uploads' in i.get('src', '')]
        
        # Si tiene muy pocas imágenes (menos de 3), probablemente sea texto/aviso
        if len(imgs_reales) < 9:
            return (True, f"Aviso detectado por pocas imagenes ({len(imgs_reales)})")
            
        return (False, "")