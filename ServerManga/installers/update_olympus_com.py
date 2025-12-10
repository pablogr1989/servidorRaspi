#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

def main():
    db = DatabaseManager()
    
    # Verificar si ya existe olympus_com
    existing = db.get_page_type('olympus_com')
    
    if existing:
        print("[INFO] olympus_com ya existe, actualizando downloader_script_path...")
        
        with db.get_connection() as conn:
            conn.execute(
                'UPDATE page_types SET downloader_script_path = ? WHERE name = ?',
                ('downloaders/olympus_com_downloader.py', 'olympus_com')
            )
        
        print("[OK] Actualizado olympus_com")
    else:
        print("[INFO] Creando page_type olympus_com...")
        
        db.add_page_type(
            name='olympus_com',
            base_url='https://olympusbiblioteca.com',
            checker_script_path='checkers/olympus_com_checker.py',
            downloader_script_path='downloaders/olympus_com_downloader.py'
        )
        
        print("[OK] Creado olympus_com")

if __name__ == "__main__":
    main()