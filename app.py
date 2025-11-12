from flask import Flask, render_template, request, send_file
import os
import threading
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ---------------- CONFIGURACIÓN ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://tu-app.onrender.com")

# Verificar configuración
print("=" * 50)
print("🔧 CONFIGURACIÓN:")
print(f"   BOT_TOKEN: {'✅ Configurado' if BOT_TOKEN else '❌ NO CONFIGURADO'}")
print(f"   WEBAPP_URL: {WEBAPP_URL}")
print("=" * 50)

# ---------------- FLASK ----------------
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/descargar', methods=['POST'])
def descargar():
    url = request.form['url']
    formato = request.form['formato']

    try:
        if formato == 'mp3':
            nombre = 'audio.mp3'
            opciones = {
                'format': 'bestaudio/best',
                'outtmpl': nombre,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        else:
            nombre = 'video.mp4'
            opciones = {'format': 'best', 'outtmpl': nombre}

        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([url])

        return send_file(nombre, as_attachment=True)
    except Exception as e:
        return f"Ocurrió un error: {str(e)}"

# ---------------- BOT TELEGRAM ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start con botón de Mini App"""
    print(f"📩 Comando /start recibido de {update.effective_user.username}")
    
    keyboard = [
        [InlineKeyboardButton("🎧 Abrir descargador", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 ¡Hola! Soy el bot descargador.\n\n"
        "Pulsa el botón para abrir la mini app y descargar MP3 o MP4.",
        reply_markup=reply_markup
    )
    print("✅ Respuesta enviada correctamente")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejo de enlaces directo en el chat (opcional)"""
    url = update.message.text
    print(f"📩 Mensaje recibido: {url[:50]}...")
    
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text(
            "❌ Envíame un enlace válido de YouTube o usa el botón del /start"
        )
        return

    await update.message.reply_text("⏳ Descargando tu video...")

    try:
        opciones = {
            'format': 'bestaudio/best',
            'outtmpl': 'temp.mp3',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([url])

        await update.message.reply_audio(open("temp.mp3", "rb"))
        os.remove("temp.mp3")
        print("✅ Descarga completada")
    except Exception as e:
        print(f"❌ Error en descarga: {str(e)}")
        await update.message.reply_text(f"❌ Error al descargar: {str(e)}")

def iniciar_bot():
    """Inicia el bot de Telegram en un thread separado"""
    if not BOT_TOKEN:
        print("⚠️ ADVERTENCIA: BOT_TOKEN no configurado. El bot NO funcionará.")
        return
    
    try:
        print("🤖 Iniciando bot de Telegram...")
        app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Registrar handlers
        app_bot.add_handler(CommandHandler("start", start))
        app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("✅ Bot configurado correctamente")
        print("🔄 Iniciando polling...")
        
        # Usar polling
        app_bot.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ ERROR AL INICIAR BOT: {str(e)}")

# ---------------- EJECUCIÓN ----------------
if __name__ == '__main__':
    # Iniciar bot en thread separado
    print("🚀 Iniciando servicios...")
    bot_thread = threading.Thread(target=iniciar_bot, daemon=True)
    bot_thread.start()
    
    # Dar tiempo al bot para iniciar
    import time
    time.sleep(2)
    
    # Iniciar Flask
    port = int(os.getenv("PORT", 5000))
    print(f"🌐 Iniciando Flask en puerto {port}...")
    print(f"🔗 Webapp disponible en: http://0.0.0.0:{port}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=False)
