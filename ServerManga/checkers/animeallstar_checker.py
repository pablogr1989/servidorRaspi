from checkers.base_checker import BaseChecker
import requests
from bs4 import BeautifulSoup
import re

class AnimeAllStarChecker(BaseChecker):
    
    @staticmethod
    def check_single(manga_data, mode_debug=False, logger=None):
        """Verificar un manga individual"""
        manga_id = manga_data['id']
        title = manga_data['title']
        check_url = manga_data['check_url']
        last_checked = manga_data.get('last_checked_chapter')
        
        msg = f"[CHECKING] {title}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://animeallstar30.com/'
        }

        try:
            response = requests.get(check_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # --- CORRECCIÓN AQUÍ ---
            # En lugar de buscar 'div', buscamos por id='main' independientemente de la etiqueta
            # o especificamente 'main'
            main_tag = soup.find('main', id='main')
            
            # Fallback por si en alguna version usan div
            if not main_tag:
                main_tag = soup.find('div', id='main')
                
            if not main_tag:
                msg = f"  [ERROR] No se encontro main#main"
                print(msg)
                if logger:
                    logger.log(msg)
                return AnimeAllStarChecker._empty_result(manga_id, title, last_checked)
            
            # Buscar el contenedor de filas
            ast_row = main_tag.find('div', class_='ast-row')
            
            if not ast_row:
                # Si no hay ast-row, intentamos buscar articles directamente dentro del main
                # (A veces la estructura cambia ligeramente)
                articles = main_tag.find_all('article')
            else:
                articles = ast_row.find_all('article')
            
            if not articles:
                msg = f"  [ERROR] No se encontraron etiquetas article"
                print(msg)
                if logger:
                    logger.log(msg)
                return AnimeAllStarChecker._empty_result(manga_id, title, last_checked)
            
            capitulos_encontrados = []
            
            for article in articles:
                # Buscar el titulo: h2.entry-title -> a
                h2_title = article.find('h2', class_='entry-title')
                if not h2_title:
                    continue
                
                link_tag = h2_title.find('a')
                if not link_tag or not link_tag.get('href'):
                    continue
                
                url = link_tag['href']
                texto_titulo = link_tag.get_text(strip=True) # Ej: One Piece Manga 1167 Español
                
                # Extraer numero del titulo
                # Busca el primer numero flotante o entero
                match = re.search(r'(\d+(?:\.\d+)?)', texto_titulo)
                if not match:
                    continue
                
                cap_num = match.group(1)
                
                capitulos_encontrados.append({
                    'name': cap_num,
                    'url': url
                })
            
            if not capitulos_encontrados:
                msg = f"  [INFO] No se encontraron capitulos con formato valido"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                return AnimeAllStarChecker._empty_result(manga_id, title, last_checked)
            
            # Ordenar por numero descendente (del mas nuevo al mas viejo)
            try:
                capitulos_encontrados.sort(key=lambda x: float(x['name']), reverse=True)
            except ValueError:
                capitulos_encontrados.sort(key=lambda x: x['name'], reverse=True)
            
            current_chapter = capitulos_encontrados[0]['name']
            
            # Filtrar nuevos
            nuevos_capitulos = []
            if last_checked:
                try:
                    for cap in capitulos_encontrados:
                        if float(cap['name']) > float(last_checked):
                            nuevos_capitulos.append(cap)
                except ValueError:
                    for cap in capitulos_encontrados:
                        if cap['name'] != last_checked:
                            nuevos_capitulos.append(cap)
            else:
                nuevos_capitulos = capitulos_encontrados
            
            has_new = len(nuevos_capitulos) > 0
            
            msg = f"  [OK] Cap actual: {current_chapter}, Ultimo descargado: {last_checked}, Nuevos: {len(nuevos_capitulos)}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            return {
                'manga_id': manga_id,
                'title': title,
                'has_new': has_new,
                'new_chapters_count': len(nuevos_capitulos),
                'last_checked_chapter': last_checked,
                'current_chapter': current_chapter,
                'nuevos_capitulos': nuevos_capitulos
            }
            
        except Exception as e:
            msg = f"  [ERROR] {e}"
            print(msg)
            if logger:
                logger.log(msg)
                import traceback
                logger.log(traceback.format_exc())
            return AnimeAllStarChecker._empty_result(manga_id, title, last_checked)
    
    @staticmethod
    def _empty_result(manga_id, title, last_checked):
        return {
            'manga_id': manga_id,
            'title': title,
            'has_new': False,
            'new_chapters_count': 0,
            'last_checked_chapter': last_checked,
            'current_chapter': None,
            'nuevos_capitulos': []
        }
    
    @staticmethod
    def check_batch(manga_list, mode_debug=True, logger=None):
        """Batch processing para animeallstar"""
        resultados = []
        for manga in manga_list:
            result = AnimeAllStarChecker.check_single(manga, mode_debug, logger)
            resultados.append(result)
            import time
            time.sleep(2) # Respetar rate limits
        return resultados