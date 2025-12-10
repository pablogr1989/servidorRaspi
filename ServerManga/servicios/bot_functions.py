#!/usr/bin/env python3
import sys
import os
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from checkers.olympus_com_checker import OlympusComChecker
from server.server_utils import *
from check_and_download_worker import check_and_download, show_summary, check_and_download_single
from utils.logger import Logger, create_log_path
from database.db_manager import DatabaseManager

db = DatabaseManager()

def actualizar():
    """Actualizar slugs de Olympus.com"""
    log_path = create_log_path("actualizar")
    
    try:
        with Logger(log_path, "bot_functions.actualizar") as logger:
            msg = f"\n{'='*60}"
            print(msg)
            logger.log(msg)
            
            msg = "ACTUALIZACION DE SLUGS"
            print(msg)
            logger.log(msg)
            
            msg = f"{'='*60}\n"
            print(msg)
            logger.log(msg)
            
            try:
                OlympusComChecker.actualizar_todos_slugs(mode_debug=True, logger=logger)
                
                msg = f"\n{'='*60}"
                print(msg)
                logger.log(msg)
                
                msg = "ACTUALIZACION COMPLETADA"
                print(msg)
                logger.log(msg)
                
                msg = f"{'='*60}"
                print(msg)
                logger.log(msg)
                
            except Exception as e:
                msg = f"\n[ERROR] {e}"
                print(msg)
                logger.log(msg)
                import traceback
                logger.log(traceback.format_exc())
                traceback.print_exc()
                
    except Exception as e:
        print(f"[ERROR FATAL] Error creando logger: {e}")

def openNordVPN(logger=None):
    import subprocess
    
    msg = "[INFO] Conectando NordVPN..."
    print(msg)
    if logger:
        logger.log(msg)
    
    try:
        subprocess.run(['sudo', 'systemctl', 'start', 'nordvpnd'], check=True, capture_output=True)
        msg = "[OK] VPN conectada"
        print(msg)
        if logger:
            logger.log(msg)
    except subprocess.CalledProcessError as e:
        msg = f"[WARN] VPN fallo: {e}"
        print(msg)
        if logger:
            logger.log(msg)
            
    time.sleep(10)
    
    try:
        subprocess.run(['/usr/bin/nordvpn', 'connect', 'Spain'], check=True, capture_output=True)
        msg = "[OK] VPN conectada"
        print(msg)
        if logger:
            logger.log(msg)
    except subprocess.CalledProcessError as e:
        msg = f"[WARN] VPN fallo: {e}"
        print(msg)
        if logger:
            logger.log(msg)
        
def closeNordVPN(logger=None):
    import subprocess
    
    msg = "\n[INFO] Desconectando NordVPN..."
    print(msg)
    if logger:
        logger.log(msg)
    
    try:
        # Desconectar VPN
        subprocess.run(['/usr/bin/nordvpn', 'disconnect'], check=True, capture_output=True)
        msg = "[OK] VPN desconectada"
        print(msg)
        if logger:
            logger.log(msg)
        
        # Parar el servicio
        subprocess.run(['sudo', 'systemctl', 'stop', 'nordvpnd'], check=False, capture_output=True)
        msg = "[OK] Servicio nordvpnd detenido"
        print(msg)
        if logger:
            logger.log(msg)
        
        # Matar procesos nordvpn restantes
        subprocess.run(['sudo', 'killall', '-9', 'nordvpnd'], check=False, capture_output=True)
        subprocess.run(['sudo', 'killall', '-9', 'nordvpn'], check=False, capture_output=True)
        msg = "[OK] Procesos nordvpn eliminados"
        print(msg)
        if logger:
            logger.log(msg)
            
    except subprocess.CalledProcessError as e:
        msg = f"[WARN] Desconexion VPN fallo: {e}"
        print(msg)
        if logger:
            logger.log(msg)
            
def statusNordVPN(logger=None):
    import subprocess
    
    msg = "\n[INFO] Verificando estado NordVPN..."
    print(msg)
    if logger:
        logger.log(msg)
    
    status_info = []
    
    # 1. Estado del servicio nordvpnd
    try:
        result = subprocess.run(['systemctl', 'is-active', 'nordvpnd'], 
                              capture_output=True, text=True)
        servicio_estado = result.stdout.strip()
        status_info.append(f"Servicio nordvpnd: {servicio_estado}")
    except Exception as e:
        status_info.append(f"Servicio nordvpnd: Error - {e}")
    
    # 2. Estado de la conexion VPN
    try:
        result = subprocess.run(['/usr/bin/nordvpn', 'status'], 
                              capture_output=True, text=True)
        vpn_status = result.stdout.strip()
        status_info.append(f"Estado VPN:\n{vpn_status}")
    except Exception as e:
        status_info.append(f"Estado VPN: Error - {e}")
    
    # 3. Procesos nordvpn activos
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        nordvpn_procs = [line for line in result.stdout.split('\n') if 'nordvpn' in line.lower()]
        if nordvpn_procs:
            status_info.append(f"Procesos activos ({len(nordvpn_procs)}):")
            for proc in nordvpn_procs:
                status_info.append(f"  {proc}")
        else:
            status_info.append("Procesos activos: Ninguno")
    except Exception as e:
        status_info.append(f"Procesos: Error - {e}")
    
    # Mostrar todo
    full_status = "\n".join(status_info)
    print(full_status)
    if logger:
        logger.log(full_status)
    
    return full_status

def descargar_olympus_com():
    descargar(1)
    
def descargar_olympus_net():
    descargar(2)
    
def descargar_tmo():
    descargar(3)
    
def descargar_menos_olympus_com():
    descargar(4)
    
def descargar_animeallstar():
    descargar(5)

def descargar(page_mode=0):
    """Chequear y descargar capitulos nuevos"""
    log_path = create_log_path("descargar")
    
    try:
        with Logger(log_path, f"bot_functions.descargar(page_mode={page_mode})") as logger:
            msg = f"\n{'='*60}"
            print(msg)
            logger.log(msg)
            
            msg = "CHECK + DESCARGA"
            print(msg)
            logger.log(msg)
            
            msg = f"{'='*60}\n"
            print(msg)
            logger.log(msg)
            
            try:
                results, descargados, check_time = check_and_download(page_mode, mode_debug=True, logger=logger)
                show_summary(results, descargados, check_time, mode_debug=True, logger=logger)
                
                msg = "\nRegenerando web..."
                print(msg)
                logger.log(msg)
                
                regenerar_seccion_mangas()
                regenerar_seccion_pendientes()
                regenerar_seccion_seguimiento()
                
                msg = "[OK] Web actualizada"
                print(msg)
                logger.log(msg)
                
                msg = f"\n{'='*60}"
                print(msg)
                logger.log(msg)
                
                msg = "DESCARGA COMPLETADA"
                print(msg)
                logger.log(msg)
                
                msg = f"{'='*60}"
                print(msg)
                logger.log(msg)
                
            except Exception as e:
                msg = f"\n[ERROR] {e}"
                print(msg)
                logger.log(msg)
                import traceback
                logger.log(traceback.format_exc())
                traceback.print_exc()
                
    except Exception as e:
        print(f"[ERROR FATAL] Error creando logger: {e}")

def tarea_diaria():
    """Actualizar slugs + chequear + descargar (con pausa)"""
    log_path = create_log_path("tarea_diaria")
    
    try:
        with Logger(log_path, "bot_functions.tarea_diaria") as logger:
            msg = f"\n{'='*60}"
            print(msg)
            logger.log(msg)
            
            msg = "TAREA DIARIA COMPLETA"
            print(msg)
            logger.log(msg)
            
            msg = f"{'='*60}\n"
            print(msg)
            logger.log(msg)
            
            try:
                # PASO 1: Actualizar slugs
                msg = "[1/2] Actualizando slugs..."
                print(msg)
                logger.log(msg)
                
                OlympusComChecker.actualizar_todos_slugs(logger=logger, mode_debug=True)
                
                msg = "[OK] Slugs actualizados"
                print(msg)
                logger.log(msg)
                
                # Pausa 1 minuto
                msg = "\n[PAUSA] Esperando 60 segundos antes de descargar..."
                print(msg)
                logger.log(msg)
                time.sleep(60)
                
                # PASO 2: Chequear y descargar
                msg = "\n[2/2] Chequeando y descargando..."
                print(msg)
                logger.log(msg)
                
                results, descargados, check_time = check_and_download(mode_debug=False, logger=logger)
                show_summary(results, descargados, check_time, mode_debug=True, logger=logger)
                
                # Regenerar web
                msg = "\nRegenerando web..."
                print(msg)
                logger.log(msg)
                
                regenerar_seccion_mangas()
                regenerar_seccion_pendientes()
                regenerar_seccion_seguimiento()
                
                msg = "[OK] Web actualizada"
                print(msg)
                logger.log(msg)
                
                msg = f"\n{'='*60}"
                print(msg)
                logger.log(msg)
                
                msg = "TAREA DIARIA COMPLETADA"
                print(msg)
                logger.log(msg)
                
                msg = f"{'='*60}"
                print(msg)
                logger.log(msg)
                
            except Exception as e:
                msg = f"\n[ERROR] {e}"
                print(msg)
                logger.log(msg)
                import traceback
                logger.log(traceback.format_exc())
                traceback.print_exc()
                
    except Exception as e:
        print(f"[ERROR FATAL] Error creando logger: {e}")
        
def descargar_manga_por_id(id):
    """Chequear y descargar capitulos nuevos del manga seleccionado"""
    log_path = create_log_path("descargar")
    
    try:
        with Logger(log_path, f"bot_functions.descargar_manga_por_id(id={id})") as logger:
            msg = f"\n{'='*60}"
            print(msg)
            logger.log(msg)
            
            msg = "CHECK + DESCARGA"
            print(msg)
            logger.log(msg)
            
            msg = f"{'='*60}\n"
            print(msg)
            logger.log(msg)
            
            try:
                results, descargados, check_time = check_and_download_single(id, mode_debug=True, logger=logger)
                show_summary(results, descargados, check_time, mode_debug=True, logger=logger)
                
                msg = "\nRegenerando web..."
                print(msg)
                logger.log(msg)
                
                regenerar_seccion_mangas()
                regenerar_seccion_pendientes()
                regenerar_seccion_seguimiento()
                
                msg = "[OK] Web actualizada"
                print(msg)
                logger.log(msg)
                
                msg = f"\n{'='*60}"
                print(msg)
                logger.log(msg)
                
                msg = "DESCARGA COMPLETADA"
                print(msg)
                logger.log(msg)
                
                msg = f"{'='*60}"
                print(msg)
                logger.log(msg)
                
            except Exception as e:
                msg = f"\n[ERROR] {e}"
                print(msg)
                logger.log(msg)
                import traceback
                logger.log(traceback.format_exc())
                traceback.print_exc()
                
    except Exception as e:
        print(f"[ERROR FATAL] Error creando logger: {e}")
        
def print_all_manga():
    """Listar todos los mangas"""
    print("\n--- LISTA DE MANGAS ---")
    
    all_manga = db.get_all_manga()
    if not all_manga:
        print("[INFO] No hay mangas")
        return
    
    print(f"\nTotal: {len(all_manga)} mangas\n")
    for m in all_manga:
        tracking_status = "Siguiendo" if m['tracking'] == 1 else "No siguiendo"
        print(f"{m['id']}: {m['title']} | {tracking_status} | {m['page_type_name']} " + (f" | PostID: {m['olympus_net_post_id']}" if m['page_type_id'] == 2 else "") + f" | Leyendo : {m['current_reading']} | Total: {m['current_chapter']}")

def help():
    comandos_info = {
        'actualizar': 'Actualiza los slugs de los mangas en la base de datos',
        'descargar': 'Descarga capitulos nuevos de todos los mangas',
        'descargar_olympus_com': 'Descarga solo de olympusbiblioteca.com',
        'descargar_olympus_net': 'Descarga solo de olympusbiblioteca.net',
        'descargar_tmo': 'Descarga solo de TMO',
        'descargar_allstar': 'Descarga solo de Anime All Star',
        'descargar_menos_olympus_com': 'Descarga de todos excepto olympus.com',
        'descargar_manga': 'Descarga un manga especifico por ID (uso: /descargar_manga <id>)',
        'listar_mangas': 'Lista todos los mangas en la base de datos',
        'diaria': 'Ejecuta la tarea diaria (actualizar + descargar + regenerar)',
        'regenerar': 'Regenera el index principal de la web',
        'iniciar': 'Inicia el servidor manga',
        'apagar': 'Apaga el servidor manga',
        'reiniciar': 'Reinicia el servidor manga',
        'status': 'Muestra el estado del servidor manga',
        'uptime': 'Muestra el tiempo de actividad del sistema',
        'disk': 'Muestra el espacio en disco',
        'temp': 'Muestra la temperatura del CPU',
        'ps': 'Muestra procesos relacionados con ServerManga',
        'logs': 'Muestra ultimos 30 logs del servidor'
    }
    
    output = "Comandos disponibles:\n\n"
    for cmd, desc in comandos_info.items():
        output += f"/{cmd}: {desc}\n"
    
    print(output)
    
def get_latest_log():
    import os
    import glob
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(BASE_DIR, 'logs')
    
    # Buscar todos los archivos log_*.txt
    log_files = glob.glob(os.path.join(log_dir, 'log_*.txt'))
    
    if not log_files:
        return "No se encontraron archivos de log"
    
    # Obtener el mas reciente por fecha de modificacion
    latest_log = max(log_files, key=os.path.getmtime)
    
    # Leer contenido
    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            content = f.read()
        print(content)
    except Exception as e:
        return f"Error al leer log: {e}"


def main():
    """Menu interactivo (opcional, para testing local)"""
    print(f"\n{'='*60}")
    print("BOT FUNCTIONS - MENU")
    print(f"{'='*60}")
    print("\n1. Actualizar slugs")
    print("2. Descargar nuevos")
    print("3. Tarea diaria (actualizar + descargar)")
    print("0. Salir")
    
    opcion = input("\nOpcion: ").strip()
    
    if opcion == "1":
        actualizar()
    elif opcion == "2":
        descargar()
    elif opcion == "3":
        tarea_diaria()
    elif opcion == "0":
        print("Saliendo...")
        return
    else:
        print("Opcion invalida")
    
    input("\nPresiona Enter para cerrar...")

if __name__ == "__main__":
    main()