#!/bin/bash

# Obtener el directorio donde esta el script (servicios/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Directorio raiz del proyecto (parent de servicios/)
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Cambiar al directorio del script
cd "$SCRIPT_DIR" || {
    echo "Error: No se encuentra el directorio servicios"
    exit 1
}

# Añadir project root al path
python3 -c "
import sys
sys.path.insert(0, '..')  # <-- Apuntar al parent (project root)
from bot_functions import actualizar
actualizar()
"

exit