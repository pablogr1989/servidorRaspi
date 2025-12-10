from checkers.base_checker import BaseChecker
import requests
from bs4 import BeautifulSoup
import re
import time

class TmoChecker(BaseChecker):
    
    @staticmethod
    def check_single(manga_data, mode_debug=False, logger=None):
        check_url = manga_data.get('check_url')
        
        msg = f"Check single con url {check_url}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        if not check_url:
            msg = f"[ERROR] '{manga_data['title']}' sin check_url"
            print(msg)
            if logger:
                logger.log(msg)
            return {
                'manga_id': manga_data['id'],
                'title': manga_data['title'],
                'has_new': False,
                'new_chapters_count': 0,
                'last_checked_chapter': manga_data['last_checked_chapter'],
                'current_chapter': None,
                'nuevos_capitulos': []
            }
        
        try:
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
            
            response = requests.get(check_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            msg = f"[DEBUG] Contenedor chapters: {soup.find('div', {'id': 'chapters'}) is not None}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            msg = f"[DEBUG] Capitulos visibles: {len(soup.find_all('li', {'class': 'list-group-item'}))}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            chevrons = soup.find_all('i', {'class': 'fa fa-chevron-down fa-fw'})           
            
            last_checked = manga_data.get('last_checked_chapter')
            nuevos_capitulos = []
            current_chapter = None
            
            for chevron in chevrons:
                chapter_name = chevron.parent.get_text(strip=True)
                match = re.search(r'(\d+(?:\.\d+)?)', chapter_name)
                
                if not match:
                    continue
                
                cap_num = match.group(1)
                
                if current_chapter is None:
                    current_chapter = cap_num
                
                chapter_li = chevron.find_parent('li', {'class': 'list-group-item'})
                if not chapter_li:
                    continue
                
                url_div = chapter_li.find('div', {'class': 'col-2 col-sm-1 text-right'})
                if not url_div:
                    continue
                
                url_link = url_div.find('a', href=True)
                if not url_link:
                    continue
                
                cap_url = url_link['href']
                
                if last_checked:
                    try:
                        if float(cap_num) > float(last_checked):
                            nuevos_capitulos.append({
                                'name': cap_num,
                                'url': cap_url
                            })
                    except ValueError:
                        if cap_num != last_checked:
                            nuevos_capitulos.append({
                                'name': cap_num,
                                'url': cap_url
                            })
                else:
                    nuevos_capitulos.append({
                        'name': cap_num,
                        'url': cap_url
                    })
            
            msg = "Ahora toca descargar la cover"
            print(msg)
            if logger:
                logger.log(msg)
            
            TmoChecker._descargar_cover(soup, manga_data, mode_debug, logger)
            
            return {
                'manga_id': manga_data['id'],
                'title': manga_data['title'],
                'has_new': len(nuevos_capitulos) > 0,
                'new_chapters_count': len(nuevos_capitulos),
                'last_checked_chapter': last_checked,
                'current_chapter': current_chapter,
                'nuevos_capitulos': nuevos_capitulos
            }
            
        except Exception as e:
            msg = f"[ERROR] check_single: {e}"
            print(msg)
            if logger:
                logger.log(msg)
                import traceback
                logger.log(traceback.format_exc())
            import traceback
            traceback.print_exc()
            return {
                'manga_id': manga_data['id'],
                'title': manga_data['title'],
                'has_new': False,
                'new_chapters_count': 0,
                'last_checked_chapter': manga_data['last_checked_chapter'],
                'current_chapter': None,
                'nuevos_capitulos': []
            }

    @staticmethod
    def check_batch(manga_list, mode_debug=True, logger=None):
        resultados = []
        
        for manga in manga_list:
            msg = f"[CHECKING] {manga['title']}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            result = TmoChecker.check_single(manga, mode_debug, logger)
            resultados.append(result)
            
            msg = f"  [OK] Cap actual: {result['current_chapter']}, Ultimo descargado: {result['last_checked_chapter']}, Nuevos: {result['new_chapters_count']}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            time.sleep(30)
        
        return resultados
    
    @staticmethod
    def _descargar_cover(soup, manga_data, mode_debug=True, logger=None):
        """Descargar cover del manga si no existe"""
        import os        
        
        img = soup.find('img', {'class': 'book-thumbnail'})
        if not img or not img.get('src'):
            msg = f"[WARN] No hay cover URL para '{manga_data['title']}'"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            return
        
        cover_url = img['src']
        
        manga_dir = manga_data['local_storage_path']
        os.makedirs(manga_dir, exist_ok=True)
        
        ext = cover_url.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png', 'webp']:
            ext = 'webp'
        
        cover_path = os.path.join(manga_dir, f'portada.{ext}')
        
        for existing_ext in ['webp', 'jpg', 'jpeg', 'png']:
            existing_path = os.path.join(manga_dir, f'portada.{existing_ext}')
            if os.path.exists(existing_path):
                msg = f"[INFO] Cover ya existe para '{manga_data['title']}'"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                return
        
        try:
            msg = f"[INFO] Descargando cover para '{manga_data['title']}'..."
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": manga_data.get('check_url', 'https://zonatmo.com/'),
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9"
            }
            
            response = requests.get(cover_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            with open(cover_path, 'wb') as f:
                f.write(response.content)
            
            msg = f"[OK] Cover descargado: {cover_path}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
        except Exception as e:
            msg = f"[ERROR] Descarga cover fallo: {e}"
            print(msg)
            if logger:
                logger.log(msg)