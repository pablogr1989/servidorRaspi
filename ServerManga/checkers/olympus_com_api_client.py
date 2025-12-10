import requests
import time

class OlympusComAPIClient:
    BASE_URL = "https://olympusbiblioteca.com/api/series"
    
    def __init__(self):
        self.session = requests.Session()
        self._page_cache = {}
    
    
    #####################################################################################
    #                               NUEVOS CAPITULOS                                    #                            
    #####################################################################################
    
    
    def obtener_capitulos(self, slug, page=1, direction='desc'):
        """
        Obtener capitulos de una serie por slug
        """
        url = f"https://dashboard.olympusbiblioteca.com/api/series/{slug}/chapters"
        params = {
            "page": page,
            "direction": direction,
            "type": "comic"
        }
        time.sleep(2)
        
        try:
            response = self.session.get(url, params=params, timeout=60)
            print(response)
            if 'text/html' in response.headers.get('Content-Type', ''):
                print(f"[ERROR] Cloudflare bloqueo: {slug}")
                return None
            
            return response.json()
        except Exception as e:
            print(f"[ERROR] obtener_capitulos: {e}")
            return None
    
    def obtener_todos_capitulos(self, slug, direction='desc', mode_debug=False, logger=None):
        """Obtener TODOS los capitulos paginando automaticamente"""
        msg = f"[DEBUG] Obteniendo capitulos para slug '{slug}'..."
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        # Primera pagina
        data = self.obtener_capitulos(slug, page=1, direction=direction)
        
        if not data or 'data' not in data:
            msg = "[ERROR] No se pudieron obtener capitulos"
            print(msg)
            if logger:
                logger.log(msg)
            return None
        
        capitulos = data['data']
        meta = data.get('meta', {})
        last_page = meta.get('last_page', 1)
        total = meta.get('total', len(capitulos))
        
        msg = f"[DEBUG] Total capitulos: {total}, Paginas: {last_page}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        # Paginar si hay mas
        if last_page > 1:
            for page in range(2, last_page + 1):
                time.sleep(5)
                page_data = self.obtener_capitulos(slug, page=page, direction=direction)
                
                if page_data and 'data' in page_data:
                    capitulos.extend(page_data['data'])
                else:
                    msg = f"[WARN] Error obteniendo pagina {page}"
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
        
        msg = f"[DEBUG] Capitulos obtenidos: {len(capitulos)}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        return {
            'last_page': last_page,
            'total': total,
            'capitulos': capitulos
        }
        
    def obtener_nuevos_capitulos(self, slug, num_capitulo, direction='desc', mode_debug=False, logger=None):
        """Obtener TODOS los capitulos nuevos, paginando automaticamente"""
        msg = f"[DEBUG] Obteniendo capitulos {num_capitulo} y slug '{slug}'..."
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        data = self.obtener_capitulos(slug, page=1, direction=direction)
        
        if not data or 'data' not in data:
            msg = "[ERROR] No se pudieron obtener capitulos"
            print(msg)
            if logger:
                logger.log(msg)
            return None
        
        capitulos = data['data']
        meta = data.get('meta', {})
        last_page = meta.get('last_page', 1)
        total = meta.get('total', len(capitulos))
        nuevos_capitulos = []
        
        for capitulo in capitulos:
            if capitulo['name'] == num_capitulo:
                if mode_debug:
                    print(nuevos_capitulos)
                if logger:
                    logger.log(str(nuevos_capitulos))
                return nuevos_capitulos
            else:
                nuevos_capitulos.append(capitulo)
            
        if last_page > 1:
            for page in range(2, last_page + 1):
                time.sleep(5)
                page_data = self.obtener_capitulos(slug, page=page, direction=direction)
                capitulos = page_data['data']
                for capitulo in capitulos:  
                    if capitulo['name'] == num_capitulo:
                        if mode_debug:
                            print(nuevos_capitulos)
                        if logger:
                            logger.log(str(nuevos_capitulos))
                        return nuevos_capitulos
                    else:
                        nuevos_capitulos.append(capitulo)   
                        
    def obtener_ultimo_capitulo(self, slug, mode_debug=False, logger=None):
        """Obtener SOLO el ultimo capitulo (pagina 1)"""
        try:
            data = self.obtener_capitulos(slug, page=1, direction='desc')
            if data and 'data' in data and len(data['data']) > 0:
                return data['data'][0]['name']
            
            msg = f"[DEBUG] Respuesta invalida para slug '{slug}': {data}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            return None
        except Exception as e:
            msg = f"[ERROR] obtener_ultimo_capitulo({slug}): {e}"
            print(msg)
            if logger:
                logger.log(msg)
            return None
    
    @staticmethod
    def construir_url_capitulo(chapter_id, slug):
        """Construir URL de capitulo"""
        return f"https://olympusbiblioteca.com/capitulo/{chapter_id}/comic-{slug}"

    
    #####################################################################################
    #                               ACTUALIZAR SLUGS                                    #                            
    #####################################################################################
    def buscar_serie(self, nombre, max_pages=999, logger=None):
        nombre = nombre.lower()
        
        params = {
            "type": "comic",
            "direction": "desc",
            "page": 1
        }
        
        response = self.session.get(self.BASE_URL, params=params, timeout=10)
        data = response.json()
        
        series_block = self._extraer_series(data)
        if not series_block:
            return None
        
        last_page = min(series_block["last_page"], max_pages)
        
        for page in range(1, last_page + 1):
            if page > 1:
                params["page"] = page
                time.sleep(3)
                response = self.session.get(self.BASE_URL, params=params, timeout=10)
                data = response.json()
                series_block = self._extraer_series(data)
                if not series_block:
                    continue
            
            for serie in series_block["data"]:
                if nombre in serie["name"].lower():
                    return serie
        
        return None

    def buscar_multiples_series(self, manga_info_list, mode_debug=False, logger=None):
        """Buscar multiples series con sistema cache optimizado"""
        from database.db_manager import DatabaseManager
        
        db = DatabaseManager()
        resultados = {}
        
        msg = f"\n[BUSQUEDA] Iniciando para {len(manga_info_list)} manga(s)"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        # FASE 1: Validar check_url existente
        msg = f"[FASE 1] Validando check_url actuales..."
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        pendientes = []
        
        for manga_info in manga_info_list:
            mid = manga_info['id']
            
            # Obtener manga completo de DB
            manga = db.get_manga(mid)
            if not manga:
                msg = f"[ERROR] Manga ID {mid} no encontrado en DB"
                print(msg)
                if logger:
                    logger.log(msg)
                continue
            
            check_url = manga.get('check_url', '')
            
            if check_url and self._validar_check_url(check_url, logger=logger):
                msg = f"[OK] '{manga['title']}' check_url valido"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                
                resultados[mid] = {'serie': {'url': check_url}}
            else:
                msg = f"[PENDIENTE] '{manga['title']}' check_url invalido"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                
                pendientes.append(manga)
        
        if not pendientes:
            msg = f"[OK] Todos los check_url validos, no requiere busqueda"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            return resultados
        
        # FASE 2: Separar con/sin cache
        msg = f"\n[FASE 2] Verificando cache para {len(pendientes)} manga(s)..."
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        sin_cache = []
        con_cache = []
        
        for manga in pendientes:
            cache = db.get_olympus_cache(manga['id'])
            
            if cache:
                manga['cache'] = cache
                con_cache.append(manga)
                
                msg = f"[CACHE] '{manga['title']}' encontrado (asc:{cache['last_search_asc_page']}, desc:{cache['last_search_desc_page']}, valid:{cache['olympus_last_valid_direction']})"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
            else:
                sin_cache.append(manga)
                
                msg = f"[SIN CACHE] '{manga['title']}' requiere inicializacion"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
        
        # FASE 3: Inicializar mangas sin cache
        if sin_cache:
            msg = f"\n[FASE 3] Inicializando {len(sin_cache)} manga(s)..."
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            self._inicializar_cache_manga(sin_cache, mode_debug=mode_debug, logger=logger)
            
            # Recargar cache despues de inicializacion
            for manga in sin_cache:
                cache = db.get_olympus_cache(manga['id'])
                if cache:
                    manga['cache'] = cache
                    con_cache.append(manga)
                    
                    msg = f"[OK] '{manga['title']}' inicializado correctamente"
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                else:
                    msg = f"[ERROR] '{manga['title']}' inicializacion fallo"
                    print(msg)
                    if logger:
                        logger.log(msg)
        
        if not con_cache:
            msg = f"[WARN] No hay mangas con cache valido"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            return resultados
        
        # FASE 4: Agrupar por pagina y direction
        msg = f"\n[FASE 4] Agrupando {len(con_cache)} manga(s) por pagina..."
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        grupos = {}
        
        for manga in con_cache:
            cache = manga['cache']
            direction = cache['olympus_last_valid_direction']
            
            if direction == 'asc':
                page = cache['last_search_asc_page']
            else:
                page = cache['last_search_desc_page']
            
            key = (page, direction)
            
            if key not in grupos:
                grupos[key] = []
            
            grupos[key].append(manga)
        
        msg = f"[FASE 4] {len(grupos)} grupos creados"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        # FASE 5: Buscar en paginas cacheadas
        msg = f"\n[FASE 5] Buscando en paginas cacheadas..."
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        reinicializar = []
        
        for (page, direction), manga_grupo in grupos.items():
            msg = f"[GRUPO] Procesando pagina {page} {direction.upper()} ({len(manga_grupo)} mangas)"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            try:
                url = "https://olympusbiblioteca.com/api/series"
                params = {'type': 'comic', 'direction': direction, 'page': page}
                response = self.session.get(url, params=params, timeout=30)
                data = response.json()
                series_list = data['data']['series']['data']
                
            except Exception as e:
                msg = f"[ERROR] Fallo fetching pagina {page} {direction}: {e}"
                print(msg)
                if logger:
                    logger.log(msg)
                
                # Todos los mangas de este grupo van a reinicializar
                reinicializar.extend(manga_grupo)
                continue
            
            # Buscar cada manga del grupo en esta pagina
            for manga in manga_grupo:
                encontrado = False
                nombre_buscar = OlympusComAPIClient._normalizar_nombre(manga['title'])
                
                for serie in series_list:
                    nombre_serie = OlympusComAPIClient._normalizar_nombre(serie['name'])
                    if nombre_serie == nombre_buscar:
                        encontrado = True
                        slug = serie['slug']
                        
                        msg = f"  [FOUND] '{manga['title']}' slug: {slug}"
                        if mode_debug:
                            print(msg)
                        if logger:
                            logger.log(msg)
                        
                        # Validar slug
                        if self._validar_slug_construido(slug, logger=logger):
                            msg = f"  [OK] Slug valido"
                            if mode_debug:
                                print(msg)
                            if logger:
                                logger.log(msg)
                            
                            resultados[manga['id']] = {'serie': {'slug': slug}}
                        else:
                            msg = f"  [INVALIDO] Slug invalido, probando direction contrario"
                            if mode_debug:
                                print(msg)
                            if logger:
                                logger.log(msg)
                            
                            # Probar direction contrario
                            direction_contrario = 'asc' if direction == 'desc' else 'desc'
                            
                            if direction_contrario == 'asc':
                                page_contrario = manga['cache']['last_search_asc_page']
                            else:
                                page_contrario = manga['cache']['last_search_desc_page']
                            
                            try:
                                params_contrario = {'type': 'comic', 'direction': direction_contrario, 'page': page_contrario}
                                response_contrario = self.session.get(url, params=params_contrario, timeout=30)
                                data_contrario = response_contrario.json()
                                series_contrario = data_contrario['data']['series']['data']
                                
                                msg = f"  [GRUPO] Procesando pagina contraria {page_contrario} {direction_contrario.upper()}"
                                if mode_debug:
                                    print(msg)
                                if logger:
                                    logger.log(msg)
                                
                                for serie_contrario in series_contrario:
                                    nombre_serie_contrario = OlympusComAPIClient._normalizar_nombre(serie_contrario['name'])
                                    if nombre_serie_contrario == nombre_buscar:
                                        slug_contrario = serie_contrario['slug']
                                        
                                        msg = f"  [FOUND] '{manga['title']}' slug: {slug_contrario}"
                                        if mode_debug:
                                            print(msg)
                                        if logger:
                                            logger.log(msg)
                                        
                                        if self._validar_slug_construido(slug_contrario, logger=logger):
                                            msg = f"  [OK] Slug valido en {direction_contrario.upper()}"
                                            if mode_debug:
                                                print(msg)
                                            if logger:
                                                logger.log(msg)
                                            
                                            resultados[manga['id']] = {'serie': {'slug': slug_contrario}}
                                            
                                            # Actualizar direction valido
                                            db.update_olympus_cache_direction(manga['id'], direction_contrario)
                                        else:
                                            msg = f"  [ERROR] Ambos slugs invalidos"
                                            print(msg)
                                            if logger:
                                                logger.log(msg)
                                        
                                        break
                            
                            except Exception as e:
                                msg = f"  [ERROR] Fallo buscando en {direction_contrario}: {e}"
                                if logger:
                                    logger.log(msg)
                        
                        break
                
                if not encontrado:
                    msg = f"  [NO ENCONTRADO] '{manga['title']}' no en pagina {page} {direction}, requiere reinicializacion"
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                    
                    reinicializar.append(manga)
        
        # FASE 6: Reinicializar mangas no encontrados
        if reinicializar:
            msg = f"\n[FASE 6] Reinicializando {len(reinicializar)} manga(s)..."
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            # Eliminar cache viejo
            for manga in reinicializar:
                db.delete_olympus_cache(manga['id'])
            
            # Reinicializar
            self._inicializar_cache_manga(reinicializar, mode_debug=mode_debug, logger=logger)
            
            # Buscar slugs de mangas reinicializados
            for manga in reinicializar:
                cache = db.get_olympus_cache(manga['id'])
                if not cache:
                    msg = f"[ERROR] '{manga['title']}' reinicializacion fallo"
                    print(msg)
                    if logger:
                        logger.log(msg)
                    continue
                
                direction = cache['olympus_last_valid_direction']
                
                if direction == 'asc':
                    page = cache['last_search_asc_page']
                else:
                    page = cache['last_search_desc_page']
                
                try:
                    url = "https://olympusbiblioteca.com/api/series"
                    params = {'type': 'comic', 'direction': direction, 'page': page}
                    response = self.session.get(url, params=params, timeout=30)
                    data = response.json()
                    series_list = data['data']['series']['data']
                    
                    nombre_buscar = manga['title'].lower()
                    
                    nombre_buscar = OlympusComAPIClient._normalizar_nombre(manga['title'])
                    
                    for serie in series_list:
                        nombre_serie = OlympusComAPIClient._normalizar_nombre(serie['name'])
                        if nombre_serie == nombre_buscar:
                            resultados[manga['id']] = {'serie': {'slug': serie['slug']}}
                            
                            msg = f"[OK] '{manga['title']}' slug obtenido tras reinicializacion"
                            if mode_debug:
                                print(msg)
                            if logger:
                                logger.log(msg)
                            break
                
                except Exception as e:
                    msg = f"[ERROR] Fallo obteniendo slug de '{manga['title']}': {e}"
                    print(msg)
                    if logger:
                        logger.log(msg)
        
        msg = f"\n[FINAL] Busqueda completada: {len(resultados)}/{len(manga_info_list)} encontrados"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        return resultados

    def _extraer_series(self, json_data):
        if "series" in json_data:
            return json_data["series"]
        if "data" in json_data and "series" in json_data["data"]:
            return json_data["data"]["series"]
        return None
    
    def _buscar_en_pagina_url(self, page_url, nombre_buscar, lista_sin_url, resultados, logger=None):
        """
        Buscar nombre_buscar en page_url
        Aprovecha para buscar tambien los de lista_sin_url
        Return: (serie, page_url) si encontrado, None si no
        """
        data = self._get_page_cached(page_url)
        if not data:
            return None
        
        series_block = self._extraer_series(data)
        if not series_block:
            return None
        
        encontrado_principal = None
        
        for serie in series_block["data"]:
            nombre_serie = serie["name"].lower()
            
            # Buscar el principal
            if nombre_buscar in nombre_serie:
                encontrado_principal = (serie, page_url)
            
            # Aprovechar para buscar sin_url
            for manga_sin_url in lista_sin_url:
                if manga_sin_url['id'] in resultados:
                    continue
                if manga_sin_url['title'].lower() in nombre_serie:
                    resultados[manga_sin_url['id']] = {
                        'serie': serie,
                        'page_url': page_url
                    }
                    
                    msg = f"[DEBUG] Bonus: encontrado '{manga_sin_url['title']}' en esta pagina"
                    if logger:
                        logger.log(msg)
        
        return encontrado_principal
    
    def _busqueda_exhaustiva(self, manga_list, resultados, mode_debug=False, logger=None):
        """Buscar en todas las paginas"""
        # Obtener total de paginas
        first_page_url = f"{self.BASE_URL}?type=comic&direction=desc&page=1"
        data = self._get_page_cached(first_page_url)
        
        series_block = self._extraer_series(data)
        if not series_block:
            msg = "[ERROR] No se pudo obtener total de paginas"
            print(msg)
            if logger:
                logger.log(msg)
            return
        
        last_page = series_block["last_page"]
        
        msg = f"[DEBUG] Total paginas: {last_page}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        pendientes = {m['id']: m['title'].lower() for m in manga_list}
        
        for page in range(1, last_page + 1):
            msg = f'Buscando en la pagina {page} de {last_page}'
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            if not pendientes:
                msg = f"[DEBUG] Todos encontrados en pagina {page-1}"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                break
            
            page_url = f"{self.BASE_URL}?type=comic&direction=desc&page={page}"
            data = self._get_page_cached(page_url)
            
            if not data:
                continue
            
            series_block = self._extraer_series(data)
            if not series_block:
                continue
            
            encontrados_ids = []
            
            for serie in series_block["data"]:
                nombre_serie = serie["name"].lower()
                for manga_id, nombre_buscar in pendientes.items():
                    if nombre_buscar in nombre_serie:
                        resultados[manga_id] = {
                            'serie': serie,
                            'page_url': page_url
                        }
                        encontrados_ids.append(manga_id)
                        
                        msg = f"[DEBUG]{nombre_buscar} Encontrado en pagina {page}"
                        if mode_debug:
                            print(msg)
                        if logger:
                            logger.log(msg)
            
            for mid in encontrados_ids:
                del pendientes[mid]
            
            if page < last_page:
                time.sleep(3)
    
    def _get_adjacent_urls(self, url):
        """Obtener URLs prev y next"""
        data = self._get_page_cached(url)
        if not data:
            return []
        
        series_block = self._extraer_series(data)
        if not series_block:
            return []
        
        urls = []
        if series_block.get("prev_page_url"):
            urls.append(series_block["prev_page_url"])
        if series_block.get("next_page_url"):
            urls.append(series_block["next_page_url"])
        
        return urls
    
    def _get_page_cached(self, url):
        """Obtener pagina con cache"""
        if url not in self._page_cache:
            try:
                response = self.session.get(url, timeout=10)
                self._page_cache[url] = response.json()
            except Exception as e:
                print(f"[ERROR] Error obteniendo {url}: {e}")
                return None
        
        return self._page_cache[url]

    def _validar_slug_construido(self, slug, logger=None):
        """Validar URL construida con slug usando GET request (no HEAD)"""
        check_url = f"https://olympusbiblioteca.com/series/comic-{slug}"
        
        try:
            # Usar GET en vez de HEAD (algunos servidores no soportan HEAD bien)
            response = self.session.get(check_url, timeout=15, allow_redirects=True)
            
            # Si status 200 y no es error page
            if response.status_code == 200:
                # Verificar que no sea pagina de error
                if 'series' in response.url and 'error' not in response.url.lower():
                    return True
            
            if logger:
                logger.log(f"[DEBUG] Slug '{slug}' invalido (status: {response.status_code}, url: {response.url})")
            
            return False
            
        except Exception as e:
            if logger:
                logger.log(f"[DEBUG] Validacion slug '{slug}' fallo: {e}")
            return False
         
    def _validar_check_url(self, check_url, logger=None):
        """Validar si check_url actual es valido con HEAD request"""
        try:
            response = self.session.head(check_url, timeout=15, allow_redirects=True)
            
            # Si es 200 y no es HTML Cloudflare
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type or 'series' in check_url:
                    return True
            
            return False
            
        except Exception as e:
            if logger:
                logger.log(f"[DEBUG] Validacion check_url fallo: {e}")
            return False
                
    @staticmethod
    def _normalizar_nombre(nombre):
        """Normalizar nombre para comparacion (lowercase, sin espacios extras, sin puntuacion)"""
        import re
        
        # Lowercase
        nombre = nombre.lower()
        
        # Remover espacios extras (multiples espacios, inicio, fin)
        nombre = ' '.join(nombre.split())
        
        # Remover puntuacion y caracteres especiales (mantener espacios y letras)
        nombre = re.sub(r'[^\w\s]', '', nombre)
        
        # Remover espacios restantes
        nombre = nombre.replace(' ', '')
        
        return nombre
                
    def _inicializar_cache_manga(self, manga_list, mode_debug=False, logger=None):
        """Inicializar cache para mangas sin entrada en olympus_com_cache"""
        
        from database.db_manager import DatabaseManager
        
        if not manga_list:
            return
        
        db = DatabaseManager()
        
        msg = f"\n[INIT] Inicializando cache para {len(manga_list)} manga(s)..."
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        # Obtener total paginas
        try:
            url = "https://olympusbiblioteca.com/api/series"
            params = {'type': 'comic', 'direction': 'asc', 'page': 1}
            response = self.session.get(url, params=params, timeout=30)
            data = response.json()
            total_pages = data['data']['series']['last_page']
            
            msg = f"[INIT] Total paginas API: {total_pages}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
        except Exception as e:
            msg = f"[ERROR] No se pudo obtener total paginas: {e}"
            print(msg)
            if logger:
                logger.log(msg)
            return
        
        # Diccionario para almacenar resultados
        resultados = {}
        for manga in manga_list:
            resultados[manga['id']] = {
                'asc_page': None,
                'desc_page': None,
                'asc_slug': None,
                'desc_slug': None
            }
        
        # FASE 1: Buscar en ASC
        msg = f"[INIT] Buscando en orden ASC..."
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        pendientes_asc = set(m['id'] for m in manga_list)
        
        for page in range(1, total_pages + 1):
            if not pendientes_asc:
                break
            
            if page % 10 == 0:
                msg = f"[INIT] Progreso ASC: {page}/{total_pages}"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
            
            try:
                params = {'type': 'comic', 'direction': 'asc', 'page': page}
                response = self.session.get(url, params=params, timeout=30)
                data = response.json()
                series_list = data['data']['series']['data']
                
                # Buscar todos los mangas pendientes en esta pagina
                for manga in manga_list:
                    if manga['id'] not in pendientes_asc:
                        continue
                    
                    nombre_buscar = OlympusComAPIClient._normalizar_nombre(manga['title'])
                    
                    for serie in series_list:
                        nombre_serie = OlympusComAPIClient._normalizar_nombre(serie['name'])
                        if nombre_serie == nombre_buscar:
                            resultados[manga['id']]['asc_page'] = page
                            resultados[manga['id']]['asc_slug'] = serie['slug']
                            pendientes_asc.remove(manga['id'])
                            
                            msg = f"[INIT] '{manga['title']}' encontrado en ASC pagina {page}"
                            if mode_debug:
                                print(msg)
                            if logger:
                                logger.log(msg)
                            break
            
            except Exception as e:
                msg = f"[ERROR] Fallo en ASC pagina {page}: {e}"
                if logger:
                    logger.log(msg)
                continue
        
        # FASE 2: Buscar en DESC
        msg = f"[INIT] Buscando en orden DESC..."
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        pendientes_desc = set(m['id'] for m in manga_list)
        
        for page in range(1, total_pages + 1):
            if not pendientes_desc:
                break
            
            if page % 10 == 0:
                msg = f"[INIT] Progreso DESC: {page}/{total_pages}"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
            
            try:
                params = {'type': 'comic', 'direction': 'desc', 'page': page}
                response = self.session.get(url, params=params, timeout=30)
                data = response.json()
                series_list = data['data']['series']['data']
                
                # Buscar todos los mangas pendientes en esta pagina
                for manga in manga_list:
                    if manga['id'] not in pendientes_desc:
                        continue
                    
                    nombre_buscar = OlympusComAPIClient._normalizar_nombre(manga['title'])
                    
                    for serie in series_list:
                        nombre_serie = OlympusComAPIClient._normalizar_nombre(serie['name'])
                        if nombre_serie == nombre_buscar:
                            resultados[manga['id']]['desc_page'] = page
                            resultados[manga['id']]['desc_slug'] = serie['slug']
                            pendientes_desc.remove(manga['id'])
                            
                            msg = f"[INIT] '{manga['title']}' encontrado en DESC pagina {page}"
                            if mode_debug:
                                print(msg)
                            if logger:
                                logger.log(msg)
                            break
            
            except Exception as e:
                msg = f"[ERROR] Fallo en DESC pagina {page}: {e}"
                if logger:
                    logger.log(msg)
                continue
        
        # FASE 3: Validar slugs y guardar en cache
        msg = f"\n{'='*60}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"[INIT] Validando slugs encontrados..."
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"{'='*60}\n"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        for manga in manga_list:
            mid = manga['id']
            res = resultados[mid]
            
            # Verificar que se encontro en ambas paginas
            if res['asc_page'] is None or res['desc_page'] is None:
                msg = f"\n{'*'*60}"
                print(msg)
                if logger:
                    logger.log(msg)
                
                msg = f"[ERROR CRITICO] '{manga['title']}' NO ENCONTRADO EN API"
                print(msg)
                if logger:
                    logger.log(msg)
                
                msg = f"[ERROR CRITICO] ASC page: {res['asc_page']}, DESC page: {res['desc_page']}"
                print(msg)
                if logger:
                    logger.log(msg)
                
                msg = f"[ERROR CRITICO] Verificar que el nombre en DB coincida exactamente con API"
                print(msg)
                if logger:
                    logger.log(msg)
                
                msg = f"{'*'*60}\n"
                print(msg)
                if logger:
                    logger.log(msg)
                continue
            
            # Validar ambos slugs
            asc_valido = self._validar_slug_construido(res['asc_slug'], logger=logger)
            desc_valido = self._validar_slug_construido(res['desc_slug'], logger=logger)
            
            if not asc_valido and not desc_valido:
                msg = f"\n{'*'*60}"
                print(msg)
                if logger:
                    logger.log(msg)
                
                msg = f"[ERROR CRITICO] '{manga['title']}' AMBOS SLUGS INVALIDOS"
                print(msg)
                if logger:
                    logger.log(msg)
                
                msg = f"[ERROR CRITICO] Slug ASC: {res['asc_slug']}"
                print(msg)
                if logger:
                    logger.log(msg)
                
                msg = f"[ERROR CRITICO] Slug DESC: {res['desc_slug']}"
                print(msg)
                if logger:
                    logger.log(msg)
                
                msg = f"{'*'*60}\n"
                print(msg)
                if logger:
                    logger.log(msg)
                continue
            
            # Determinar direction valido por defecto
            if desc_valido:
                valid_direction = 'desc'
            else:
                valid_direction = 'asc'
            
            # Insertar en cache
            try:
                db.insert_olympus_cache(
                    mid, 
                    res['asc_page'], 
                    res['desc_page'], 
                    valid_direction
                )
                
                msg = f"[INIT] '{manga['title']}' cache creado (asc:{res['asc_page']}, desc:{res['desc_page']}, valid:{valid_direction})"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
            
            except Exception as e:
                msg = f"[ERROR] No se pudo guardar cache para '{manga['title']}': {e}"
                print(msg)
                if logger:
                    logger.log(msg)