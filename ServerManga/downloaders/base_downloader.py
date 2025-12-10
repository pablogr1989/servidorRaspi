from abc import ABC, abstractmethod
import os
import requests
import time

class BaseDownloader(ABC):
    
    @staticmethod
    @abstractmethod
    def download_full_manga(manga_data, start_chapter, browser, mode_debug=False, logger=None):
        """
        Descargar capitulos completos
        manga_data: dict con info del manga
        start_chapter: str o "RESUME"
        browser: instancia playwright browser
        mode_debug: bool para prints condicionales
        logger: instancia Logger para registro
        return: ultimo_capitulo_descargado (str)
        """
        pass
    
    @staticmethod
    @abstractmethod
    def download_chapters_list(manga_data, capitulos_lista, browser, mode_debug=False, logger=None):
        """
        Descargar lista especifica de capitulos (optimizado)
        manga_data: dict con info del manga
        capitulos_lista: list[dict] estructura dependiente del page_type
        browser: instancia playwright browser
        mode_debug: bool para prints condicionales
        logger: instancia Logger para registro
        return: ultimo_capitulo_descargado (str)
        """
        pass
    
    @staticmethod
    @abstractmethod
    def extract_images(chapter_page, mode_debug=False, logger=None):
        """Extraer URLs de imagenes del capitulo. Retorna list[str]"""
        pass
    
    @staticmethod
    def download_images(image_urls, chapter_num, content_dir, mode_debug=False, logger=None):
        """Descargar imagenes a raw_Capitulo_X/. Retorna list[str] filenames"""
        raw_dir = os.path.join(content_dir, f'raw_Capitulo_{chapter_num}')
        os.makedirs(raw_dir, exist_ok=True)
        
        downloaded = []
        for idx, url in enumerate(image_urls, 1):
            filename = f'pagina_{idx:03d}.jpg'
            filepath = os.path.join(raw_dir, filename)
            
            max_retries = 5
            for attempt in range(1, max_retries + 1):
                try:
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    downloaded.append(filename)
                    
                    msg = f"  [OK] {filename}"
                    print(msg)
                    if logger:
                        logger.log(msg)
                    
                    time.sleep(0.5)
                    break
                    
                except Exception as e:
                    if attempt < max_retries:
                        msg = f"  [WARN] Descarga {idx} fallo (intento {attempt}/{max_retries}): {e}"
                        if mode_debug:
                            print(msg)
                        if logger:
                            logger.log(msg)
                        
                        msg = f"  [INFO] Reintentando en 5 segundos..."
                        if mode_debug:
                            print(msg)
                        if logger:
                            logger.log(msg)
                        
                        time.sleep(5)
                    else:
                        msg = f"  [ERROR] Fallo al descargar en el capitulo {chapter_num} la imagen {idx}. Fallo tras {max_retries} intentos: {e}"
                        print(msg)
                        if logger:
                            logger.log(msg)
        
        return downloaded
    
    @staticmethod
    def create_chapter_html(chapter_num, image_files, prev_chapter, next_chapter, manga_data, content_dir, logger=None):
        """Crear capitulo_X.html"""
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                      'templates', 'capitulo_template.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        images_html = ''
        for img in image_files:
            images_html += f'        <img src="raw_Capitulo_{chapter_num}/{img}" alt="Pagina" loading="lazy">\n'
        
        html = template.replace('{{MANGA_TITLE}}', manga_data['title'])
        html = html.replace('{{CHAPTER_NUM}}', str(chapter_num))
        html = html.replace('{{IMAGES}}', images_html)
        html = html.replace('{{MANGA_ID}}', str(manga_data['id']))
        html = html.replace('{{PREV_CHAPTER}}', prev_chapter if prev_chapter else '#')
        html = html.replace('{{NEXT_CHAPTER}}', next_chapter if next_chapter else '#')
        html = html.replace('{{PREV_DISABLED}}', '' if prev_chapter else 'disabled')
        html = html.replace('{{NEXT_DISABLED}}', '' if next_chapter else 'disabled')
        
        filepath = os.path.join(content_dir, f'capitulo_{chapter_num}.html')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        msg = f"[OK] Creado capitulo_{chapter_num}.html"
        print(msg)
        if logger:
            logger.log(msg)
    
    @staticmethod
    def create_index_html(manga_data, logger=None):
        """Crear index.html en raiz manga"""
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                      'templates', 'manga_index.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        html = template.replace('{{MANGA_ID}}', str(manga_data['id']))
        html = html.replace('{{MANGA_TITLE}}', manga_data['title'])
        
        local_path = manga_data['local_storage_path']
        filepath = os.path.join(local_path, 'index.html')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        msg = f"[OK] Creado index.html en {local_path}"
        print(msg)
        if logger:
            logger.log(msg)