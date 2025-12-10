#!/bin/bash

# Obtener el directorio donde esta el script (servicios/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Directorio raiz del proyecto (parent de servicios/)
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

sleep 2

echo "Generando index.html principal..."
python3 -c "
import sys
import os
sys.path.insert(0, '$PROJECT_DIR')
from server.server_utils import generar_index_principal

index_path = os.path.join('$PROJECT_DIR', 'index.html')
print(f'Ruta absoluta: {index_path}')

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(generar_index_principal())
print('Index principal generado')
"

exit