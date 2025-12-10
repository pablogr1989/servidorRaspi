import os
import re
from pathlib import Path

BASE_DIR = Path("mangas")

# --- Función para convertir capítulos a numérico para ordenar ---
def chapter_key(filename):
    num = filename.replace("capitulo_", "").replace(".html", "")
    try:
        return float(num)
    except:
        return float("inf")

# --- Procesar cada manga ---
for manga_dir in BASE_DIR.iterdir():
    contenido = manga_dir / "contenido"
    if not contenido.exists():
        continue

    # Encontrar todos capítulos HTML
    html_files = sorted(
        [f for f in contenido.glob("capitulo_*.html")],
        key=lambda x: chapter_key(x.name)
    )

    if not html_files:
        continue

    print(f"\n📘 Procesando manga: {manga_dir.name}")
    chapters = [f.name for f in html_files]

    # Mapa de capítulo → anterior/siguiente
    prev_next = {}
    for idx, chap in enumerate(chapters):
        prev_chap = chapters[idx - 1] if idx > 0 else "#"
        next_chap = chapters[idx + 1] if idx < len(chapters) - 1 else "#"
        prev_next[chap] = (prev_chap, next_chap)

    # --- Modificar cada archivo HTML ---
    for chap_file in html_files:
        chap_name = chap_file.name
        prev_chap, next_chap = prev_next[chap_name]

        text = chap_file.read_text(encoding="utf-8")

        # -------------------------
        # 1. ARREGLAR BOTONES HTML
        # -------------------------
        # Anterior
        if prev_chap == "#":
            new_prev_btn = "<button onclick=\"location.href='#'\" disabled>◀ Anterior</button>"
        else:
            new_prev_btn = f"<button onclick=\"location.href='{prev_chap}'\">◀ Anterior</button>"

        text = re.sub(
            r"<button onclick=\"location\.href='[^']*'\"(?: disabled)?>◀ Anterior</button>",
            new_prev_btn,
            text
        )

        # Siguiente
        if next_chap == "#":
            new_next_btn = "<button onclick=\"location.href='#'\" disabled>Siguiente ▶</button>"
        else:
            new_next_btn = f"<button onclick=\"location.href='{next_chap}'\">Siguiente ▶</button>"

        text = re.sub(
            r"<button onclick=\"location\.href='[^']*'\"(?: disabled)?>Siguiente ▶</button>",
            new_next_btn,
            text
        )

        # ---------------------------------
        # 2. ARREGLAR NAVEGACIÓN POR TECLADO
        # ---------------------------------
        new_script = (
            f"document.addEventListener('keydown', (e) => {{\n"
            f"            if (e.key === 'ArrowLeft' && '{prev_chap}' !== '#') {{\n"
            f"                location.href = '{prev_chap}';\n"
            f"            }} else if (e.key === 'ArrowRight' && '{next_chap}' !== '#') {{\n"
            f"                location.href = '{next_chap}';\n"
            f"            }} else if (e.key === 'Home') {{\n"
            f"                location.href = '/';\n"
            f"            }}\n"
            f"        }});"
        )

        text = re.sub(
            r"document\.addEventListener\([\s\S]*?}\);",
            new_script,
            text
        )

        # Guardar si hubo cambios
        chap_file.write_text(text, encoding="utf-8")
        print(f"✔ Arreglado: {chap_name}")

print("\n🎉 Proceso completado.")
