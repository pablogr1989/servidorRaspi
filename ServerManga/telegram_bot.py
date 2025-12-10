#!/usr/bin/env python3
import os
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Tu token del bot
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8451965289:AAGzKJhsIxPXljNfbL9mxtLnHtxC5JvmLWg')
# Tu chat_id autorizado (para seguridad)
AUTHORIZED_CHAT_ID = 114203979

# Ruta base de tus scripts
BASE_PATH = '/home/pablopi/Server/ServerManga'

# Comandos permitidos (lista blanca por seguridad)
ALLOWED_COMMANDS = {
    'actualizar': f'{BASE_PATH}/servicios/actualizar_slugs.sh',
    'descargar' : f'{BASE_PATH}/servicios/bot_functions_script.sh',
    'descargar_olympus_com': f'{BASE_PATH}/servicios/bot_functions_script.sh descargar_olympus_com',
    'descargar_olympus_net': f'{BASE_PATH}/servicios/bot_functions_script.sh descargar_olympus_net',
    'descargar_tmo': f'{BASE_PATH}/servicios/bot_functions_script.sh descargar_tmo',
    'descargar_allstar': f'{BASE_PATH}/servicios/bot_functions_script.sh descargar_animeallstar',
    'descargar_menos_olympus_com': f'{BASE_PATH}/servicios/bot_functions_script.sh descargar_menos_olympus_com',
    'descargar_manga': f'{BASE_PATH}/servicios/bot_functions_script.sh descargar_manga_por_id',
    'listar_mangas' : f'{BASE_PATH}/servicios/bot_functions_script.sh print_all_manga',
    'diaria' : f'{BASE_PATH}/servicios/tarea_diaria.sh',
    'regenerar': f'{BASE_PATH}/servicios/regenerar_web.sh',
    'iniciar': 'sudo systemctl start manga-server',
    'apagar': 'sudo systemctl stop manga-server',
    'reiniciar': 'sudo systemctl restart manga-server',
    'status': 'systemctl status manga-server --no-pager',
    'uptime': 'uptime',
    'disk': 'df -h',
    'temp': 'vcgencmd measure_temp',
    'ps': f'ps aux | grep -E "(python|ServerManga)" | grep -v grep',
    'logs': 'journalctl -u manga-server -n 30 --no-pager',
    'help' : f'{BASE_PATH}/servicios/bot_functions_script.sh help',
    'ultimo_log' : f'{BASE_PATH}/servicios/bot_functions_script.sh get_latest_log',
    'encender_nordvpn' : f'{BASE_PATH}/servicios/bot_functions_script.sh openNordVPN',
    'apagar_nordvpn' : f'{BASE_PATH}/servicios/bot_functions_script.sh closeNordVPN',
    'status_nordvpn' : f'{BASE_PATH}/servicios/bot_functions_script.sh statusNordVPN',
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    if update.effective_chat.id != AUTHORIZED_CHAT_ID:
        await update.message.reply_text("No autorizado.")
        return
    
    comandos = "\n".join([f"/{cmd}" for cmd in ALLOWED_COMMANDS.keys()])
    await update.message.reply_text(
        f"🤖 Bot de control del servidor manga\n\n"
        f"Comandos disponibles:\n{comandos}"
    )

async def ejecutar_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta un comando del sistema"""
    # Verificar autorización
    if update.effective_chat.id != AUTHORIZED_CHAT_ID:
        await update.message.reply_text("❌ No autorizado.")
        return
    
    # Obtener el comando solicitado
    parts = update.message.text.strip().split(maxsplit=2)
    comando_nombre = parts[0][1:]  # quitar "/"
    parametro = parts[1] if len(parts) > 1 else ""
    
    if comando_nombre not in ALLOWED_COMMANDS:
        await update.message.reply_text(f"❌ Comando '{comando_nombre}' no permitido.")
        return
    
    comando_base = ALLOWED_COMMANDS[comando_nombre]
    comando_completo = f"{comando_base} {parametro}" if parametro else comando_base

    
    try:
        # Para el comando 'iniciar', ejecutar completamente desacoplado
        if comando_nombre == 'iniciar':
            # Matar sesión previa si existe
            subprocess.run('screen -S manga-server -X quit', shell=True, stderr=subprocess.DEVNULL)
            # Ejecutar en screen con setsid para desacoplar completamente
            subprocess.Popen(
                f'setsid screen -dmS manga-server bash -c "{comando_completo}"',
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setpgrp  # Crea un nuevo grupo de procesos
            )
            await update.message.reply_text("✅ Servidor iniciado en sesión screen 'manga-server'")
            return
        
        # Para otros comandos, ejecutar normalmente
        resultado = subprocess.run(
            comando_completo,
            shell=True,
            capture_output=True,
            text=True,
            timeout=99999
        )

        # Si la salida es muy larga, enviar como archivo
        output = resultado.stdout + resultado.stderr
        if len(output) > 4000:
            temp_file = f'/tmp/telegram_output_{comando_nombre}.txt'  # CAMBIAR command -> comando_nombre
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(output)
            
            # Enviar archivo
            await update.message.reply_document(document=open(temp_file, 'rb'))            
            os.remove(temp_file)
        else:
            await update.message.reply_text(output if output else "Comando ejecutado sin salida")
        
    except subprocess.TimeoutExpired:
        await update.message.reply_text("⏱️ Timeout: el comando tardó demasiado")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    """Función principal"""
    # Crear la aplicación
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Agregar handlers
    application.add_handler(CommandHandler("start", start))
    
    # Agregar un handler para cada comando permitido
    for comando in ALLOWED_COMMANDS.keys():
        application.add_handler(CommandHandler(comando, ejecutar_comando))
    
    # Iniciar el bot
    print("🤖 Bot iniciado. Esperando comandos...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()