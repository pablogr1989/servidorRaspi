#!/usr/bin/env python3
"""
Script para descargar covers de todos los mangas olympus_com
y regenerar index.html principal
"""

import sys
import os

# Path resolution
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from database.db_manager import DatabaseManager
from checkers.olympus_com_api_client import OlympusComAPIClient
from server.server_utils import generar_index_principal
import requests

def descargar_todos_covers():
    """Descargar covers de todos los mangas olympus_com"""
    db = DatabaseManager()
    api = OlympusComAPIClient()
    
    # Obtener page_type olympus_com
    page_type = db.get_page_type('olympus_com')
    if not page_type:
        print("[ERROR] page_type 'olympus_com' no encontrado")
        return
    
    # Obtener todos los mangas de este tipo
    all_manga = db.get_manga_by_page_type(page_type['id'])
    
    if not all_manga:
        print("[INFO] No hay mangas olympus_com en la base de datos")
        return
    
    print(f"\n{'='*60}")
    print(f"DESCARGA MASIVA DE COVERS - {len(all_manga)} mangas")
    print(f"{'='*60}\n")
    
    # Preparar info
    manga_info_list = [{
        'id': m['id'],
        'title': m['title'],
        'olympus_index_url': m.get('olympus_index_url')
    } for m in all_manga]
    
    # Buscar todos con optimizacion
    print("[INFO] Buscando series en API...")
    resultados_busqueda = api.buscar_multiples_series(manga_info_list)
    
    descargados = 0
    ya_existian = 0
    errores = 0
    
    for manga in all_manga:
        mid = manga['id']
        print(f"\nProcesando: {manga['title']}")
        
        if mid not in resultados_busqueda:
            print(f"  [ERROR] No encontrado en API")
            errores += 1
            continue
        
        serie = resultados_busqueda[mid]['serie']
        cover_url = serie.get('cover')
        
        if not cover_url:
            print(f"  [WARN] No hay cover URL")
            errores += 1
            continue
        
        # Crear directorio manga si no existe
        manga_dir = manga['local_storage_path']
        os.makedirs(manga_dir, exist_ok=True)
        
        cover_path = os.path.join(manga_dir, 'portada.webp')
        
        # Si ya existe, skip
        if os.path.exists(cover_path):
            print(f"  [INFO] Cover ya existe")
            ya_existian += 1
            continue
        
        # Descargar
        try:
            print(f"  [INFO] Descargando...")
            response = requests.get(cover_url, timeout=15)
            response.raise_for_status()
            
            with open(cover_path, 'wb') as f:
                f.write(response.content)
            
            print(f"  [OK] Descargado: {cover_path}")
            descargados += 1
            
        except Exception as e:
            print(f"  [ERROR] Descarga fallo: {e}")
            errores += 1
    
    print(f"\n{'='*60}")
    print(f"RESUMEN:")
    print(f"  - Descargados: {descargados}")
    print(f"  - Ya existian: {ya_existian}")
    print(f"  - Errores: {errores}")
    print(f"  - Total: {len(all_manga)}")
    print(f"{'='*60}\n")
    
    return descargados > 0 or ya_existian > 0

def main():
    print(f"\n{'='*60}")
    print("DESCARGA COVERS + REGENERACION INDEX")
    print(f"{'='*60}")
    
    try:
        # # Descargar covers
        # exito = descargar_todos_covers()
        
        # if not exito:
        #     print("\n[WARN] No se descargaron covers, pero regenerando index de todas formas...")
        
        # Regenerar index principal
        print("\n[INFO] Regenerando index.html principal...")
        index_html = generar_index_principal()
        
        index_path = os.path.join(base_dir, 'index.html')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        print(f"[OK] Index regenerado: {index_path}")
        
        print(f"\n{'='*60}")
        print("PROCESO COMPLETADO")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n[ERROR FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    input("\nPresiona Enter para cerrar...")

if __name__ == "__main__":
    main()