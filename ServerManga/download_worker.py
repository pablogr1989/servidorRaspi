#!/usr/bin/env python3
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager
from playwright.sync_api import sync_playwright
from utils.logger import Logger, create_log_path

# Mapeo de page_types a clases downloader
DOWNLOADER_CLASSES = {
    'olympus_com': 'downloaders.olympus_com_downloader.OlympusComDownloader',
    'olympus_net': 'downloaders.olympus_net_downloader.OlympusNetDownloader',
    'tmo': 'downloaders.tmo_downloader.TmoDownloader',
    'animeallstar' : 'downloaders.animeallstar_downloader.AnimeAllStarDownloader',
}

def get_downloader_class(page_type_name):
    """Importar clase downloader dinamicamente"""
    if page_type_name not in DOWNLOADER_CLASSES:
        raise Exception(f"Page type '{page_type_name}' no tiene downloader configurado")
    
    module_path, class_name = DOWNLOADER_CLASSES[page_type_name].rsplit('.', 1)
    module = __import__(module_path, fromlist=[class_name])
    return getattr(module, class_name)

def download_manga_from_list(manga_id, capitulos_lista, browser, mode_debug=False, logger=None):
    """Descargar manga desde lista de capitulos (optimizado)"""
    db = DatabaseManager()
    
    # Obtener manga
    manga = db.get_manga(manga_id)
    if not manga:
        msg = f"[ERROR] Manga ID {manga_id} no encontrado"
        print(msg)
        if logger:
            logger.log(msg)
        return False
    
    # Obtener page_type
    page_type = db.get_page_type_by_id(manga['page_type_id'])
    if not page_type:
        msg = f"[ERROR] Page type no encontrado"
        print(msg)
        if logger:
            logger.log(msg)
        return False
    
    page_type_name = page_type['name']
    
    # Verificar si tiene downloader
    if page_type_name not in DOWNLOADER_CLASSES:
        msg = f"[ERROR] No hay downloader para '{page_type_name}'"
        print(msg)
        if logger:
            logger.log(msg)
        return False
    
    msg = f"\n{'='*60}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"DESCARGA OPTIMIZADA (con lista)"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"{'='*60}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"Manga: {manga['title']}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"Capitulos: {len(capitulos_lista)}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"{'='*60}\n"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    try:
        # Cargar downloader y ejecutar
        downloader_class = get_downloader_class(page_type_name)
        ultimo_descargado = downloader_class.download_chapters_list(manga, capitulos_lista, browser, mode_debug=mode_debug, logger=logger)
        
        if ultimo_descargado:
            # Actualizar SOLO last_checked_chapter (NO current_chapter)
            msg = "\nActualizando base de datos..."
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            with db.get_connection() as conn:
                conn.execute(
                    'UPDATE manga SET last_checked_chapter = ? WHERE id = ?',
                    (ultimo_descargado, manga_id)
                )
            
            msg = f"[OK] last_checked_chapter actualizado a: {ultimo_descargado}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
        
        msg = f"\n{'='*60}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = "DESCARGA COMPLETADA"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"{'='*60}\n"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        # Regenerar index
        try:
            from server.server_utils import regenerar_seccion_seguimiento, regenerar_seccion_mangas
            msg = "\nRegenerando index principal..."
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            regenerar_seccion_seguimiento()
            regenerar_seccion_mangas()
            
            msg = "[OK] Index actualizado"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
        except Exception as e:
            msg = f"[WARN] No se pudo actualizar index: {e}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
        
        return True
        
    except Exception as e:
        msg = f"\n[ERROR FATAL] {e}"
        print(msg)
        if logger:
            logger.log(msg)
            import traceback
            logger.log(traceback.format_exc())
        import traceback
        traceback.print_exc()
        return False

def download_manga(manga_id, start_chapter, mode_debug=False, logger=None):
    """Descargar manga por ID"""
    db = DatabaseManager()
    
    # Obtener manga
    manga = db.get_manga(manga_id)
    if not manga:
        msg = f"[ERROR] Manga ID {manga_id} no encontrado"
        print(msg)
        if logger:
            logger.log(msg)
        return False
    
    # Obtener page_type
    page_type = db.get_page_type_by_id(manga['page_type_id'])
    if not page_type:
        msg = f"[ERROR] Page type no encontrado"
        print(msg)
        if logger:
            logger.log(msg)
        return False
    
    page_type_name = page_type['name']
    
    # Verificar si tiene downloader
    if page_type_name not in DOWNLOADER_CLASSES:
        msg = f"[ERROR] No hay downloader para '{page_type_name}'"
        print(msg)
        if logger:
            logger.log(msg)
        return False
    
    msg = f"\n{'='*60}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"MANGA DOWNLOADER WORKER"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"{'='*60}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"Manga: {manga['title']}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"Tipo: {page_type_name}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"Capitulo inicial: {start_chapter}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"{'='*60}\n"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # Cargar downloader y ejecutar
            downloader_class = get_downloader_class(page_type_name)
            ultimo_descargado = downloader_class.download_full_manga(manga, start_chapter, browser, mode_debug=mode_debug, logger=logger)
            
            browser.close()
        
        if ultimo_descargado:
            # Actualizar DB
            msg = "\nActualizando base de datos..."
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            with db.get_connection() as conn:
                conn.execute(
                    '''UPDATE manga 
                       SET last_checked_chapter = ?, current_chapter = ? 
                       WHERE id = ?''',
                    (ultimo_descargado, ultimo_descargado, manga_id)
                )
            
            msg = f"[OK] last_checked_chapter: {ultimo_descargado}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            msg = f"[OK] current_chapter: {ultimo_descargado}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
        
        msg = f"\n{'='*60}"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = "DESCARGA COMPLETADA"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        msg = f"{'='*60}\n"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
        
        # Regenerar index
        try:
            from server.server_utils import regenerar_seccion_seguimiento, regenerar_seccion_mangas
            msg = "\nRegenerando index principal..."
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            regenerar_seccion_seguimiento()
            regenerar_seccion_mangas()
            
            msg = "[OK] Index actualizado"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
        except Exception as e:
            msg = f"[WARN] No se pudo actualizar index: {e}"
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
        
        return True
        
    except Exception as e:
        msg = f"\n[ERROR FATAL] {e}"
        print(msg)
        if logger:
            logger.log(msg)
            import traceback
            logger.log(traceback.format_exc())
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 3:
        print("Uso: python3 download_worker.py <manga_id> <start_chapter>")
        input("\nPresiona Enter para cerrar...")
        sys.exit(1)
    
    log_path = create_log_path("download_worker")
    
    try:
        with Logger(log_path, "download_worker.main") as logger:
            try:
                manga_id = int(sys.argv[1])
                start_chapter = sys.argv[2]
                
                success = download_manga(manga_id, start_chapter, mode_debug=True, logger=logger)
                
                if not success:
                    sys.exit(1)
                    
            except Exception as e:
                msg = f"\n[ERROR] {e}"
                print(msg)
                logger.log(msg)
                import traceback
                logger.log(traceback.format_exc())
                traceback.print_exc()
                sys.exit(1)
    except Exception as e:
        print(f"[ERROR FATAL] Error creando logger: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        input("\nPresiona Enter para cerrar...")

if __name__ == "__main__":
    main()