import sys
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from database.db_manager import DatabaseManager

def add_olympus_url_fields():
    db = DatabaseManager()
    
    try:
        with db.get_connection() as conn:
            # Agregar olympus_index_url
            try:
                conn.execute('ALTER TABLE manga ADD COLUMN olympus_index_url TEXT')
                print("[OK] Campo 'olympus_index_url' agregado")
            except Exception as e:
                if 'duplicate column name' in str(e).lower():
                    print("[INFO] Campo 'olympus_index_url' ya existe")
                else:
                    raise
            
            # Agregar last_download_url
            try:
                conn.execute('ALTER TABLE manga ADD COLUMN last_download_url TEXT')
                print("[OK] Campo 'last_download_url' agregado")
            except Exception as e:
                if 'duplicate column name' in str(e).lower():
                    print("[INFO] Campo 'last_download_url' ya existe")
                else:
                    raise
            
            conn.commit()
        
        print("\n[EXITO] Migracion completada")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("="*50)
    print("MIGRACION: Agregar olympus_index_url y last_download_url")
    print("="*50)
    add_olympus_url_fields()