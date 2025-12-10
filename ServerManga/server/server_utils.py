#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# Resolver imports desde raiz proyecto
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from database.db_manager import DatabaseManager

db = DatabaseManager()


def generar_seccion_pendientes():
    """
    Seccion pendientes de leer (current_reading < last_checked_chapter)
    Muestra capitulos descargados pero no leidos
    """
    mangas = db.get_manga_by_tracking(1)
    
    pendientes = []
    for m in mangas:
        reading = m.get('current_reading')
        last_checked = m.get('last_checked_chapter')
        
        if reading and last_checked:
            try:
                diff = float(last_checked) - float(reading)
                if diff > 0:
                    slug_path = '/mangas/' + m['local_storage_path'].split('mangas/')[-1]
                    
                    # Buscar portada con cualquier extension
                    manga_dir = m['local_storage_path']
                    portada_file = None
                    for ext in ['webp', 'jpg', 'png']:
                        test_file = f'portada.{ext}'
                        test_path = os.path.join(manga_dir, test_file)
                        if os.path.exists(test_path):
                            portada_file = test_file
                            break
                    
                    # Si no existe ninguna, usar webp por defecto
                    if not portada_file:
                        portada_file = 'portada.webp'
                    
                    portada_path = f'{slug_path}/{portada_file}'
                    
                    pendientes.append({
                        'title': m['title'],
                        'slug': slug_path,
                        'reading': reading,
                        'last_checked': last_checked,
                        'diff': diff,
                        'portada': portada_path
                    })
            except:
                pass
    
    pendientes.sort(key=lambda x: x['diff'], reverse=True)
    
    html = '<section id="seccion-pendientes" class="card">\n'
    html += '  <div class="card-header">\n'
    html += '    <h2 class="section-title">En seguimiento</h2>\n'
    html += '    <h3>Pendientes de Leer</h3>\n'
    html += f'    <span class="badge">{len(pendientes)}</span>\n'
    html += '  </div>\n'
    
    if pendientes:
        html += '  <div class="manga-grid">\n'
        for m in pendientes:
            html += f'    <a href="{m["slug"]}" class="manga-card">\n'
            html += f'      <div class="manga-cover">\n'
            html += f'        <img src="{m["portada"]}" alt="{m["title"]}" onerror="this.src=\'/placeholder.png\'">\n'
            html += f'        <div class="new-badge">LEER</div>\n'
            html += f'      </div>\n'
            html += f'      <div class="manga-info-card">\n'
            html += f'        <div class="manga-title">{m["title"]}</div>\n'
            html += f'        <div class="chapter-info">\n'
            html += f'          <span class="current">Cap. {m["last_checked"]}</span>\n'
            # html += f'          <span class="diff">+{int(m["diff"])}</span>\n'
            html += f'        </div>\n'
            html += f'        <div class="read-progress">Leido: Cap. {m["reading"]}</div>\n'
            html += f'      </div>\n'
            html += f'    </a>\n'
        html += '  </div>\n'
    else:
        html += '  <div class="empty-state">\n'
        html += '    <p>No hay capitulos pendientes de leer</p>\n'
        html += '  </div>\n'
    
    html += '</section>\n'
    return html

def generar_seccion_seguimiento():
    """
    Genera HTML seccion seguimiento (tracking=1 con capitulos nuevos)
    Grid responsive con portadas
    DIFF = current_chapter - last_checked_chapter (capitulos sin descargar)
    """
    mangas = db.get_manga_by_tracking(1)
    
    # Filtrar solo con capitulos nuevos (sin descargar)
    con_nuevos = []
    for m in mangas:
        current = m.get('current_chapter')
        last_checked = m.get('last_checked_chapter')
        
        if current and last_checked:
            try:
                diff = float(current) - float(last_checked)
                if diff > 0:
                    slug_path = '/mangas/' + m['local_storage_path'].split('mangas/')[-1]
                    portada_path = f'{slug_path}/portada.webp'
                    reading = m.get('current_reading', '?')
                    
                    con_nuevos.append({
                        'title': m['title'],
                        'slug': slug_path,
                        'current': current,
                        'last_checked': last_checked,
                        'reading': reading,
                        'diff': diff,
                        'portada': portada_path
                    })
            except:
                pass
    
    # Ordenar por diferencia (mas capitulos sin descargar primero)
    con_nuevos.sort(key=lambda x: x['diff'], reverse=True)
    
    html = '<section id="seccion-seguimiento" class="card">\n'
    html += '  <div class="card-header">\n'
    html += '    <h2>Nuevas descargas</h2>\n'
    html += f'    <span class="badge">{len(con_nuevos)}</span>\n'
    html += '  </div>\n'
    
    if con_nuevos:
        html += '  <div class="manga-grid">\n'
        for m in con_nuevos:
            html += f'    <a href="{m["slug"]}" class="manga-card">\n'
            html += f'      <div class="manga-cover">\n'
            html += f'        <img src="{m["portada"]}" alt="{m["title"]}" onerror="this.src=\'/placeholder.png\'">\n'
            html += f'        <div class="new-badge">NUEVO</div>\n'
            html += f'      </div>\n'
            html += f'      <div class="manga-info-card">\n'
            html += f'        <div class="manga-title">{m["title"]}</div>\n'
            html += f'        <div class="chapter-info">\n'
            html += f'          <span class="current">Cap. {m["current"]}</span>\n'
            html += f'          <span class="diff">+{int(m["diff"])}</span>\n'
            html += f'        </div>\n'
            html += f'        <div class="read-progress">Descargado: Cap. {m["last_checked"]}</div>\n'
            html += f'      </div>\n'
            html += f'    </a>\n'
        html += '  </div>\n'
    else:
        html += '  <div class="empty-state">\n'
        html += '    <p>No han salido nuevos capitulos</p>\n'
        html += '  </div>\n'
    
    html += '</section>\n'
    return html

def generar_seccion_mangas():
    """
    Genera HTML seccion todos los mangas
    Grid responsive con portadas
    """
    mangas = db.get_all_manga()
    
    # Separar por tracking
    tracked = [m for m in mangas if m.get('tracking') == 1]
    untracked = [m for m in mangas if m.get('tracking') == 0]
    
    html = '<section id="seccion-mangas" class="card">\n'
    html += '  <div class="card-header">\n'
    html += '    <h2>Biblioteca</h2>\n'
    html += f'    <span class="badge">{len(mangas)}</span>\n'
    html += '  </div>\n'
    
    if mangas:
        # if tracked:
        #     html += '  <div class="manga-section">\n'
        #     html += '    <h3 class="section-title">En Seguimiento</h3>\n'
        #     html += '    <div class="manga-grid">\n'
        #     for m in sorted(tracked, key=lambda x: x['title']):
        #         slug_path = '/mangas/' + m['local_storage_path'].split('mangas/')[-1]
        #         current = m.get('last_checked_chapter', '?')
        #         reading = m.get('current_reading', '?')
        #         portada_path = f'{slug_path}/portada.webp'
                
        #         html += f'      <a href="{slug_path}" class="manga-card tracked">\n'
        #         html += f'        <div class="manga-cover">\n'
        #         html += f'          <img src="{portada_path}" alt="{m["title"]}" onerror="this.src=\'/placeholder.png\'">\n'
        #         html += f'        </div>\n'
        #         html += f'        <div class="manga-info-card">\n'
        #         html += f'          <div class="manga-title">{m["title"]}</div>\n'
        #         html += f'          <div class="chapter-status">Cap. {current}</div>\n'
        #         html += f'          <div class="read-status">Leido: {reading}</div>\n'
        #         html += f'        </div>\n'
        #         html += f'      </a>\n'
        #     html += '    </div>\n'
        #     html += '  </div>\n'
        
        if untracked:
            html += '  <div class="manga-section">\n'
            html += '    <div class="manga-grid">\n'
            for m in sorted(untracked, key=lambda x: x['title']):
                slug_path = '/mangas/' + m['local_storage_path'].split('mangas/')[-1]
                current = m.get('last_checked_chapter', '?')
                reading = m.get('current_reading', '?')
                portada_path = f'{slug_path}/portada.webp'
                
                html += f'      <a href="{slug_path}/" class="manga-card">\n'
                html += f'        <div class="manga-cover">\n'
                html += f'          <img src="{portada_path}" alt="{m["title"]}" onerror="this.src=\'/placeholder.png\'">\n'
                html += f'        </div>\n'
                html += f'        <div class="manga-info-card">\n'
                html += f'          <div class="manga-title">{m["title"]}</div>\n'
                html += f'          <div class="chapter-status">Cap. {current}</div>\n'
                html += f'          <div class="read-status">Leido: {reading}</div>\n'
                html += f'        </div>\n'
                html += f'      </a>\n'
            html += '    </div>\n'
            html += '  </div>\n'
    else:
        html += '  <div class="empty-state">\n'
        html += '    <p>No hay mangas en la biblioteca</p>\n'
        html += '  </div>\n'
    
    html += '</section>\n'
    return html


def generar_index_principal():
    """
    Genera index.html completo con grid responsive de portadas
    """
    print("== GENERANDO INDEX PRINCIPAL ==")
    html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manga Tracker</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px 20px;
            background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #888;
            font-size: 0.9em;
        }
        
        .card {
            background: rgba(22, 33, 62, 0.8);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .card-header h2 {
            font-size: 1.5em;
            color: #fff;
        }
        
        .badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        
        .manga-section {
            margin-bottom: 30px;
        }
        
        .manga-section:last-child {
            margin-bottom: 0;
        }
        
        .section-title {
            color: #888;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 20px;
            padding-left: 10px;
            border-left: 3px solid #667eea;
        }
        
        .manga-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 20px;
        }
        
        .manga-card {
            background: rgba(30, 58, 95, 0.5);
            border-radius: 12px;
            overflow: hidden;
            text-decoration: none;
            color: inherit;
            transition: all 0.3s ease;
            border: 2px solid transparent;
            display: flex;
            flex-direction: column;
        }
        
        .manga-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 24px rgba(102, 126, 234, 0.4);
            border-color: #667eea;
        }
        
        .manga-card.tracked {
            border-color: rgba(16, 185, 129, 0.3);
        }
        
        .manga-cover {
            position: relative;
            width: 100%;
            padding-top: 140%;
            background: #1a1a2e;
            overflow: hidden;
        }
        
        .manga-cover img {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .new-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            background: #f43f5e;
            color: white;
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 0.75em;
            font-weight: bold;
            box-shadow: 0 2px 8px rgba(244, 63, 94, 0.4);
        }
        
        .manga-info-card {
            padding: 15px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }
        
        .manga-title {
            font-size: 0.95em;
            font-weight: 600;
            color: #fff;
            margin-bottom: 8px;
            line-height: 1.3;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .chapter-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }
        
        .current {
            color: #a0aec0;
            font-size: 0.85em;
        }
        
        .diff {
            background: #f43f5e;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.75em;
            font-weight: bold;
        }
        
        .read-progress {
            color: #667eea;
            font-size: 0.8em;
        }
        
        .chapter-status {
            color: #a0aec0;
            font-size: 0.85em;
            margin-bottom: 3px;
        }
        
        .read-status {
            color: #667eea;
            font-size: 0.8em;
        }
        
        .no-tracking {
            color: #888;
            font-size: 0.8em;
            font-style: italic;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #666;
        }
        
        .empty-state p {
            font-size: 1.1em;
        }
        
        /* Tablet */
        @media (max-width: 1024px) {
            .manga-grid {
                grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
                gap: 15px;
            }
        }
        
        /* Mobile */
        @media (max-width: 768px) {
            h1 {
                font-size: 1.8em;
            }
            
            .manga-grid {
                grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
                gap: 12px;
            }
            
            .card {
                padding: 20px;
            }
            
            .manga-title {
                font-size: 0.85em;
            }
        }
        
        /* Small mobile */
        @media (max-width: 480px) {
            .manga-grid {
                grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
                gap: 10px;
            }
            
            .manga-info-card {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>MANGA TRACKER</h1>
            <p class="subtitle">Tu biblioteca personal de manga</p>
        </header>
'''
    
    html += '        ' + generar_seccion_seguimiento()
    html += '        ' + generar_seccion_pendientes()
    html += '        ' + generar_seccion_mangas()
    
    html += '''    </div>
</body>
</html>
'''
    return html

def regenerar_seccion_seguimiento():
    """
    Actualiza solo seccion seguimiento en index.html existente
    """
    index_path = os.path.join(base_dir, 'index.html')
    
    if not os.path.exists(index_path):
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(generar_index_principal())
        return
    
    with open(index_path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    nueva_seccion = generar_seccion_seguimiento()
    
    import re
    patron = r'<section id="seccion-seguimiento".*?</section>'
    nuevo_contenido = re.sub(patron, nueva_seccion.strip(), contenido, flags=re.DOTALL)
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(nuevo_contenido)

def regenerar_seccion_mangas():
    """
    Actualiza solo seccion mangas en index.html existente
    """
    index_path = os.path.join(base_dir, 'index.html')
    
    if not os.path.exists(index_path):
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(generar_index_principal())
        return
    
    with open(index_path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    nueva_seccion = generar_seccion_mangas()
    
    import re
    patron = r'<section id="seccion-mangas".*?</section>'
    nuevo_contenido = re.sub(patron, nueva_seccion.strip(), contenido, flags=re.DOTALL)
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(nuevo_contenido)
        
def regenerar_seccion_pendientes():
    """Actualiza solo seccion pendientes en index.html existente"""
    index_path = os.path.join(base_dir, 'index.html')
    
    if not os.path.exists(index_path):
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(generar_index_principal())
        return
    
    with open(index_path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    nueva_seccion = generar_seccion_pendientes()
    
    import re
    patron = r'<section id="seccion-pendientes".*?</section>'
    nuevo_contenido = re.sub(patron, nueva_seccion.strip(), contenido, flags=re.DOTALL)
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(nuevo_contenido)