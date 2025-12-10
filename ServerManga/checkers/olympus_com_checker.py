from checkers.base_checker import BaseChecker
from checkers.olympus_com_api_client import OlympusComAPIClient

class OlympusComChecker(BaseChecker):    
    
    @staticmethod
    def check_single(manga_data, mode_debug=False, logger=None):
        api = OlympusComAPIClient()
        
        slug = manga_data.get('slug')
        if not slug:
            msg = f"[ERROR] '{manga_data['title']}' sin slug"
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
            nuevos_caps = api.obtener_nuevos_capitulos(
                slug, 
                manga_data['last_checked_chapter'],
                logger=logger,
                mode_debug=mode_debug
            )
            
            if nuevos_caps:
                return {
                    'manga_id': manga_data['id'],
                    'title': manga_data['title'],
                    'has_new': True,
                    'new_chapters_count': len(nuevos_caps),
                    'last_checked_chapter': manga_data['last_checked_chapter'],
                    'current_chapter': nuevos_caps[0]['name'],
                    'nuevos_capitulos': nuevos_caps
                }
            else:
                return {
                    'manga_id': manga_data['id'],
                    'title': manga_data['title'],
                    'has_new': False,
                    'new_chapters_count': 0,
                    'last_checked_chapter': manga_data['last_checked_chapter'],
                    'current_chapter': manga_data['last_checked_chapter'],
                    'nuevos_capitulos': []
                }
                
        except Exception as e:
            msg = f"[ERROR] {manga_data['title']}: {e}"
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
            
    @staticmethod
    def check_batch(manga_list, mode_debug=True, logger=None):
        from database.db_manager import DatabaseManager
        
        api = OlympusComAPIClient()
        db = DatabaseManager()
        
        resultados = []
        
        for manga in manga_list:
            mid = manga['id']
            slug = manga.get('slug')
            last_checked = manga.get('last_checked_chapter')
            
            if not slug:
                msg = f"[WARN] '{manga['title']}' sin slug"
                if mode_debug:
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
            
            msg = f"[CHECKING] {manga['title']} (slug: {slug})"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            try:
                nuevos_caps = api.obtener_nuevos_capitulos(slug, last_checked, logger=logger, mode_debug = mode_debug)
                
                if nuevos_caps:
                    resultados.append({
                        'manga_id': mid,
                        'title': manga['title'],
                        'has_new': True,
                        'new_chapters_count': len(nuevos_caps),
                        'last_checked_chapter': last_checked,
                        'current_chapter': nuevos_caps[0]['name'],
                        'nuevos_capitulos': nuevos_caps
                    })
                    
                    msg = f"  [OK] Nuevos: {len(nuevos_caps)}, Ultimo: {nuevos_caps[0]['name']}"
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                else:
                    resultados.append({
                        'manga_id': mid,
                        'title': manga['title'],
                        'has_new': False,
                        'new_chapters_count': 0,
                        'last_checked_chapter': last_checked,
                        'current_chapter': last_checked,
                        'nuevos_capitulos': []
                    })
                    
                    msg = f"  [OK] Sin capitulos nuevos. Cap actual: {last_checked}, Ultimo descargado: {last_checked}"
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
            time.sleep(60)
        
        return resultados
    
    
    @staticmethod
    def actualizar_todos_slugs(mode_debug=False, logger=None):
        """Actualizar check_url y slug de TODOS los mangas olympus_com en DB"""
        from database.db_manager import DatabaseManager
        
        db = DatabaseManager()
        api = OlympusComAPIClient()
        
        # Obtener page_type olympus_com
        page_type = db.get_page_type('olympus_com')
        if not page_type:
            msg = "[ERROR] page_type 'olympus_com' no encontrado"
            print(msg)
            if logger:
                logger.log(msg)
            return
        
        # Obtener todos los mangas de este tipo
        all_manga = db.get_manga_by_page_type(page_type['id'])
        
        if not all_manga:
            msg = "[INFO] No hay mangas olympus_com en la base de datos"
            print(msg)
            if logger:
                logger.log(msg)
            return
        
        msg = f"\n{'='*60}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"ACTUALIZACION MASIVA DE SLUGS - {len(all_manga)} mangas"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"{'='*60}\n"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        # Preparar info
        manga_info_list = [{
            'id': m['id'],
            'title': m['title']
        } for m in all_manga]
        
        # Buscar todos con optimizacion
        resultados_busqueda = api.buscar_multiples_series(manga_info_list, mode_debug=mode_debug, logger=logger)
        
        actualizados = 0
        no_encontrados = 0
        
        for manga in all_manga:
            mid = manga['id']
            
            msg = f"\nProcesando: {manga['title']}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            if mid in resultados_busqueda:
                serie = resultados_busqueda[mid]['serie']
                
                # Verificar si es formato URL (check_url ya valido) o slug (nuevo)
                if 'url' in serie:
                    # check_url ya era valido, no actualizar nada
                    msg = f"  [OK] check_url ya valido, sin cambios"
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                    
                    actualizados += 1
                
                elif 'slug' in serie:
                    # Nuevo slug encontrado, actualizar
                    new_slug = serie['slug']
                    new_check_url = f"https://olympusbiblioteca.com/series/comic-{new_slug}"
                    
                    # Actualizar check_url y slug
                    with db.get_connection() as conn:
                        conn.execute('''UPDATE manga 
                                    SET check_url = ?, slug = ? 
                                    WHERE id = ?''',
                                (new_check_url, new_slug, mid))
                    
                    msg = f"  [OK] URL: {new_check_url}"
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                    
                    msg = f"  [OK] Slug: {new_slug}"
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                    
                    # Descargar cover (construir serie completa para metodo)
                    serie_completa = {'slug': new_slug, 'cover': None}
                    
                    # Intentar obtener cover de API si es necesario
                    try:
                        cache = db.get_olympus_cache(mid)
                        if cache:
                            direction = cache['olympus_last_valid_direction']
                            
                            if direction == 'asc':
                                page = cache['last_search_asc_page']
                            else:
                                page = cache['last_search_desc_page']
                            
                            url = "https://olympusbiblioteca.com/api/series"
                            params = {'type': 'comic', 'direction': direction, 'page': page}
                            response = api.session.get(url, params=params, timeout=30)
                            data = response.json()
                            series_list = data['data']['series']['data']
                            
                            nombre_buscar = manga['title'].lower()
                            
                            for s in series_list:
                                if s['name'].lower() == nombre_buscar:
                                    serie_completa['cover'] = s.get('cover')
                                    break
                    
                    except Exception as e:
                        msg = f"  [WARN] No se pudo obtener cover: {e}"
                        if logger:
                            logger.log(msg)
                    
                    OlympusComChecker._descargar_cover(serie_completa, manga, mode_debug=mode_debug, logger=logger)
                    
                    actualizados += 1
                
                else:
                    msg = f"  [ERROR] Formato serie invalido"
                    print(msg)
                    if logger:
                        logger.log(msg)
                    no_encontrados += 1
            
            else:
                msg = f"  [ERROR] {manga['title']} No encontrado en API Olympus_COM"
                print(msg)
                if logger:
                    logger.log(msg)
                no_encontrados += 1
        
        msg = f"\n{'='*60}"
        print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"RESUMEN:"
        print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"  - Actualizados: {actualizados}/{len(all_manga)}"
        print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"  - No encontrados: {no_encontrados}"
        print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"{'='*60}\n"
        print(msg)
        if logger:
            logger.log(msg)
    
    @staticmethod
    def _descargar_cover(serie, manga_data, mode_debug=False, logger=None):
        """Descargar cover del manga si no existe"""
        import requests
        import os
        
        cover_url = serie.get('cover')
        if not cover_url:
            msg = f"[WARN] No hay cover URL para '{manga_data['title']}'"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            return
        
        # Crear directorio manga si no existe
        manga_dir = manga_data['local_storage_path']
        os.makedirs(manga_dir, exist_ok=True)
        
        cover_path = os.path.join(manga_dir, 'portada.webp')
        
        # Si ya existe, skip
        if os.path.exists(cover_path):
            msg = f"[INFO] Cover ya existe para '{manga_data['title']}'"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            return
        
        # Descargar
        try:
            msg = f"[INFO] Descargando cover para '{manga_data['title']}'..."
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            response = requests.get(cover_url, timeout=15)
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