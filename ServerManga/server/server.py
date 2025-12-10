#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import sys
from urllib.parse import urlparse, parse_qs
import re
import subprocess

# Resolver imports desde raiz proyecto
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from database.db_manager import DatabaseManager
db = DatabaseManager()

class MiServidor(SimpleHTTPRequestHandler):
    """
    Servidor HTTP multi-manga con API progreso
    """
    
    def translate_path(self, path):
        """
        Traduce URLs a paths del filesystem
        /mangas/overgeared/index.html -> /home/pablopi/Server/ServerManga/mangas/overgeared/index.html
        """
        # Obtener path sin query params
        path = urlparse(path).path
        
        # Remover leading slash
        path = path.lstrip('/')
        
        # Path absoluto base
        base = os.path.join(base_dir)
        
        # Combinar
        full_path = os.path.join(base, path)
        
        return full_path
    
    def do_GET(self):
        """
        Maneja peticiones GET con manejo de errores de conexion
        """
        try:
            parsed_path = urlparse(self.path)
            
            # API endpoints
            if parsed_path.path == '/api/progreso':
                self.manejar_api_progreso(parsed_path)
            elif parsed_path.path == '/guardar_progreso':
                self.manejar_guardar_progreso(parsed_path)
            else:
                # Servir archivos estaticos
                super().do_GET()
        
        except BrokenPipeError:
            # Cliente cerro conexion antes de recibir respuesta completa
            # Ignorar - es comportamiento normal (usuario navego rapido)
            pass
        except ConnectionResetError:
            # Conexion reseteada por el cliente
            # Ignorar - comportamiento normal
            pass
        except Exception as e:
            # Otros errores - log pero no crashear servidor
            print(f"[WARN] Error sirviendo {self.path}: {e}")
    
    def manejar_api_progreso(self, parsed_path):
        """
        GET /api/progreso?manga_id=X
        Retorna current_reading y last_checked_chapter de DB
        """
        params = parse_qs(parsed_path.query)
        
        if 'manga_id' not in params:
            self.send_json_response({
                'success': False,
                'error': 'Falta parametro manga_id'
            }, 400)
            return
        
        try:
            manga_id = int(params['manga_id'][0])
            manga = db.get_manga(manga_id=manga_id)
            
            if not manga:
                self.send_json_response({
                    'success': False,
                    'error': 'Manga no encontrado'
                }, 404)
                return
            
            respuesta = {
                'success': True,
                'current_reading': manga.get('current_reading'),
                'current_chapter': manga.get('last_checked_chapter'),
                'title': manga.get('title')
            }
            
            self.send_json_response(respuesta)
            
        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, 500)
    
    def manejar_guardar_progreso(self, parsed_path):
        """
        GET /guardar_progreso?manga_id=X&capitulo=Y
        Actualiza current_reading en DB
        """
        params = parse_qs(parsed_path.query)
        
        if 'manga_id' not in params or 'capitulo' not in params:
            self.send_json_response({
                'success': False,
                'error': 'Faltan parametros manga_id o capitulo'
            }, 400)
            return
        
        try:
            manga_id = int(params['manga_id'][0])
            capitulo = params['capitulo'][0]
                        
            # Validar formato capitulo
            if not re.match(r'^\d+(\.\d+)?$', capitulo):
                self.send_json_response({
                    'success': False,
                    'error': 'Formato capitulo invalido'
                }, 400)
                return
            
            print(f"Guardar capitulo {capitulo} de manga id = {manga_id}")
            
            # UPDATE en DB
            with db.get_connection() as conn:
                conn.execute(
                    'UPDATE manga SET current_reading = ? WHERE id = ?',
                    (capitulo, manga_id)
                )     
                
            subprocess.Popen([
                'x-terminal-emulator', '-e',
                'bash', '-c', 'cd /home/pablopi/Server/ServerManga && bash servicios/regenerar_web.sh'
            ])         
            
            respuesta = {
                'success': True,
                'manga_id': manga_id,
                'capitulo': capitulo
            }
            
            self.send_json_response(respuesta)
            
        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, 500)
    
    def send_json_response(self, data, status=200):
        """
        Helper para enviar respuestas JSON
        """
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Logs personalizados"""
        mensaje = format % args if args else format
        
        # Loguear solo API y guardar_progreso
        if '/api/' in mensaje or 'guardar_progreso' in mensaje:
            print(f"[API] {mensaje}")

def main():
    puerto = 8000
    
    print("="*60)
    print("SERVIDOR MULTI-MANGA INICIADO")
    print("="*60)
    print(f"\nDireccion: http://localhost:{puerto}")
    print(f"Sirviendo desde: {base_dir}")
    print(f"\nPresiona Ctrl+C para detener\n")
    print("="*60)
    
    try:
        servidor = HTTPServer(('', puerto), MiServidor)
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServidor detenido")
        print("="*60)

if __name__ == "__main__":
    main()