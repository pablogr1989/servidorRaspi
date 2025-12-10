import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        base_dir = '/home/pablopi/Server/ServerManga'
        db_path = os.path.join(base_dir, 'database', 'manga_tracker.db')
        sql_path = os.path.join(base_dir, 'database', 'init_db.sql')
        
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            with open(sql_path, 'r', encoding='utf-8') as f:
                init_sql = f.read()
            
            with self.get_connection() as conn:
                conn.executescript(init_sql)
    
    def _init_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            with open('database/init_db.sql', 'r') as f:
                cursor.executescript(f.read())
            
            conn.commit()
            conn.close()
        
    def _dict_factory(self, cursor, row):
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = self._dict_factory
        return conn
    
    # ========== PAGE TYPES ==========
    
    def add_page_type(self, name, base_url, checker_script_path, downloader_script_path=None):
        with self.get_connection() as conn:
            cursor = conn.execute(
                'INSERT INTO page_types (name, base_url, checker_script_path, downloader_script_path) VALUES (?, ?, ?, ?)',
                (name, base_url, checker_script_path, downloader_script_path)
            )
            return cursor.lastrowid
    
    def get_page_type_by_id(self, page_type_id):
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT id, name, base_url, checker_script_path, downloader_script_path FROM page_types WHERE id = ?',
                (page_type_id,)
            )
            return cursor.fetchone()
        
    def get_page_type(self, name):
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT id, name, base_url, checker_script_path, downloader_script_path FROM page_types WHERE name = ?',
                (name,)
            )
            return cursor.fetchone()
    
    def get_all_page_types(self):
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT id, name, base_url, checker_script_path, downloader_script_path FROM page_types')
            return cursor.fetchall()
    
    # ========== MANGA ==========

    def add_manga(self, title, check_url, page_type_id, local_storage_path, 
                last_checked_chapter=None, current_chapter=None, 
                current_reading=None, tracking=1,
                olympus_index_url=None, last_download_url=None, olympus_net_post_id = 0):
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO manga (title, check_url, page_type_id, local_storage_path,
                                last_checked_chapter, current_chapter, current_reading,
                                tracking, olympus_index_url, last_download_url, olympus_net_post_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, check_url, page_type_id, local_storage_path,
                last_checked_chapter, current_chapter, current_reading,
                tracking, olympus_index_url, last_download_url, olympus_net_post_id))
            conn.commit()
            return cursor.lastrowid
    
    def update_manga_chapters(self, manga_id, current_chapter, last_checked_chapter=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if last_checked_chapter:
            cursor.execute(
                '''UPDATE manga SET current_chapter = ?, last_checked_chapter = ?, 
                   last_check_timestamp = ? WHERE id = ?''',
                (current_chapter, last_checked_chapter, datetime.now(), manga_id)
            )
        else:
            cursor.execute(
                '''UPDATE manga SET current_chapter = ?, last_check_timestamp = ? 
                   WHERE id = ?''',
                (current_chapter, datetime.now(), manga_id)
            )
        conn.commit()
        conn.close()
    
    def get_manga(self, manga_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM manga WHERE id = ?', (manga_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_manga_by_id(self, manga_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.*, pt.name as page_type_name, pt.checker_script_path
            FROM manga m
            JOIN page_types pt ON m.page_type_id = pt.id
            WHERE m.id = ?
        ''', (manga_id,))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_all_manga(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.*, pt.name as page_type_name, pt.checker_script_path
            FROM manga m 
            JOIN page_types pt ON m.page_type_id = pt.id
        ''')
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_manga_by_page_type(self, page_type_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.*, pt.name as page_type_name, pt.checker_script_path
            FROM manga m
            JOIN page_types pt ON m.page_type_id = pt.id
            WHERE m.page_type_id = ?
        ''', (page_type_id,))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def delete_manga(self, manga_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM manga WHERE id = ?', (manga_id,))
        conn.commit()
        conn.close()
        
    # TRACKING
    def get_manga_by_tracking(self, tracking_status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.*, pt.name as page_type_name, pt.checker_script_path
            FROM manga m
            JOIN page_types pt ON m.page_type_id = pt.id
            WHERE m.tracking = ?
        ''', (tracking_status,))
        results = cursor.fetchall()
        conn.close()
        return results
        
    def get_manga_by_tracking_and_page(self, tracking_status, page_type_id):
        """Retorna mangas dependiendo del tracking y page_type"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                '''SELECT m.*, pt.name as page_type_name, pt.checker_script_path, pt.downloader_script_path
                FROM manga m 
                JOIN page_types pt ON m.page_type_id = pt.id 
                WHERE m.tracking = ? AND m.page_type_id = ?''',
                (tracking_status, page_type_id)
            )
            return cursor.fetchall()

    def set_tracking(self, manga_id, tracking_status):
        """Cambia estado tracking de un manga"""
        conn = self.get_connection()
        conn.execute("UPDATE manga SET tracking = ? WHERE id = ?", (tracking_status, manga_id))
        conn.commit()
        conn.close()

    def update_manga_for_tracking(self, manga_id, last_checked, current_reading):
        """Actualiza manga al activar tracking"""
        conn = self.get_connection()
        conn.execute(
            '''UPDATE manga SET tracking = 1, last_checked_chapter = ?, 
            current_chapter = ?, current_reading = ? WHERE id = ?''',
            (current_reading, current_reading, current_reading, manga_id)
        )
        conn.commit()
        conn.close()
        
        
    def update_olympus_index_url(self, manga_id, olympus_index_url):
        with self.get_connection() as conn:
            conn.execute('UPDATE manga SET olympus_index_url = ? WHERE id = ?',
                    (olympus_index_url, manga_id))
            conn.commit()

    def update_last_download_url(self, manga_id, last_download_url):
        with self.get_connection() as conn:
            conn.execute('UPDATE manga SET last_download_url = ? WHERE id = ?',
                    (last_download_url, manga_id))
            conn.commit()
            
    # METODOS OLYMPUS_COM CACHE
    
    def get_olympus_cache(self, manga_id):
            """Obtener cache olympus_com para un manga"""
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT manga_id, last_search_asc_page, last_search_desc_page, 
                        olympus_last_valid_direction
                    FROM olympus_com_cache
                    WHERE manga_id = ?
                ''', (manga_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None

    def insert_olympus_cache(self, manga_id, asc_page, desc_page, valid_direction):
        """Insertar cache olympus_com"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO olympus_com_cache 
                (manga_id, last_search_asc_page, last_search_desc_page, olympus_last_valid_direction)
                VALUES (?, ?, ?, ?)
            ''', (manga_id, asc_page, desc_page, valid_direction))

    def update_olympus_cache_pages(self, manga_id, asc_page=None, desc_page=None):
        """Actualizar paginas cache olympus_com"""
        updates = []
        params = []
        
        if asc_page is not None:
            updates.append('last_search_asc_page = ?')
            params.append(asc_page)
        
        if desc_page is not None:
            updates.append('last_search_desc_page = ?')
            params.append(desc_page)
        
        if not updates:
            return
        
        params.append(manga_id)
        
        with self.get_connection() as conn:
            conn.execute(f'''
                UPDATE olympus_com_cache 
                SET {', '.join(updates)}
                WHERE manga_id = ?
            ''', params)

    def update_olympus_cache_direction(self, manga_id, direction):
        """Actualizar direction valido cache olympus_com"""
        with self.get_connection() as conn:
            conn.execute('''
                UPDATE olympus_com_cache 
                SET olympus_last_valid_direction = ?
                WHERE manga_id = ?
            ''', (direction, manga_id))

    def delete_olympus_cache(self, manga_id):
        """Eliminar cache olympus_com (forzar reinicializacion)"""
        with self.get_connection() as conn:
            conn.execute('DELETE FROM olympus_com_cache WHERE manga_id = ?', (manga_id,))
        
    # Metodos auxiliares de una sola vez   
    
    def add_post_id_column(self):
        """Agrega columna olympus_net_post_id si no existe"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE manga ADD COLUMN olympus_net_post_id INTEGER")
            conn.commit()
            print("[OK] Columna olympus_net_post_id agregada")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("[INFO] Columna olympus_net_post_id ya existe")
            else:
                print(f"[ERROR] {str(e)}")
        finally:
            conn.close()
         
    def add_current_reading_column(self):
        """Agrega columna current_reading si no existe"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE manga ADD COLUMN current_reading TEXT")
            conn.commit()
            print("[OK] Columna current_reading agregada")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("[INFO] Columna current_reading ya existe")
            else:
                print(f"[ERROR] {str(e)}")
        finally:
            conn.close()
            
    def add_tracking_column(self):
        """Agrega columna tracking (bool) y setea existing manga a true"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE manga ADD COLUMN tracking INTEGER DEFAULT 1")
            cursor.execute("UPDATE manga SET tracking = 1 WHERE tracking IS NULL")
            conn.commit()
            print("[OK] Columna tracking agregada, mangas existentes seteados a true")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("[INFO] Columna tracking ya existe")
            else:
                print(f"[ERROR] {str(e)}")
        finally:
            conn.close()
            
    def add_downloader_column(self):
        with self.get_connection() as conn:
            try:
                conn.execute('ALTER TABLE page_types ADD COLUMN downloader_script_path TEXT')
                print("[OK] Columna downloader_script_path agregada")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print("[INFO] Columna downloader_script_path ya existe")
                else:
                    print(f"[ERROR] {e}")                
            
    def add_slug_column(self):
        """Agrega columna slug (TEXT) para almacenar slug de olympus"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE manga ADD COLUMN slug TEXT")
            conn.commit()
            print("[OK] Columna slug agregada")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("[INFO] Columna slug ya existe")
            else:
                print(f"[ERROR] {str(e)}")
        finally:
            conn.close()
            
            
    def add_olympus_com_cache_table(self):
        """Crear tabla olympus_com_cache si no existe"""
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS olympus_com_cache (
                    manga_id INTEGER PRIMARY KEY,
                    last_search_asc_page INTEGER NOT NULL,
                    last_search_desc_page INTEGER NOT NULL,
                    olympus_last_valid_direction TEXT NOT NULL CHECK(olympus_last_valid_direction IN ('asc', 'desc')),
                    FOREIGN KEY (manga_id) REFERENCES manga(id) ON DELETE CASCADE
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_olympus_cache_manga 
                ON olympus_com_cache(manga_id)
            ''')