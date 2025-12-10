#!/usr/bin/env python3
import os
import shutil
import sys
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager

# Configuracion
MANGA_DIR = "/home/pablopi/Server/ServerManga/mangas/against-the-gods"
MANGA_TITLE = "Against The Gods"
CHECK_URL = "https://olympusbiblioteca.net/manga/against-the-gods/"
FIRST_CHAPTER = 100
LAST_CHAPTER = 710
CURRENT_READING = 513

def crear_estructura():
    """Crear carpeta contenido"""
    contenido_dir = os.path.join(MANGA_DIR, 'contenido')
    os.makedirs(contenido_dir, exist_ok=True)
    print(f"[OK] Carpeta contenido creada: {contenido_dir}")
    return contenido_dir

def mover_y_renombrar_carpetas(contenido_dir):
    """Mover raw_Capitulo X a contenido/raw_Capitulo_X"""
    print("\n[INFO] Moviendo carpetas raw...")
    
    movidas = 0
    errores = 0
    
    for num in range(FIRST_CHAPTER, LAST_CHAPTER + 1):
        old_name = f"raw_Capitulo {num}"
        new_name = f"raw_Capitulo_{num}"
        
        old_path = os.path.join(MANGA_DIR, old_name)
        new_path = os.path.join(contenido_dir, new_name)
        
        if os.path.exists(old_path):
            try:
                shutil.move(old_path, new_path)
                movidas += 1
                if movidas % 50 == 0:
                    print(f"  Progreso: {movidas}/{LAST_CHAPTER - FIRST_CHAPTER + 1}")
            except Exception as e:
                print(f"  [ERROR] {old_name}: {e}")
                errores += 1
    
    print(f"[OK] Carpetas movidas: {movidas}")
    if errores > 0:
        print(f"[WARN] Errores: {errores}")

def listar_imagenes(raw_dir):
    """Obtener lista de imagenes en raw_Capitulo_X ordenadas"""
    if not os.path.exists(raw_dir):
        return []
    
    imagenes = []
    for file in sorted(os.listdir(raw_dir)):
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            imagenes.append(file)
    
    return imagenes

def generar_html_capitulo(contenido_dir, chapter_num, manga_id):
    """Generar capitulo_X.html usando template"""
    # Leer template
    template_path = os.path.join(BASE_DIR, 'templates', 'capitulo_template.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Obtener imagenes
    raw_dir = os.path.join(contenido_dir, f'raw_Capitulo_{chapter_num}')
    imagenes = listar_imagenes(raw_dir)
    
    if not imagenes:
        print(f"  [WARN] Cap. {chapter_num}: No se encontraron imagenes")
        return False
    
    # Generar HTML de imagenes
    images_html = ''
    for img in imagenes:
        images_html += f'        <img src="raw_Capitulo_{chapter_num}/{img}" alt="Pagina" loading="lazy">\n'
    
    # Navegacion
    prev_chapter = f'capitulo_{chapter_num - 1}.html' if chapter_num > FIRST_CHAPTER else None
    next_chapter = f'capitulo_{chapter_num + 1}.html' if chapter_num < LAST_CHAPTER else None
    
    # Reemplazar placeholders
    html = template.replace('{{MANGA_TITLE}}', MANGA_TITLE)
    html = html.replace('{{CHAPTER_NUM}}', str(chapter_num))
    html = html.replace('{{MANGA_ID}}', str(manga_id))
    html = html.replace('{{IMAGES}}', images_html)
    html = html.replace('{{PREV_CHAPTER}}', prev_chapter if prev_chapter else '#')
    html = html.replace('{{NEXT_CHAPTER}}', next_chapter if next_chapter else '#')
    html = html.replace('{{PREV_DISABLED}}', '' if prev_chapter else 'disabled')
    html = html.replace('{{NEXT_DISABLED}}', '' if next_chapter else 'disabled')
    
    # Guardar
    filepath = os.path.join(contenido_dir, f'capitulo_{chapter_num}.html')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return True

def generar_todos_htmls(contenido_dir, manga_id):
    """Generar todos los HTMLs de capitulos"""
    print("\n[INFO] Generando HTMLs de capitulos...")
    
    generados = 0
    errores = 0
    
    for num in range(FIRST_CHAPTER, LAST_CHAPTER + 1):
        try:
            if generar_html_capitulo(contenido_dir, num, manga_id):
                generados += 1
                if generados % 50 == 0:
                    print(f"  Progreso: {generados}/{LAST_CHAPTER - FIRST_CHAPTER + 1}")
        except Exception as e:
            print(f"  [ERROR] Cap. {num}: {e}")
            errores += 1
    
    print(f"[OK] HTMLs generados: {generados}")
    if errores > 0:
        print(f"[WARN] Errores: {errores}")

def crear_index_manga(manga_id):
    """Crear index.html del manga"""
    template_path = os.path.join(BASE_DIR, 'templates', 'manga_index.html')
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    html = template.replace('{{MANGA_ID}}', str(manga_id))
    html = html.replace('{{MANGA_TITLE}}', MANGA_TITLE)
    
    filepath = os.path.join(MANGA_DIR, 'index.html')
    
    # Backup del index viejo
    if os.path.exists(filepath):
        backup_path = os.path.join(MANGA_DIR, 'index_OLD.html')
        shutil.move(filepath, backup_path)
        print(f"[INFO] Index viejo respaldado como index_OLD.html")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"[OK] Index manga creado: {filepath}")

def insertar_en_db():
    """Insertar manga en base de datos"""
    db = DatabaseManager()
    
    # Verificar si ya existe
    all_manga = db.get_all_manga()
    for m in all_manga:
        if m['title'].lower() == MANGA_TITLE.lower():
            print(f"[WARN] Manga ya existe en DB con ID: {m['id']}")
            usar = input("Usar ID existente? (s/n): ").lower()
            if usar == 's':
                return m['id']
            else:
                print("[INFO] Abortando...")
                sys.exit(0)
    
    # Obtener page_type olympus_com
    page_types = db.get_all_page_types()
    olympus_com_id = None
    
    for pt in page_types:
        if 'olympus' in pt['name'].lower() and 'com' in pt['name'].lower():
            olympus_com_id = pt['id']
            break
    
    if not olympus_com_id:
        print("[ERROR] No se encontro page_type olympus_com")
        print("Page types disponibles:")
        for pt in page_types:
            print(f"  {pt['id']}: {pt['name']}")
        sys.exit(1)
    
    print(f"\n[INFO] Insertando manga en DB...")
    print(f"  Titulo: {MANGA_TITLE}")
    print(f"  Check URL: {CHECK_URL}")
    print(f"  Page Type ID: {olympus_com_id}")
    print(f"  Last Checked: {LAST_CHAPTER}")
    print(f"  Current Reading: {CURRENT_READING}")
    print(f"  Tracking: 0 (desactivado)")
    
    manga_id = db.add_manga(
        title=MANGA_TITLE,
        check_url=CHECK_URL,
        page_type_id=olympus_com_id,
        local_storage_path=MANGA_DIR,
        last_checked_chapter=str(LAST_CHAPTER),
        current_chapter=str(LAST_CHAPTER),
        current_reading=str(CURRENT_READING),
        tracking=0
    )
    
    print(f"[OK] Manga insertado con ID: {manga_id}")
    return manga_id

def limpiar_archivos_viejos():
    """Eliminar archivos del sistema viejo"""
    print("\n[INFO] Limpiando archivos viejos...")
    
    archivos_eliminar = ['servidor.py', 'ultimo_capitulo.txt']
    
    for archivo in archivos_eliminar:
        filepath = os.path.join(MANGA_DIR, archivo)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"  [OK] Eliminado: {archivo}")
    
    # Eliminar HTMLs viejos en raiz
    eliminados = 0
    for num in range(FIRST_CHAPTER, LAST_CHAPTER + 1):
        old_html = os.path.join(MANGA_DIR, f'capitulo{num}.html')
        if os.path.exists(old_html):
            os.remove(old_html)
            eliminados += 1
    
    if eliminados > 0:
        print(f"  [OK] Eliminados {eliminados} HTMLs viejos")

def main():
    print("="*60)
    print("MIGRACION: AGAINST THE GODS")
    print("="*60)
    print(f"\nDirectorio: {MANGA_DIR}")
    print(f"Capitulos: {FIRST_CHAPTER} - {LAST_CHAPTER}")
    print(f"Total: {LAST_CHAPTER - FIRST_CHAPTER + 1} capitulos")
    
    confirmar = input("\nEsta operacion modificara archivos. Continuar? (s/n): ").lower()
    if confirmar != 's':
        print("[INFO] Operacion cancelada")
        return
    
    try:
        # 1. Insertar en DB (primero para obtener manga_id)
        manga_id = insertar_en_db()
        
        # 2. Crear estructura
        contenido_dir = crear_estructura()
        
        # 3. Mover carpetas raw
        mover_y_renombrar_carpetas(contenido_dir)
        
        # 4. Generar HTMLs
        generar_todos_htmls(contenido_dir, manga_id)
        
        # 5. Crear index manga
        crear_index_manga(manga_id)
        
        # 6. Limpiar archivos viejos
        limpiar_archivos_viejos()
        
        # 7. Regenerar index principal
        print("\n[INFO] Regenerando index principal...")
        from server.server_utils import regenerar_seccion_mangas
        regenerar_seccion_mangas()
        print("[OK] Index principal actualizado")
        
        print("\n" + "="*60)
        print("MIGRACION COMPLETADA EXITOSAMENTE")
        print("="*60)
        print(f"\nManga ID: {manga_id}")
        print(f"Index manga: {MANGA_DIR}/index.html")
        print(f"Capitulos: {MANGA_DIR}/contenido/capitulo_XXX.html")
        
    except Exception as e:
        print(f"\n[ERROR FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()