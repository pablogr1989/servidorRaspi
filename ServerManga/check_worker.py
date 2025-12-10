#!/usr/bin/env python3
import sys
import os
import time
from server.server_utils import regenerar_seccion_seguimiento
from database.db_manager import DatabaseManager
import importlib.util

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from utils.logger import Logger, create_log_path

# Mapeo de page_types a clases checker
CHECKER_CLASSES = {
    'olympus_com': 'checkers.olympus_com_checker.OlympusComChecker',
    'olympus_net': 'checkers.olympus_net_checker.OlympusNetChecker',
    'tmo': 'checkers.tmo_checker.TmoChecker',
    'animeallstar' : 'checkers.animeallstar_checker.AnimeAllStarChecker',
}

def get_checker_class(page_type_name):
    """Importar clase checker dinamicamente"""
    if page_type_name not in CHECKER_CLASSES:
        raise Exception(f"Page type '{page_type_name}' no tiene checker configurado")
    
    module_path, class_name = CHECKER_CLASSES[page_type_name].rsplit('.', 1)
    module = __import__(module_path, fromlist=[class_name])
    return getattr(module, class_name)

def check_single_manga(manga_id, mode_debug=True, logger=None):
    """Chequear un solo manga por ID"""
    msg = " -- check_single_manga -- "
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    db = DatabaseManager()
    
    # Obtener manga
    manga = db.get_manga(manga_id)
    if not manga:
        msg = f"[ERROR] Manga ID {manga_id} no encontrado"
        print(msg)
        if logger:
            logger.log(msg)
        return None
    
    # Verificar tracking
    if manga.get('tracking') != 1:
        msg = f"[WARN] '{manga['title']}' no esta en seguimiento"
        print(msg)
        if logger:
            logger.log(msg)
        return None
    
    # Obtener page_type
    page_type = db.get_page_type_by_id(manga['page_type_id'])
    if not page_type:
        msg = f"[ERROR] Page type no encontrado"
        print(msg)
        if logger:
            logger.log(msg)
        return None
    
    try:
        msg = f"\nVerificando: {manga['title']}..."
        print(msg)
        if logger:
            logger.log(msg)
        
        start_time = time.time()
        
        # Cargar checker
        checker_class = get_checker_class(page_type['name'])
        result = checker_class.check_single(manga, mode_debug=mode_debug, logger=logger)
        
        if result['has_new']:
            with db.get_connection() as conn:
                conn.execute(
                    'UPDATE manga SET current_chapter = ? WHERE id = ?',
                    (result['current_chapter'], manga['id'])
                )
            msg = f"  [NUEVO] Ultimo capitulo: {result['current_chapter']}"
            print(msg)
            if logger:
                logger.log(msg)
            
            msg = f"  [INFO] Tienes {result['new_chapters_count']} capitulos sin descargar"
            print(msg)
            if logger:
                logger.log(msg)
        else:
            msg = f"  [OK] Sin capitulos nuevos"
            print(msg)
            if logger:
                logger.log(msg)
        
        check_time = time.time() - start_time
        results = []
        results.append(result)
        return results, check_time
        
    except Exception as e:
        msg = f"[ERROR] {e}"
        print(msg)
        if logger:
            logger.log(msg)
            import traceback
            logger.log(traceback.format_exc())
        import traceback
        traceback.print_exc()
        return None
        
    
def check_all_manga(page_mode=0, mode_debug=True, logger=None):
    """
    Page Mode = 0 -> Todos los tipos de paginas
    Page Mode = 1 -> Solo Olympus_Com
    Page Mode = 2 -> Solo Olympus_Net
    Page Mode = 3 -> Solo TMO
    Page Mode = 4 -> Todos menos Olympus_Com
    Page Mode = 5 -> Solo Anime All Star
    """
    db = DatabaseManager()
    all_manga = db.get_manga_by_tracking(1)    
    
    if not all_manga:
        msg = "\n[INFO] No hay manga en seguimiento"
        print(msg)
        if logger:
            logger.log(msg)
        return [], 0
    
    msg = f"\nIniciando verificacion de {len(all_manga)} manga..."
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    # Agrupar por page_type
    mangas_por_tipo = {}
    for manga in all_manga:
        page_type_id = manga['page_type_id']
        page_type_name = manga['page_type_name']
        
        if page_type_name not in mangas_por_tipo:
            mangas_por_tipo[page_type_name] = []
        mangas_por_tipo[page_type_name].append(manga)
    
    msg = f"[DEBUG] Grupos de page_type: {len(mangas_por_tipo)}"
    if mode_debug:
        print(msg)
    if logger:
        logger.log(msg)
    
    for pt_name, manga_list in mangas_por_tipo.items():
        msg = f"[DEBUG] {pt_name}: {len(manga_list)} mangas"
        if mode_debug:
            print(msg)
        if logger:
            logger.log(msg)
    
    results = []
    start_total = time.time()
    
    # Procesar por grupos con batch
    for page_type_name, manga_list in mangas_por_tipo.items():
        try:
            if page_mode == 1:
                if page_type_name == 'olympus_net' or page_type_name == 'tmo' or page_type_name == 'animeallstar':
                    continue
            elif page_mode == 2:
                if page_type_name == 'olympus_com' or page_type_name == 'tmo' or page_type_name == 'animeallstar':
                    continue
            elif page_mode == 3:
                if page_type_name == 'olympus_com' or page_type_name == 'olympus_net' or page_type_name == 'animeallstar':
                    continue
            elif page_mode == 4:
                if page_type_name == 'olympus_com':
                    continue
            elif page_mode == 5:
                if page_type_name == 'olympus_net' or page_type_name == 'tmo' or page_type_name == 'olympus_com':
                    continue
            
            checker_class = get_checker_class(page_type_name)
            
            msg = f"\n[BATCH] Chequeando {len(manga_list)} manga(s) de '{page_type_name}'..."
            if mode_debug:
                print(msg)
            if logger:
                logger.log(msg)
            
            batch_results = checker_class.check_batch(manga_list, mode_debug=mode_debug, logger=logger)
            
            # Actualizar DB y agregar a results
            for result in batch_results:
                if result['has_new']:
                    with db.get_connection() as conn:
                        conn.execute(
                            'UPDATE manga SET current_chapter = ? WHERE id = ?',
                            (result['current_chapter'], result['manga_id'])
                        )
                    msg = f"  [NUEVO] {result['title']}: Cap. {result['current_chapter']} (+{result['new_chapters_count']})"
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                else:
                    msg = f"  [OK] {result['title']}: Sin nuevos"
                    if mode_debug:
                        print(msg)
                    if logger:
                        logger.log(msg)
                
                results.append(result)
        
        except Exception as e:
            msg = f"[ERROR] Error procesando page_type '{page_type_name}': {e}"
            print(msg)
            if logger:
                logger.log(msg)
                import traceback
                logger.log(traceback.format_exc())
            import traceback
            traceback.print_exc()
            continue
    
    total_time = time.time() - start_total
    return results, total_time

def show_summary(results, total_time, mode_debug=True, logger=None):
    nuevos = [r for r in results if r.get('has_new', False)]
    
    separator = "=" * 50
    
    msg = "\n" + separator
    print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"Total manga verificados: {len(results)}"
    print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"Tiempo total: {total_time:.2f}s"
    print(msg)
    if logger:
        logger.log(msg)
    
    msg = f"Manga con capitulos nuevos: {len(nuevos)}"
    print(msg)
    if logger:
        logger.log(msg)
    
    if nuevos:
        msg = "\nNUEVOS CAPITULOS:"
        print(msg)
        if logger:
            logger.log(msg)
        
        for r in nuevos:
            msg = f"  - {r['title']}: Cap. {r['current_chapter']} (+{r['new_chapters_count']})"
            print(msg)
            if logger:
                logger.log(msg)
    
    # Regenerar seccion seguimiento si hubo cambios
    if nuevos:
        try:
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
    log_path = create_log_path("check_worker")
    
    try:
        with Logger(log_path, "check_worker.main") as logger:
            msg = f"\n{'='*60}"
            print(msg)
            logger.log(msg)
            
            msg = "MANGA CHECKER WORKER"
            print(msg)
            logger.log(msg)
            
            msg = f"{'='*60}"
            print(msg)
            logger.log(msg)
            
            try:
                # Si recibe argumento, chequear solo ese manga
                if len(sys.argv) > 1:
                    manga_id = int(sys.argv[1])
                    result = check_single_manga(manga_id, mode_debug=True, logger=logger)
                    if result:
                        msg = f"\nVerificacion completada"
                        print(msg)
                        logger.log(msg)
                else:
                    # Sin argumentos, chequear todos
                    results, total_time = check_all_manga(mode_debug=True, logger=logger)
                    show_summary(results, total_time, mode_debug=True, logger=logger)
            except Exception as e:
                msg = f"[ERROR FATAL] {e}"
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