from checkers.base_checker import BaseChecker
import requests

class OlympusNetChecker(BaseChecker):
    
    @staticmethod
    def check_single(manga_data, mode_debug=False, logger=None):
        import re
        
        post_id = manga_data.get('olympus_net_post_id')
        if not post_id:
            msg = f"[ERROR] '{manga_data['title']}' sin olympus_net_post_id"
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
            api_url = f"https://olympusbiblioteca.net/wp-admin/admin-ajax.php?action=load_chapters&page=1&per_page=999&post_id={post_id}&reverse=0"
            
            response = requests.get(api_url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list) or len(data) == 0:
                return {
                    'manga_id': manga_data['id'],
                    'title': manga_data['title'],
                    'has_new': False,
                    'new_chapters_count': 0,
                    'last_checked_chapter': manga_data['last_checked_chapter'],
                    'current_chapter': None,
                    'nuevos_capitulos': []
                }
            
            chapters = data
            last_checked = manga_data.get('last_checked_chapter')
            
            # Extraer numeros y filtrar nuevos
            nuevos_capitulos = []
            current_chapter = None
            
            for cap in chapters:
                chapter_name = cap.get('chapter_name', '')
                match = re.search(r'(\d+(?:\.\d+)?)', chapter_name)
                
                if not match:
                    continue
                
                cap_num = match.group(1)
                
                if current_chapter is None:
                    current_chapter = cap_num
                
                if last_checked:
                    try:
                        if float(cap_num) > float(last_checked):
                            nuevos_capitulos.append({
                                'name': cap_num,
                                'url': cap.get('url')
                            })
                    except ValueError:
                        if cap_num != last_checked:
                            nuevos_capitulos.append({
                                'name': cap_num,
                                'url': cap.get('url')
                            })
                else:
                    nuevos_capitulos.append({
                        'name': cap_num,
                        'url': cap.get('url')
                    })
            
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
        """Batch processing para olympus_net"""
        from database.db_manager import DatabaseManager
        import re
        
        db = DatabaseManager()
        resultados = []
        
        for manga in manga_list:
            mid = manga['id']
            post_id = manga.get('olympus_net_post_id')
            last_checked = manga.get('last_checked_chapter')
            
            if not post_id:
                msg = f"[WARN] '{manga['title']}' sin olympus_net_post_id"
                print(msg)
                if logger:
                    logger.log(msg)
                resultados.append({
                    'manga_id': mid,
                    'title': manga['title'],
                    'has_new': False,
                    'new_chapters_count': 0,
                    'last_checked_chapter': last_checked,
                    'current_chapter': None,
                    'nuevos_capitulos': []
                })
                continue
            
            msg = f"[CHECKING] {manga['title']} (post_id: {post_id})"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            try:
                api_url = f"https://olympusbiblioteca.net/wp-admin/admin-ajax.php?action=load_chapters&page=1&per_page=999&post_id={post_id}&reverse=0"
                
                response = requests.get(api_url, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                if not data or not isinstance(data, list) or len(data) == 0:
                    resultados.append({
                        'manga_id': mid,
                        'title': manga['title'],
                        'has_new': False,
                        'new_chapters_count': 0,
                        'last_checked_chapter': last_checked,
                        'current_chapter': None,
                        'nuevos_capitulos': []
                    })
                    msg = f"  [ERROR] Sin capitulos en respuesta"
                    print(msg)
                    if logger:
                        logger.log(msg)
                    continue
                
                chapters = data
                
                # Extraer primer capitulo
                chapter_name = chapters[0].get('chapter_name', '')
                match = re.search(r'(\d+(?:\.\d+)?)', chapter_name)
                
                if not match:
                    resultados.append({
                        'manga_id': mid,
                        'title': manga['title'],
                        'has_new': False,
                        'new_chapters_count': 0,
                        'last_checked_chapter': last_checked,
                        'current_chapter': None,
                        'nuevos_capitulos': []
                    })
                    msg = f"  [ERROR] No se pudo extraer numero de '{chapter_name}'"
                    print(msg)
                    if logger:
                        logger.log(msg)
                    continue
                
                current_chapter = match.group(1)
                
                # Calcular nuevos
                nuevos_capitulos = []
                has_new = False
                
                if last_checked:
                    try:
                        has_new = float(current_chapter) > float(last_checked)
                        if has_new:
                            for cap in chapters:
                                cap_name = cap.get('chapter_name', '')
                                cap_match = re.search(r'(\d+(?:\.\d+)?)', cap_name)
                                if not cap_match:
                                    continue
                                
                                cap_num_str = cap_match.group(1)
                                
                                try:
                                    if float(cap_num_str) > float(last_checked):
                                        nuevos_capitulos.append({
                                            'name': cap_num_str,
                                            'url': cap.get('url')
                                        })
                                    elif float(cap_num_str) <= float(last_checked):
                                        break
                                except ValueError:
                                    break
                    except ValueError:
                        has_new = current_chapter != last_checked
                        if has_new:
                            nuevos_capitulos.append({
                                'name': current_chapter,
                                'url': chapters[0].get('url')
                            })
                else:
                    has_new = True
                    for cap in chapters:
                        cap_name = cap.get('chapter_name', '')
                        cap_match = re.search(r'(\d+(?:\.\d+)?)', cap_name)
                        if cap_match:
                            nuevos_capitulos.append({
                                'name': cap_match.group(1),
                                'url': cap.get('url')
                            })
                
                resultados.append({
                    'manga_id': mid,
                    'title': manga['title'],
                    'has_new': has_new,
                    'new_chapters_count': len(nuevos_capitulos),
                    'last_checked_chapter': last_checked,
                    'current_chapter': current_chapter,
                    'nuevos_capitulos': nuevos_capitulos
                })
                
                msg = f"  [OK] Cap actual: {current_chapter}, Ultimo descargado: {last_checked} Nuevos: {len(nuevos_capitulos)}"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                
            except Exception as e:
                msg = f"  [ERROR] {e}"
                print(msg)
                if logger:
                    logger.log(msg)
                resultados.append({
                    'manga_id': mid,
                    'title': manga['title'],
                    'has_new': False,
                    'new_chapters_count': 0,
                    'last_checked_chapter': last_checked,
                    'current_chapter': None,
                    'nuevos_capitulos': []
                })
    
            import time
            time.sleep(5)        

        
        return resultados