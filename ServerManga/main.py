#!/usr/bin/env python3
import os
import sys
import importlib.util
import time
import subprocess
import shutil
import subprocess

from playwright.sync_api import sync_playwright
from server.server_utils import regenerar_seccion_mangas
from checkers.olympus_com_checker import OlympusComChecker

# Path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager

db = DatabaseManager()

# ============================================================================
# MENU PRINCIPAL
# ============================================================================

def menu_principal():
    """Menu principal del sistema"""
    while True:
        print("\n" + "="*50)
        print("MANGA TRACKER - MENU PRINCIPAL (TU PUTA MADRE)")
        print("="*50)
        print("1. Lanzar servidor")
        print("2. Gestionar mangas")
        print("3. Gestionar seguimiento")
        print("0. Salir")
        
        opcion = input("\nOpcion: ").strip()
        
        if opcion == "1":
            lanzar_servidor()
        elif opcion == "2":
            menu_gestionar_mangas()
        elif opcion == "3":
            menu_gestionar_seguimiento()
        elif opcion == "0":
            print("\nSaliendo...")
            break
        else:
            print("[ERROR] Opcion invalida")

# ============================================================================
# LANZAR SERVIDOR
# ============================================================================
def lanzar_servidor():
    """
    Genera index principal y lanza servidor + cloudflare
    """
    print("\n=== LANZANDO SERVIDOR ===\n")
    
    # Generar index.html principal
    print("Generando index.html principal...")
    from server.server_utils import generar_index_principal
    
    try:
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(generar_index_principal())
        print("[OK] Index principal generado\n")
    except Exception as e:
        print(f"[ERROR] No se pudo generar index: {e}")
        return
    
    # Lanzar servidor en ventana independiente
    print("Iniciando servidor + cloudflare en ventana nueva v2...")
    try:
        subprocess.Popen([
            'x-terminal-emulator', '-e',
            'bash', '-c', 'cd /home/pablopi/Server/ServerManga && bash server/iniciarServidor.sh'
        ])
        
        print("[OK] Servidor lanzado")
        print("Revisa la ventana nueva para ver la URL de Cloudflare\n")
    except Exception as e:
        print(f"[ERROR] No se pudo lanzar servidor: {e}")
        print("Intenta ejecutar manualmente: bash server/iniciarServidor.sh\n")

# ============================================================================
# GESTIONAR MANGAS
# ============================================================================

def menu_gestionar_mangas():
    """Menu gestion de mangas"""
    while True:
        print("\n" + "-"*50)
        print("GESTIONAR MANGAS")
        print("-"*50)
        print("1. Crear manga")
        print("2. Editar manga")
        print("3. Listar mangas")
        print("4. Descargar manga")
        print("5. Actualizar OlympusCom info")
        print("6. Eliminar manga")           
        print("7. Ver informacion manga")    
        print("0. Volver")
        
        opcion = input("\nOpcion: ").strip()
        
        if opcion == "1":
            crear_manga()
        elif opcion == "2":
            editar_manga_sin_tracking()
        elif opcion == "3":
            listar_todos_mangas()
        elif opcion == "4":
            descargar_manga()
        elif opcion == "5":
            actualizar_olympusCom_info()
        elif opcion == "6":                  
            eliminar_manga()
        elif opcion == "7":                
            ver_info_manga()
        elif opcion == "0":
            break
        else:
            print("[ERROR] Opcion invalida")

def crear_manga():
    """Crear nuevo manga (tracking=0)"""
    print("\n--- CREAR MANGA ---")
    
    title = input("Titulo: ").strip()
    if not title:
        print("[ERROR] Titulo requerido")
        return
    
    check_url = input("Check URL: ").strip()
    if not check_url:
        print("[ERROR] URL requerida")
        return
    
    # Seleccionar page_type
    page_types = db.get_all_page_types()
    if not page_types:
        print("[ERROR] No hay tipos de pagina configurados")
        return
    
    print("\nTipos de pagina:")
    for i, pt in enumerate(page_types, 1):
        print(f"  {i}. {pt['name']}")
    
    try:
        pt_choice = int(input("Selecciona numero: ")) - 1
        page_type_id = page_types[pt_choice]['id']
    except (ValueError, IndexError):
        print("[ERROR] Seleccion invalida")
        return
    
    post_id = 0
    if page_type_id == 2:
        post_id = input("Introduce el post_id de Olympus Net: ").strip()
        if not post_id:
            print("[ERROR] Post id requerido")
            return
    
    # Local storage path
    default_path = f"/home/pablopi/Server/ServerManga/mangas/{title.replace(' ', '-').lower()}"
    local_path = input(f"Local storage [{default_path}]: ").strip()
    if not local_path:
        local_path = default_path
    
    # Crear manga en DB (tracking=0)
    manga_id = db.add_manga(
        title=title,
        check_url=check_url,
        page_type_id=page_type_id,
        local_storage_path=local_path,
        tracking=0,
        olympus_net_post_id = post_id
    )
    
    # Crear carpeta
    os.makedirs(local_path, exist_ok=True)
    
    # Crear index.html vacio
    template_path = os.path.join(BASE_DIR, 'templates', 'manga_index_empty.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    html = template.replace('{{MANGA_TITLE}}', title)
    
    index_path = os.path.join(local_path, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n[OK] Manga creado (ID: {manga_id})")
    print(f"[OK] Carpeta: {local_path}")
    print(f"[OK] Index creado")
    
    # Regenerar seccion mangas del index principal
    try:
        regenerar_seccion_mangas()
    except:
        pass  # Index principal aun no existe, se generara al lanzar servidor

def editar_manga_sin_tracking():
    """Editar manga (sin opciones de tracking)"""
    print("\n--- EDITAR MANGA ---")
    
    all_manga = db.get_all_manga()
    if not all_manga:
        print("[INFO] No hay mangas")
        return
    
    print("\nMangas disponibles:")
    for i, m in enumerate(all_manga, 1):
        tracking_status = "Si" if m['tracking'] == 1 else "No"
        print(f"  {i}. {m['title']} (Tracking: {tracking_status})")
    
    try:
        choice = int(input("\nSelecciona manga (0 cancelar): "))
        if choice == 0:
            return
        manga = all_manga[choice - 1]
    except (ValueError, IndexError):
        print("[ERROR] Seleccion invalida")
        return
    
    while True:
        print(f"\n--- EDITANDO: {manga['title']} ---")
        print(f"1. Titulo: {manga['title']}")
        print(f"2. Check URL: {manga['check_url']}")
        print(f"3. Tipo pagina: {manga['page_type_name']}")
        print(f"4. Post ID: (Solo OlympusNet) {manga['olympus_net_post_id']}")
        print(f"5. Local storage: {manga['local_storage_path']}")
        print(f"6. Current reading chapter: {manga['current_reading']}")
        print("0. Volver")
        
        edit_choice = input("\nCampo a editar: ").strip()
        
        if edit_choice == "0":
            break
        elif edit_choice == "1":
            new_value = input("Nuevo titulo: ").strip()
            if new_value:
                with db.get_connection() as conn:
                    conn.execute('UPDATE manga SET title = ? WHERE id = ?', 
                               (new_value, manga['id']))
                manga['title'] = new_value
                print("[OK] Actualizado")
        
        elif edit_choice == "2":
            new_value = input("Nueva URL: ").strip()
            if new_value:
                with db.get_connection() as conn:
                    conn.execute('UPDATE manga SET check_url = ? WHERE id = ?', 
                               (new_value, manga['id']))
                manga['check_url'] = new_value
                print("[OK] Actualizado")
        
        elif edit_choice == "3":
            page_types = db.get_all_page_types()
            print("\nTipos disponibles:")
            for i, pt in enumerate(page_types, 1):
                print(f"  {i}. {pt['name']}")
            
            try:
                pt_choice = int(input("Selecciona: ")) - 1
                new_pt_id = page_types[pt_choice]['id']
                
                with db.get_connection() as conn:
                    conn.execute('UPDATE manga SET page_type_id = ? WHERE id = ?', 
                               (new_pt_id, manga['id']))
                manga['page_type_id'] = new_pt_id
                manga['page_type_name'] = page_types[pt_choice]['name']
                print("[OK] Actualizado")
            except (ValueError, IndexError):
                print("[ERROR] Seleccion invalida")
        
        elif edit_choice == "4":
            new_value = input("New OlympusNet post id: ").strip()
            if new_value:
                with db.get_connection() as conn:
                    conn.execute(f'UPDATE manga SET olympus_net_post_id = ? WHERE id = ?',
                               (new_value, manga['id']))
                manga['olympus_net_post_id'] = new_value
                print("[OK] Actualizado")    
        
        elif edit_choice == "5":
            new_value = input("Nuevo local storage: ").strip()
            if new_value:
                if not os.path.exists(new_value):
                    crear = input(f"Crear '{new_value}'? (s/n): ").lower()
                    if crear == 's':
                        os.makedirs(new_value, exist_ok=True)
                    else:
                        continue
                
                with db.get_connection() as conn:
                    conn.execute('UPDATE manga SET local_storage_path = ? WHERE id = ?', 
                               (new_value, manga['id']))
                manga['local_storage_path'] = new_value
                print("[OK] Actualizado")
        
        elif edit_choice == "6":
            new_value = input("New current reading: ").strip()
            if new_value:
                with db.get_connection() as conn:
                    conn.execute(f'UPDATE manga SET current_reading = ? WHERE id = ?',
                               (new_value, manga['id']))
                manga['current_reading'] = new_value
                print("[OK] Actualizado")       
        else:
            print("[ERROR] Opcion invalida")

def listar_todos_mangas():
    """Listar todos los mangas"""
    print("\n--- LISTA DE MANGAS ---")
    
    all_manga = db.get_all_manga()
    if not all_manga:
        print("[INFO] No hay mangas")
        return
    
    print(f"\nTotal: {len(all_manga)} mangas\n")
    for m in all_manga:
        tracking_status = "Si" if m['tracking'] == 1 else "No"
        print(f"ID: {m['id']}")
        print(f"  Titulo: {m['title']}")
        print(f"  Tracking: {tracking_status}")
        print(f"  Tipo: {m['page_type_name']}")
        p_id = m['page_type_id']
        print(f"  URL: {m['check_url']}")
        if p_id == 1: print(f"  Slug: {m['slug']}")
        if p_id == 2: print(f'  Post ID: {m['olympus_net_post_id']}')
        print(f"  Path: {m['local_storage_path']}")
        print(f"  Current reading: {m['current_reading']}")
        print(f"  Total chapters: {m['current_chapter']}")
        print()
    
    input("Presiona Enter para continuar...")

def descargar_manga():
    """Descargar manga en ventana independiente"""
    print("\n--- DESCARGAR MANGA ---")
    
    all_manga = db.get_all_manga()
    if not all_manga:
        print("[INFO] No hay mangas")
        return
    
    print("\nMangas disponibles:")
    for i, m in enumerate(all_manga, 1):
        print(f"  {i}. {m['title']}")
    
    try:
        choice = int(input("\nSelecciona manga (0 cancelar): "))
        if choice == 0:
            return
        manga = all_manga[choice - 1]
    except (ValueError, IndexError):
        print("[ERROR] Seleccion invalida")
        return
    
    last_url = manga.get('last_download_url')
    start_chapter = None
    
    if last_url:
        print(f"\n[INFO] Ultima descarga {manga.get('current_chapter')}: {last_url}\n")
        opcion = input("Continuar desde ultima descarga? (s/n): ").lower()
        
        if opcion == 's':
            print("[INFO] Continuando desde ultima descarga...")
            start_chapter = "RESUME"  # Flag especial
        else:
            print(f'[INFO] El ultimo capitulo leido es: {manga.get('current_reading')}')
            print(f'[INFO] El ultimo chequeado es: {manga.get('last_checked_chapter')}')
            start_chapter = input("Capitulo inicial: ").strip()
    else:
        print(f'[INFO] El ultimo capitulo leido es: {manga.get('current_reading')}')
        print(f'[INFO] El ultimo chequeado es: {manga.get('last_checked_chapter')}')
        start_chapter = input("Capitulo inicial: ").strip()
    
    if not start_chapter:
        print("[ERROR] Capitulo requerido")
        return
    
    print(f"\n[INFO] Lanzando descarga de '{manga['title']}'...")
    
    try:
        subprocess.Popen([
            'x-terminal-emulator', '-e',
            'python3', 'download_worker.py', str(manga['id']), start_chapter
        ])
        print("[OK] Descarga iniciada en nueva ventana")
    except Exception as e:
        print(f"[ERROR] {e}")
    
    input("\nPresiona Enter para continuar...")
    
def actualizar_olympusCom_info():
    OlympusComChecker.actualizar_todos_slugs()
    
    
def eliminar_manga():
    """Eliminar manga completamente (DB + carpeta)"""
    print("\n--- ELIMINAR MANGA ---")
    
    all_manga = db.get_all_manga()
    if not all_manga:
        print("[INFO] No hay mangas")
        return
    
    print("\nMangas disponibles:")
    for i, m in enumerate(all_manga, 1):
        tracking_status = "Si" if m['tracking'] == 1 else "No"
        print(f"  {i}. {m['title']} (Tracking: {tracking_status})")
    
    try:
        choice = int(input("\nSelecciona manga (0 cancelar): "))
        if choice == 0:
            return
        manga = all_manga[choice - 1]
    except (ValueError, IndexError):
        print("[ERROR] Seleccion invalida")
        return
    
    # Confirmacion
    print(f"\n[WARN] Vas a eliminar: {manga['title']}")
    print(f"[WARN] Se borrara:")
    print(f"  - Entrada en base de datos")
    print(f"  - Carpeta: {manga['local_storage_path']}")
    
    confirmar = input("\nEscribe 'ELIMINAR' para confirmar: ").strip()
    
    if confirmar != 'ELIMINAR':
        print("[INFO] Cancelado")
        return
    
    # Eliminar carpeta
    import shutil
    if os.path.exists(manga['local_storage_path']):
        try:
            shutil.rmtree(manga['local_storage_path'])
            print(f"[OK] Carpeta eliminada")
        except Exception as e:
            print(f"[ERROR] No se pudo eliminar carpeta: {e}")
    else:
        print("[INFO] Carpeta no existe")
    
    # Eliminar de DB
    db.delete_manga(manga['id'])
    print(f"[OK] Entrada DB eliminada")
    
    # Regenerar index
    try:
        regenerar_seccion_mangas()
        print(f"[OK] Index principal actualizado")
    except Exception as e:
        print(f"[WARN] No se pudo actualizar index: {e}")
    
    print(f"\n[OK] '{manga['title']}' eliminado completamente")

def ver_info_manga():
    """Ver toda la informacion de un manga"""
    print("\n--- INFORMACION MANGA ---")
    
    all_manga = db.get_all_manga()
    if not all_manga:
        print("[INFO] No hay mangas")
        return
    
    print("\nMangas disponibles:")
    for i, m in enumerate(all_manga, 1):
        print(f"  {i}. {m['title']}")
    
    try:
        choice = int(input("\nSelecciona manga (0 cancelar): "))
        if choice == 0:
            return
        manga = all_manga[choice - 1]
    except (ValueError, IndexError):
        print("[ERROR] Seleccion invalida")
        return
    
    # Mostrar TODOS los campos
    print(f"\n{'='*60}")
    print(f"INFORMACION COMPLETA: {manga['title']}")
    print(f"{'='*60}")
    
    # Campos principales
    print(f"\nID: {manga.get('id')}")
    print(f"Titulo: {manga.get('title')}")
    print(f"Check URL: {manga.get('check_url')}")
    print(f"Slug: {manga.get('slug')}")
    
    # Capitulos
    print(f"\nLast Checked Chapter: {manga.get('last_checked_chapter')}")
    print(f"Current Chapter: {manga.get('current_chapter')}")
    print(f"Current Reading: {manga.get('current_reading')}")
    
    # Estado
    tracking_str = "Activo" if manga.get('tracking') == 1 else "Inactivo"
    print(f"\nTracking: {tracking_str}")
    
    # Tipo pagina
    print(f"\nPage Type ID: {manga.get('page_type_id')}")
    print(f"Page Type Name: {manga.get('page_type_name')}")
    print(f"Checker Script: {manga.get('checker_script_path')}")
    
    # Paths
    print(f"\nLocal Storage: {manga.get('local_storage_path')}")
    print(f"Olympus Index URL: {manga.get('olympus_index_url')}")
    print(f"Last Download URL: {manga.get('last_download_url')}")
    
    # Timestamp
    print(f"\nLast Check Timestamp: {manga.get('last_check_timestamp')}")
    
    print(f"\n{'='*60}")
    
    input("\nPresiona Enter para continuar...")

# ============================================================================
# GESTIONAR SEGUIMIENTO
# ============================================================================

def menu_gestionar_seguimiento():
    """Menu gestion de seguimiento"""
    while True:
        print("\n" + "-"*50)
        print("GESTIONAR SEGUIMIENTO")
        print("-"*50)
        print("1. Anadir manga a seguimiento")
        print("2. Editar manga en seguimiento")
        print("3. Quitar manga de seguimiento")
        print("4. Chequear nuevos capitulos")
        print("5. Añadir tipo de pagina")
        print("6. Listar tipos de paginas")
        print("7. Editar tipo paginas")
        print("8. Chequear y descargar nuevos capitulos")
        print("9. Chequear capitulos nuevo para manga individual")
        print("0. Volver")
        
        opcion = input("\nOpcion: ").strip()
        
        if opcion == "1":
            anadir_manga_seguimiento()
        elif opcion == "2":
            editar_manga_solo_tracking()
        elif opcion == "3":
            quitar_manga_seguimiento()
        elif opcion == "4":
            chequear_capitulos()
        elif opcion == "5":
            add_tipo_pagina()
        elif opcion == "6":
            listar_tipos_paginas()
        elif opcion == "7":
            editar_tipo_paginas()
        elif opcion == "8":
            chequear_y_descargar()
        elif opcion == "9":
            chequear_manga_individual()
        elif opcion == "0":
            break
        else:
            print("[ERROR] Opcion invalida")

def anadir_manga_seguimiento():
    """Añadir manga a seguimiento (tracking=0 -> tracking=1)"""
    print("\n--- ANADIR MANGA A SEGUIMIENTO ---")
    
    untracked = db.get_manga_by_tracking(0)
    if not untracked:
        print("[INFO] No hay mangas sin seguimiento")
        return
    
    print("\nMangas disponibles:")
    for i, m in enumerate(untracked, 1):
        print(f"  {i}. {m['title']}")
    
    try:
        choice = int(input("\nSelecciona manga (0 cancelar): "))
        if choice == 0:
            return
        manga = untracked[choice - 1]
    except (ValueError, IndexError):
        print("[ERROR] Seleccion invalida")
        return
    
    # Pedir datos de tracking
    last_checked = input("Ultimo capitulo chequeado: ").strip()
    current_reading = input("Capitulo actual leyendo: ").strip()
    
    # Actualizar tracking
    db.set_tracking(manga['id'], 1)
    
    if last_checked:
        with db.get_connection() as conn:
            conn.execute('UPDATE manga SET last_checked_chapter = ? WHERE id = ?',
                       (last_checked, manga['id']))
    
    if current_reading:
        with db.get_connection() as conn:
            conn.execute('UPDATE manga SET current_reading = ? WHERE id = ?',
                       (current_reading, manga['id']))
    
    print(f"\n[OK] '{manga['title']}' anadido a seguimiento")

def editar_manga_solo_tracking():
    """Editar manga (SOLO opciones tracking)"""
    print("\n--- EDITAR SEGUIMIENTO ---")
    
    tracked = db.get_manga_by_tracking(1)
    if not tracked:
        print("[INFO] No hay mangas en seguimiento")
        return
    
    print("\nMangas en seguimiento:")
    for i, m in enumerate(tracked, 1):
        print(f"  {i}. {m['title']}")
    
    try:
        choice = int(input("\nSelecciona manga (0 cancelar): "))
        if choice == 0:
            return
        manga = tracked[choice - 1]
    except (ValueError, IndexError):
        print("[ERROR] Seleccion invalida")
        return
    
    while True:
        print(f"\n--- EDITANDO: {manga['title']} ---")
        print(f"1. Last checked: {manga['last_checked_chapter']}")
        print(f"2. Current chapter: {manga['current_chapter']}")
        print(f"3. Current reading: {manga['current_reading']}")
        print("0. Volver")
        
        edit_choice = input("\nCampo a editar: ").strip()
        
        if edit_choice == "0":
            break
        elif edit_choice in ["1", "2", "3"]:
            field_map = {
                "1": ("last_checked_chapter", "Ultimo chequeado"),
                "2": ("current_chapter", "Ultimo online"),
                "3": ("current_reading", "Leyendo actualmente")
            }
            
            field, label = field_map[edit_choice]
            new_value = input(f"Nuevo {label}: ").strip()
            
            if new_value:
                with db.get_connection() as conn:
                    conn.execute(f'UPDATE manga SET {field} = ? WHERE id = ?',
                               (new_value, manga['id']))
                manga[field] = new_value
                print("[OK] Actualizado")
        else:
            print("[ERROR] Opcion invalida")

def quitar_manga_seguimiento():
    """Quitar manga de seguimiento (tracking=1 -> tracking=0)"""
    print("\n--- QUITAR MANGA DE SEGUIMIENTO ---")
    
    tracked = db.get_manga_by_tracking(1)
    if not tracked:
        print("[INFO] No hay mangas en seguimiento")
        return
    
    print("\nMangas en seguimiento:")
    for i, m in enumerate(tracked, 1):
        print(f"  {i}. {m['title']}")
    
    try:
        choice = int(input("\nSelecciona manga (0 cancelar): "))
        if choice == 0:
            return
        manga = tracked[choice - 1]
    except (ValueError, IndexError):
        print("[ERROR] Seleccion invalida")
        return
    
    confirmar = input(f"Quitar '{manga['title']}' de seguimiento? (s/n): ").lower()
    if confirmar == 's':
        db.set_tracking(manga['id'], 0)
        print(f"[OK] '{manga['title']}' quitado de seguimiento")
    else:
        print("[INFO] Cancelado")

def chequear_capitulos():
    """Chequear nuevos capitulos en ventana independiente"""
    print("\n[INFO] Lanzando chequeo de capitulos...")
    
    try:
        subprocess.Popen([
            'x-terminal-emulator', '-e',
            'python3', 'check_worker.py'
        ])
        print("[OK] Chequeo iniciado en nueva ventana")
    except Exception as e:
        print(f"[ERROR] {e}")
    
    input("\nPresiona Enter para continuar...")
    
def add_tipo_pagina():
    """ Añadir tipo de pagina """    
    print("\n--- AÑADIR TIPO DE PAGINA ---")
    
    nombre = input("Introduce el nombre de la pagina: ")
    if not nombre:
        print("[ERROR] Nombre requerido")
        return
    url = input("Introduce la url base de la pagina:\n")
    if not url:
        print("[ERROR] URL requerido")
        return
    checker_script_path = input("Introduce la ruta relativa desde main.py para el checker de la pagina:\n")
    if not checker_script_path:
        print("[ERROR] Path del checker requerido")
        return
    downloader_script_path = input("Introduce la ruta relativa desde main.py para el checker de la pagina:\n")    
    if not downloader_script_path:
        print("[ERROR] Path del downloader requerido")
        return
    
    page_id = db.add_page_type(nombre, url, checker_script_path, downloader_script_path)
    
    print(f"\n[OK] Pagina creada (ID: {page_id})")    
    
    listar_tipos_paginas()

def listar_tipos_paginas():
    """Listar tipos de paginas"""
    print("\n--- TIPOS DE PAGINAS ---")
    
    page_types = db.get_all_page_types()
    if not page_types:
        print("[INFO] No hay tipos configurados")
        return
    
    for pt in page_types:
        print(f"\nID: {pt['id']}")
        print(f"  Nombre: {pt['name']}")
        print(f"  Base URL: {pt['base_url']}")
        print(f"  Checker: {pt['checker_script_path']}")
        print(f"  Downloader: {pt['downloader_script_path']}")
    
    input("\nPresiona Enter para continuar...")

def editar_tipo_paginas():
    """Editar tipo de pagina"""
    print("\n--- EDITAR TIPO PAGINA ---")
    
    page_types = db.get_all_page_types()
    if not page_types:
        print("[INFO] No hay tipos configurados")
        return
    
    print("\nTipos disponibles:")
    for i, pt in enumerate(page_types, 1):
        print(f"  {i}. {pt['name']}")
    
    try:
        choice = int(input("\nSelecciona tipo (0 cancelar): "))
        if choice == 0:
            return
        page_type = page_types[choice - 1]
    except (ValueError, IndexError):
        print("[ERROR] Seleccion invalida")
        return
    
    while True:
        print(f"\n--- EDITANDO: {page_type['name']} ---")
        print(f"1. Nombre: {page_type['name']}")
        print(f"2. Base URL: {page_type['base_url']}")
        print(f"3. Checker path: {page_type['checker_script_path']}")
        print(f"4. Downloader path: {page_type['downloader_script_path']}")
        print("0. Volver")
        
        edit_choice = input("\nCampo a editar: ").strip()
        
        if edit_choice == "0":
            break
        elif edit_choice in ["1", "2", "3", "4"]:
            field_map = {
                "1": ("name", "Nombre"),
                "2": ("base_url", "Base URL"),
                "3": ("checker_script_path", "Checker path"),
                "4": ("downloader_script_path", "Downloader path")
            }
            
            field, label = field_map[edit_choice]
            new_value = input(f"Nuevo {label}: ").strip()
            
            if new_value:
                with db.get_connection() as conn:
                    conn.execute(f'UPDATE page_types SET {field} = ? WHERE id = ?',
                               (new_value, page_type['id']))
                page_type[field] = new_value
                print("[OK] Actualizado")
        else:
            print("[ERROR] Opcion invalida")
            
def chequear_y_descargar():
    """Chequear capitulos y descargar automaticamente"""
    print("\n[INFO] Lanzando chequeo + descarga automatica...")
    print("[WARN] Esta operacion puede tardar varios minutos")
    print("[INFO] current_reading NO se actualizara (solo current_chapter)")
    
    confirmar = input("\nContinuar? (s/n): ").lower()
    if confirmar != 's':
        print("[INFO] Cancelado")
        return
    
    try:
        subprocess.Popen([
            'x-terminal-emulator', '-e',
            'python3', 'check_and_download_worker.py'
        ])
        print("[OK] Proceso iniciado en nueva ventana")
    except Exception as e:
        print(f"[ERROR] {e}")
    
    input("\nPresiona Enter para continuar...")

def chequear_manga_individual():
    """Chequear un solo manga sin abrir ventana nueva"""
    print("\n--- CHEQUEAR MANGA INDIVIDUAL ---")
    
    tracked = db.get_manga_by_tracking(1)
    if not tracked:
        print("[INFO] No hay mangas en seguimiento")
        input("\nPresiona Enter para continuar...")
        return
    
    print("\nMangas en seguimiento:")
    for i, m in enumerate(tracked, 1):
        print(f"  {i}. {m['title']}")
    
    try:
        choice = int(input("\nSelecciona manga (0 cancelar): "))
        if choice == 0:
            return
        manga = tracked[choice - 1]
    except (ValueError, IndexError):
        print("[ERROR] Seleccion invalida")
        input("\nPresiona Enter para continuar...")
        return
    
    # Importar y llamar directamente
    import sys
    import os
    import time
    import importlib.util
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    def load_checker_class_only(checker_path):
        absolute_path = os.path.join(BASE_DIR, checker_path)
        spec = importlib.util.spec_from_file_location("checker_module", absolute_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        for item_name in dir(module):
            item = getattr(module, item_name)
            if isinstance(item, type) and item_name.endswith('Checker') and item_name != 'BaseChecker':
                return item
        raise Exception(f"No se encontro clase Checker")
    
    # Chequear
    try:
        print(f"\nVerificando: {manga['title']}...")
        start_time = time.time()
        
        page_type = db.get_page_type_by_id(manga['page_type_id'])
        checker_class = load_checker_class_only(page_type['checker_script_path'])
        checker = checker_class(manga)
        
        info = checker.get_chapter_info()
        
        if info['has_new']:
            with db.get_connection() as conn:
                conn.execute(
                    'UPDATE manga SET current_chapter = ? WHERE id = ?',
                    (info['latest_chapter'], manga['id'])
                )
            print(f"  [NUEVO] Capitulos disponibles: {info['latest_chapter']}")
            print(f"  [INFO] Capitulos atras: {info['difference']}")
            
            # Regenerar index
            try:
                from server.server_utils import regenerar_seccion_seguimiento
                regenerar_seccion_seguimiento()
                print("  [OK] Index actualizado")
            except:
                pass
        else:
            print(f"  [OK] Sin capitulos nuevos (ultimo: {info['latest_chapter']})")
        
        elapsed = time.time() - start_time
        print(f"\nTiempo: {elapsed:.2f}s")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPresiona Enter para continuar...")
    
    

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    menu_principal()