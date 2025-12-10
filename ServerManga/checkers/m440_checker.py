from checkers.base_checker import BaseChecker
from playwright.sync_api import sync_playwright
import re
import json
import time
import os

class M440Checker(BaseChecker):
    
    @staticmethod
    def check_single(manga_data, mode_debug=False, logger=None):
        """Verifica un solo manga instanciando su propio navegador"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                return M440Checker._process_manga(manga_data, browser, mode_debug, logger)
            finally:
                browser.close()

    @staticmethod
    def check_batch(manga_list, mode_debug=True, logger=None):
        """Batch processing"""
        resultados = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for manga in manga_list:
                try:
                    res = M440Checker._process_manga(manga, browser, mode_debug, logger)
                    resultados.append(res)
                except Exception as e:
                    msg = f"[ERROR BATCH] Fallo procesando {manga['title']}: {e}"
                    print(msg)
                    if logger: logger.log(msg)
                    resultados.append(M440Checker._empty_result(manga['id'], manga['title'], manga.get('last_checked_chapter')))
                time.sleep(2)
            browser.close()
        return resultados

    @staticmethod
    def _process_manga(manga_data, browser, mode_debug, logger):
        manga_id = manga_data['id']
        title = manga_data['title']
        check_url = manga_data['check_url']
        last_checked = manga_data.get('last_checked_chapter')
        
        msg = f"[CHECKING] {title} (M440 via Playwright)"
        if mode_debug: print(msg)
        if logger: logger.log(msg)

        page = browser.new_page()
        capitulos_encontrados = []
        
        try:
            # Headers para simular usuario real
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'es-ES,es;q=0.9'
            })

            # Navegar
            page.goto(check_url, timeout=60000, wait_until='domcontentloaded')
            
            # Esperas inteligentes: Intentar esperar al footer o al contenedor de la lista
            try:
                page.wait_for_selector('div.footer, ul#AAIcIabCiEbCBNuZ', state='attached', timeout=15000)
            except:
                if mode_debug: print("  [WARN] Timeout esperando selectores clave. Continuando...")

            page_title = page.title()
            if mode_debug: print(f"  [DEBUG] Título: '{page_title}'")

            # Verificación anti-bot simple
            if "Just a moment" in page_title or "Cloudflare" in page_title:
                msg = "  [ERROR] BLOQUEADO POR CLOUDFLARE"
                print(msg)
                if logger: logger.log(msg)
                page.close()
                return M440Checker._empty_result(manga_id, title, last_checked)

            # --- ESTRATEGIA 1: BUSQUEDA PROFUNDA DE JSON EN SCRIPTS ---
            # Buscamos cualquier array de objetos que tenga "number" y "slug"
            scripts = page.query_selector_all('script')
            for script in scripts:
                content = script.inner_text()
                if not content or "slug" not in content: continue
                
                # Regex para encontrar arrays JSON: [{...}]
                # Busca bloques que empiecen con [{, contengan "number":, "slug": y terminen en }]
                matches = re.findall(r'(\[\s*\{.*?"number"\s*:.*?"slug"\s*:.*?\}\s*\])', content, re.DOTALL)
                
                for json_str in matches:
                    try:
                        data = json.loads(json_str)
                        if isinstance(data, list) and len(data) > 0 and 'slug' in data[0]:
                            msg = f"  [DEBUG] ESTRATEGIA 1 (JSON): Encontrados {len(data)} capítulos"
                            if mode_debug: print(msg)
                            if logger: logger.log(msg)
                            
                            for cap in data:
                                c_num = str(cap.get('number', '')).strip()
                                c_slug = cap.get('slug', '')
                                if c_num and c_slug:
                                    base = check_url.rstrip('/')
                                    capitulos_encontrados.append({'name': c_num, 'url': f"{base}/{c_slug}"})
                            break
                    except:
                        continue # JSON inválido, seguir buscando
                
                if capitulos_encontrados: break

            # --- ESTRATEGIA 2: FALLBACK DOM (Si JS ejecutó y pintó el HTML) ---
            if not capitulos_encontrados:
                if mode_debug: print("  [INFO] Intentando ESTRATEGIA 2 (DOM Scraping)...")
                
                # Buscamos enlaces con los atributos data-number y data-whatever
                links = page.query_selector_all('a[data-number][data-whatever]')
                
                if links:
                    msg = f"  [DEBUG] ESTRATEGIA 2 (DOM): Encontrados {len(links)} elementos"
                    if mode_debug: print(msg)
                    if logger: logger.log(msg)
                    
                    for link in links:
                        c_num = link.get_attribute('data-number')
                        c_slug = link.get_attribute('data-whatever') # El atributo data-whatever tiene el slug
                        
                        if c_num and c_slug:
                            base = check_url.rstrip('/')
                            # A veces data-whatever es solo el slug, a veces ruta relativa. Construimos con cuidado.
                            capitulos_encontrados.append({'name': str(c_num), 'url': f"{base}/{c_slug}"})

            page.close()

            # --- RESULTADO ---
            if not capitulos_encontrados:
                msg = "  [ERROR] No se encontraron capítulos ni por JSON ni por DOM."
                print(msg)
                if logger: logger.log(msg)
                
                # Debug HTML
                try:
                    debug_file = f"/tmp/m440_fail_{manga_id}.html"
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(page.content())
                    if mode_debug: print(f"  [DEBUG] HTML guardado en {debug_file}")
                except: pass
                
                return M440Checker._empty_result(manga_id, title, last_checked)

            # Ordenar y filtrar
            try:
                capitulos_encontrados.sort(key=lambda x: float(x['name']), reverse=True)
            except ValueError:
                capitulos_encontrados.sort(key=lambda x: x['name'], reverse=True)

            current_chapter = capitulos_encontrados[0]['name']
            
            # Filtrar nuevos
            nuevos = []
            if last_checked:
                try:
                    l_chk = float(last_checked)
                    for cap in capitulos_encontrados:
                        if float(cap['name']) > l_chk:
                            nuevos.append(cap)
                except ValueError:
                    for cap in capitulos_encontrados:
                        if cap['name'] != last_checked:
                            nuevos.append(cap)
            else:
                nuevos = capitulos_encontrados

            has_new = len(nuevos) > 0
            msg = f"  [OK] Ultimo: {current_chapter} | Nuevos: {len(nuevos)}"
            if mode_debug: print(msg)
            if logger: logger.log(msg)

            return {
                'manga_id': manga_id,
                'title': title,
                'has_new': has_new,
                'new_chapters_count': len(nuevos),
                'last_checked_chapter': last_checked,
                'current_chapter': current_chapter,
                'nuevos_capitulos': nuevos
            }

        except Exception as e:
            msg = f"  [ERROR CRITICO] {e}"
            print(msg)
            if logger: 
                logger.log(msg)
                import traceback
                logger.log(traceback.format_exc())
            try: page.close()
            except: pass
            return M440Checker._empty_result(manga_id, title, last_checked)

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