#!/bin/bash

# Obtener el directorio donde esta el script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Directorio raiz del proyecto (parent de server/)
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

BOT_CONFIG="$PROJECT_DIR/.bot_config"
if [ -f "$BOT_CONFIG" ]; then
    BOT_TOKEN=$(cat "$BOT_CONFIG")
else
    BOT_TOKEN=""
fi

echo "Parando cualquier proceso en el puerto 8000..."
sudo fuser -k 8000/tcp 2>/dev/null
sleep 1

# Cambiar al directorio raiz del proyecto
cd "$PROJECT_DIR" || {
    echo "Error: No se encuentra el directorio del proyecto"
    exit 1
}

echo "Generando index.html principal..."
python3 -c "
import sys
sys.path.insert(0, '.')
from server.server_utils import generar_index_principal
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(generar_index_principal())
print('Index principal generado')
"

echo "Iniciando servidor de manga..."
python3 server/server.py &
SERVIDOR_PID=$!
sleep 2

echo "Iniciando Cloudflare Tunnel..."
echo "Esperando URL del tunel..."

# Capturar solo la URL de cloudflared
cloudflared tunnel --url http://localhost:8000 2>&1 | while read -r line; do
    # Buscar la linea que contiene la URL
    if [[ $line =~ https://[a-zA-Z0-9.-]+\.trycloudflare\.com ]]; then
        URL="${BASH_REMATCH[0]}"
        echo ""
        echo "=========================================="
        echo "Tu servidor esta disponible en:"
        echo "$URL"
        echo "=========================================="
        echo ""
        
        if [ -n "$BOT_TOKEN" ]; then
            curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
                -d chat_id=114203979 \
                -d text="Servidor manga activo:%0A$URL" > /dev/null
        fi
    fi
done &

CLOUDFLARED_PID=$!

# Funcion para limpiar procesos al salir
cleanup() {
    echo ""
    echo "Cerrando servicios..."
    kill $CLOUDFLARED_PID 2>/dev/null
    kill $SERVIDOR_PID 2>/dev/null
    exit 0
}

# Capturar Ctrl+C para limpieza
trap cleanup SIGINT SIGTERM

# Esperar indefinidamente
wait