import os
import sys
from datetime import datetime

class Logger:
    def __init__(self, log_file_path, function_name):
        self.log_file_path = log_file_path
        self.function_name = function_name
        self.file = None
        
        # Crear directorio logs si no existe
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Abrir archivo
        try:
            self.file = open(log_file_path, 'a', encoding='utf-8')
            self._write_header()
        except Exception as e:
            print(f"[ERROR] No se pudo crear log: {e}")
            self.file = None
    
    def _write_header(self):
        if not self.file:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        separator = "=" * 80
        
        self.file.write(f"\n{separator}\n")
        self.file.write(f"INICIO DE EJECUCION: {self.function_name}\n")
        self.file.write(f"FECHA Y HORA: {timestamp}\n")
        self.file.write(f"{separator}\n\n")
        self.file.flush()
    
    def log(self, message):
        """Escribir en log (siempre si existe logger)"""
        if self.file:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.file.write(f"[{timestamp}] {message}\n")
            self.file.flush()
    
    def close(self):
        if self.file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            separator = "=" * 80
            
            self.file.write(f"\n{separator}\n")
            self.file.write(f"FIN DE EJECUCION: {self.function_name}\n")
            self.file.write(f"FECHA Y HORA: {timestamp}\n")
            self.file.write(f"{separator}\n\n")
            self.file.flush()
            self.file.close()
            self.file = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.log(f"[ERROR FATAL] Exception: {exc_type.__name__}: {exc_val}")
            if exc_tb:
                import traceback
                tb_str = ''.join(traceback.format_tb(exc_tb))
                self.log(f"Traceback:\n{tb_str}")
        self.close()
        return False

def create_log_path(prefix="file"):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(BASE_DIR, 'logs')
    timestamp = datetime.now().strftime("%d%m%Y_%H%M")
    log_filename = f"log_{prefix}_{timestamp}.txt"
    return os.path.join(log_dir, log_filename)