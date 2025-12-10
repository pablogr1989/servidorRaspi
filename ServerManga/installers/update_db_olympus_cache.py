import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

def main():
    print("Creando tabla olympus_com_cache...")
    
    db = DatabaseManager()
    
    try:
        db.add_olympus_com_cache_table()
        print("[OK] Tabla olympus_com_cache creada exitosamente")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == '__main__':
    main()