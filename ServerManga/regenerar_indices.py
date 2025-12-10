#!/usr/bin/env python3
"""
Script para regenerar index.html de todos los mangas con nuevo template
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager

def regenerar_index(manga):
    """Regenerar index.html para un manga"""
    template_path = os.path.join(BASE_DIR, 'templates', 'manga_index.html')
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    html = template.replace('{{MANGA_ID}}', str(manga['id']))
    html = html.replace('{{MANGA_TITLE}}', manga['title'])
    
    local_path = manga['local_storage_path']
    index_path = os.path.join(local_path, 'index.html')
    
    # Verificar que existe la carpeta
    if not os.path.exists(local_path):
        print(f"[WARN] Carpeta no existe: {local_path}")
        return False
    
    # Backup del index viejo si existe
    if os.path.exists(index_path):
        backup_path = os.path.join(local_path, 'index_OLD.html')
        os.rename(index_path, backup_path)
        print(f"[INFO] Backup: index_OLD.html")
    
    # Crear nuevo index
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"[OK] Regenerado: {index_path}")
    return True

def main():
    db = DatabaseManager()
    
    # Obtener todos los mangas
    all_manga = db.get_all_manga()
    
    if not all_manga:
        print("[INFO] No hay mangas en la base de datos")
        return
    
    print(f"\n{'='*60}")
    print(f"REGENERACION MASIVA DE INDEX.HTML")
    print(f"{'='*60}")
    print(f"Total mangas: {len(all_manga)}\n")
    
    confirmacion = input("Continuar? (s/n): ").lower()
    
    if confirmacion != 's':
        print("[INFO] Operacion cancelada")
        return
    
    exitosos = 0
    fallidos = 0
    
    for manga in all_manga:
        print(f"\nProcesando: {manga['title']}")
        
        if regenerar_index(manga):
            exitosos += 1
        else:
            fallidos += 1
    
    print(f"\n{'='*60}")
    print(f"RESUMEN:")
    print(f"  - Exitosos: {exitosos}/{len(all_manga)}")
    print(f"  - Fallidos: {fallidos}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()