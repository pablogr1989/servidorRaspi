import os
import re
from database.db_manager import DatabaseManager

TEMPLATE_PATH = '/home/pablopi/Server/ServerManga/templates/capitulo_template.html'

def leer_template():
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def extraer_numero_capitulo(filename):
    """Extrae numero de capitulo sin .00 decimales"""
    match = re.search(r'capitulo_(\d+(?:\.\d+)?)', filename)
    if not match:
        return None
    
    num_str = match.group(1)
    
    # Si tiene decimales
    if '.' in num_str:
        partes = num_str.split('.')
        if partes[1] == '00':
            return partes[0]  # Sin decimales
        else:
            # Eliminar ceros trailing
            decimal = partes[1].rstrip('0')
            return f"{partes[0]}.{decimal}" if decimal else partes[0]
    
    return num_str

def listar_capitulos(contenido_dir):
    """Lista capitulos en orden ascendente"""
    if not os.path.exists(contenido_dir):
        return []
    
    archivos = [f for f in os.listdir(contenido_dir) 
                if f.startswith('capitulo_') and f.endswith('.html')]
    
    def sort_key(filename):
        num = extraer_numero_capitulo(filename)
        if num is None:
            return 0
        try:
            return float(num)
        except:
            return 0
    
    return sorted(archivos, key=sort_key)

def extraer_imagenes(html_path):
    """Extrae imagenes del HTML existente"""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    images = []
    img_pattern = r'<img[^>]*src="(raw_Capitulo_\d+[^"]+)"[^>]*>'
    for match in re.finditer(img_pattern, content):
        images.append(match.group(1))
    
    return images

def generar_html(template, manga_id, manga_title, chapter_num, images, prev_file, next_file):
    """Genera HTML con template"""
    images_html = ''
    for img in images:
        images_html += f'        <img src="{img}" alt="Pagina" loading="lazy">\n'
    
    html = template.replace('{{MANGA_TITLE}}', manga_title)
    html = html.replace('{{CHAPTER_NUM}}', str(chapter_num))
    html = html.replace('{{MANGA_ID}}', str(manga_id))
    html = html.replace('{{IMAGES}}', images_html)
    html = html.replace('{{PREV_CHAPTER}}', prev_file if prev_file else '#')
    html = html.replace('{{NEXT_CHAPTER}}', next_file if next_file else '#')
    html = html.replace('{{PREV_DISABLED}}', '' if prev_file else 'disabled')
    html = html.replace('{{NEXT_DISABLED}}', '' if next_file else 'disabled')
    
    return html

def recrear_capitulos_manga(manga, template):
    """Recrea todos los capitulos de un manga"""
    manga_id = manga['id']
    manga_title = manga['title']
    local_path = manga['local_storage_path']
    contenido_dir = os.path.join(local_path, 'contenido')
    
    print(f"\n[PROCESANDO] {manga_title} (ID: {manga_id})")
    print(f"  Path: {local_path}")
    
    capitulos = listar_capitulos(contenido_dir)
    
    if not capitulos:
        print(f"  [SKIP] Sin capitulos")
        return 0
    
    print(f"  Capitulos encontrados: {len(capitulos)}")
    
    actualizados = 0
    errores = []
    
    for idx, cap_file in enumerate(capitulos):
        cap_path = os.path.join(contenido_dir, cap_file)
        chapter_num = extraer_numero_capitulo(cap_file)
        
        if chapter_num is None:
            errores.append(f"No se pudo extraer numero de: {cap_file}")
            continue
        
        # Determinar prev/next
        prev_file = None
        next_file = None
        
        if idx > 0:
            prev_file = capitulos[idx - 1]
            # Validar existencia
            if not os.path.exists(os.path.join(contenido_dir, prev_file)):
                errores.append(f"[{manga_title}] Cap {chapter_num}: Prev no existe: {prev_file}")
                prev_file = None
        
        if idx < len(capitulos) - 1:
            next_file = capitulos[idx + 1]
            # Validar existencia
            if not os.path.exists(os.path.join(contenido_dir, next_file)):
                errores.append(f"[{manga_title}] Cap {chapter_num}: Next no existe: {next_file}")
                next_file = None
        
        try:
            # Extraer imagenes del HTML actual
            images = extraer_imagenes(cap_path)
            
            if not images:
                errores.append(f"[{manga_title}] Cap {chapter_num}: Sin imagenes")
                continue
            
            # Generar nuevo HTML
            nuevo_html = generar_html(
                template, manga_id, manga_title, chapter_num,
                images, prev_file, next_file
            )
            
            # Escribir
            with open(cap_path, 'w', encoding='utf-8') as f:
                f.write(nuevo_html)
            
            actualizados += 1
            
        except Exception as e:
            errores.append(f"[{manga_title}] Cap {chapter_num}: {e}")
    
    print(f"  [OK] {actualizados}/{len(capitulos)} actualizados")
    
    if errores:
        print(f"  [ERRORES] {len(errores)}:")
        for err in errores:
            print(f"    - {err}")
    
    return actualizados

def main():
    print("=" * 70)
    print("RECREACION DE CAPITULOS DESDE BASE DE DATOS")
    print("=" * 70)
    
    if not os.path.exists(TEMPLATE_PATH):
        print(f"[ERROR] Template no existe: {TEMPLATE_PATH}")
        return
    
    template = leer_template()
    
    db = DatabaseManager()
    mangas = db.get_all_manga()
    
    print(f"\nMangas en BD: {len(mangas)}")
    
    confirmacion = input("\nContinuar? (s/n): ").lower()
    if confirmacion != 's':
        print("Operacion cancelada")
        return
    
    total = 0
    for manga in mangas:
        total += recrear_capitulos_manga(manga, template)
    
    print("\n" + "=" * 70)
    print(f"TOTAL CAPITULOS RECREADOS: {total}")
    print("=" * 70)

if __name__ == '__main__':
    main()