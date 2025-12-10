#!/usr/bin/env python3
"""
Worker que checkea capitulos nuevos Y descarga automaticamente
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager
from check_worker import check_all_manga, check_single_manga
from download_worker import download_manga
from utils.logger import Logger, create_log_path

def check_and_download_single(id = 0, mode_debug = True, logger = None):
    """Chequear capitulos y descargar nuevos automaticamente de un solo manga"""
    msg = f"\n{'='*60}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = "MANGA CHECK + DOWNLOAD WORKER (OPTIMIZADO)"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"{'='*60}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    # PASO 1: Chequear capitulos
    msg = "\n[FASE 1] Chequeando capitulos nuevos..."
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    results, check_time = check_single_manga(id, mode_debug=mode_debug, logger=logger)    
    print("El check lo he hecho bien")
    print(results)
    results, descargados, check_time = _download_mangas(results, check_time, mode_debug=mode_debug, logger=logger)
    
    return results, descargados, check_time

def check_and_download(page_mode=0, mode_debug=True, logger=None):
    """Chequear capitulos y descargar nuevos automaticamente"""
    msg = f"\n{'='*60}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = "MANGA CHECK + DOWNLOAD WORKER (OPTIMIZADO)"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"{'='*60}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    # PASO 1: Chequear capitulos
    msg = "\n[FASE 1] Chequeando capitulos nuevos..."
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    results, check_time = check_all_manga(page_mode, mode_debug=mode_debug, logger=logger)    
    results, descargados, check_time = _download_mangas(results, check_time, mode_debug=mode_debug, logger=logger)
    
    return results, descargados, check_time
    

def _download_mangas(results, check_time, mode_debug=True, logger=None):    
    
    if not results:
        msg = "\n[INFO] No hay manga en seguimiento o no se pudieron chequear"
        print(msg)
        if logger:
            logger.log(msg)
        return [], 0, check_time
    
    # Filtrar solo los que tienen nuevos
    con_nuevos = [r for r in results if r.get('has_new', False)]
    
    if not con_nuevos:
        msg = "\n[INFO] No hay capitulos nuevos para descargar"
        print(msg)
        if logger:
            logger.log(msg)
        return results, 0, check_time
    
    msg = f"\n[INFO] {len(con_nuevos)} manga(s) con capitulos nuevos"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    # PASO 2: Descargar capitulos nuevos
    msg = f"\n{'='*60}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = "[FASE 2] Descargando capitulos nuevos..."
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"{'='*60}\n"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    descargados = 0
    
    from download_worker import download_manga_from_list, download_manga
    from playwright.sync_api import sync_playwright
    
    # Crear browser UNA VEZ para todos los mangas
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for result in con_nuevos:
            manga_id = result['manga_id']
            title = result['title']
            new_count = result['new_chapters_count']
            current_chapter = result['current_chapter']
            last_checked = result['last_checked_chapter']
            nuevos_caps = result.get('nuevos_capitulos')
            
            msg = f"\n{'='*60}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            msg = f"DESCARGANDO: {title}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            msg = f"{'='*60}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            msg = f"Capitulos nuevos: {new_count}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            msg = f"Ultimo disponible: {current_chapter}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            msg = f"Ultimo descargado: {last_checked}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            # OPTIMIZACION: Usar lista si existe
            if nuevos_caps and len(nuevos_caps) > 0:
                msg = f"[INFO] Usando lista optimizada ({len(nuevos_caps)} caps)"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                success = download_manga_from_list(manga_id, nuevos_caps, browser, mode_debug=mode_debug, logger=logger)
            else:
                # Fallback: metodo tradicional
                msg = f"[WARN] Sin lista, usando metodo tradicional"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                
                if last_checked:
                    try:
                        start_cap = str(int(float(last_checked)) + 1)
                    except ValueError:
                        start_cap = current_chapter
                else:
                    start_cap = current_chapter
                
                msg = f"[INFO] Descargando desde capitulo {start_cap}"
                if mode_debug:
                    print(msg)
                if logger:
                    logger.log(msg)
                
                # IMPORTANTE: Cerrar browser compartido temporalmente
                browser.close()
                success = download_manga(manga_id, start_cap, mode_debug=mode_debug, logger=logger)
                # Reabrir para siguiente manga
                browser = p.chromium.launch(headless=True)
            
            if success:
                result['downloaded'] = True
                descargados += 1
            else:
                result['downloaded'] = False
        
        browser.close()
    
    return results, descargados, check_time
    

def show_summary(results, descargados, check_time, mode_debug=True, logger=None):
    """Mostrar resumen con info de descargas"""
    nuevos = [r for r in results if r.get('has_new', False)]
    
    separator = "=" * 60
    
    msg = "\n" + separator
    print(msg)
    if logger:
        logger.log(msg)
    
    msg = "RESUMEN CHECK + DOWNLOAD v2"
    print(msg)
    if logger:
        logger.log(msg)
    
    msg = separator
    print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"Total manga verificados: {len(results)}"
    print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"Tiempo chequeo: {check_time:.2f}s"
    print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"Manga con capitulos nuevos: {len(nuevos)}"
    print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"Manga descargados: {descargados}"
    print(msg)
    if logger:
        logger.log(msg)
    
    if nuevos:
        msg = "\nLista mangas con nuevos capitulos:"
        print(msg)
        if logger:
            logger.log(msg)
        
        for r in nuevos:
            current = r.get('current_chapter', 'N/A')
            new_count = r.get('new_chapters_count', 'N/A')
            downloaded_str = "[DESCARGADO]" if r.get('downloaded') else "[SOLO CHECK]"
            msg = f"  - {r['title']}: Cap. {current} (+{new_count}) {downloaded_str}"
            print(msg)
            if logger:
                logger.log(msg)
    
    # Regenerar index
    if nuevos:
        try:
            from server.server_utils import regenerar_seccion_seguimiento
            msg = "\nRegenerando index principal..."
            print(msg)
            if logger:
                logger.log(msg)
            
            regenerar_seccion_seguimiento()
            
            msg = "[OK] Index actualizado"
            print(msg)
            if logger:
                logger.log(msg)
        except Exception as e:
            msg = f"[WARN] No se pudo actualizar index: {e}"
            print(msg)
            if logger:
                logger.log(msg)
    
    msg = separator
    print(msg)
    if logger:
        logger.log(msg)

def main():
    log_path = create_log_path("check_and_download")
    
    try:
        with Logger(log_path, "check_and_download_worker.main") as logger:
            try:
                results, descargados, check_time = check_and_download(mode_debug=True, logger=logger)
                show_summary(results, descargados, check_time, mode_debug=True, logger=logger)
                
            except Exception as e:
                msg = f"\n[ERROR FATAL] {e}"
                print(msg)
                logger.log(msg)
                import traceback
                logger.log(traceback.format_exc())
                traceback.print_exc()
    except Exception as e:
        print(f"[ERROR FATAL] Error creando logger: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPresiona Enter para cerrar...")

if __name__ == "__main__":
    main()