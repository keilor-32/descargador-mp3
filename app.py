from flask import Flask, render_template, request, send_file, Response
import os
import asyncio
import yt_dlp
import requests
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ---------------- CONFIGURACIÓN ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://descargador-mp3.onrender.com")

print("=" * 50)
print("🔧 CONFIGURACIÓN:")
print(f"   BOT_TOKEN: {'✅ Configurado' if BOT_TOKEN else '❌ NO CONFIGURADO'}")
print(f"   WEBAPP_URL: {WEBAPP_URL}")
print("=" * 50)

# ---------------- FLASK ----------------
app = Flask(__name__)

# Crear bot y aplicación
bot = None
bot_app = None

if BOT_TOKEN:
    bot = Bot(token=BOT_TOKEN)
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()

@app.route('/')
def index():
    return "Bot is running!"

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

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint para recibir actualizaciones de Telegram"""
    if not bot_app:
        print("❌ Bot no configurado")
        return Response("Bot not configured", status=500)
    
    try:
        json_data = request.get_json()
        print(f"📩 Webhook recibido: {json_data}")
        
        update = Update.de_json(json_data, bot_app.bot)
        
        # Crear un nuevo event loop para procesar la actualización
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot_app.process_update(update))
        loop.close()
        
        return Response("OK", status=200)
    except Exception as e:
        print(f"❌ Error en webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(f"Error: {str(e)}", status=500)

# ---------------- BOT TELEGRAM ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    print(f"📩 /start recibido de {update.effective_user.username}")
    
    await update.message.reply_text(
        "👋 ¡Hola! Soy el bot descargador de YouTube.\n\n"
        "📝 Envíame un enlace de YouTube y te enviaré el audio en MP3.\n\n"
        "🔗 Ejemplo: https://youtube.com/watch?v=..."
    )
    print("✅ Respuesta enviada")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejo de enlaces directo en el chat"""
    url = update.message.text
    print(f"📩 Mensaje: {url[:50]}...")
    
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text(
            "❌ Por favor, envíame un enlace válido de YouTube"
        )
        return

    await update.message.reply_text("⏳ Descargando audio...")

    try:
        opciones = {
            'format': 'bestaudio/best',
            'outtmpl': 'temp_%(id)s.mp3',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'

        with open(filename, 'rb') as audio_file:
            await update.message.reply_audio(
                audio_file,
                title=info.get('title', 'Audio'),
                performer=info.get('uploader', 'Unknown')
            )
        
        os.remove(filename)
        print("✅ Descarga completada")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        await update.message.reply_text(f"❌ Error al descargar: {str(e)}")

# Registrar handlers
if bot_app:
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Handlers registrados")

def setup_webhook():
    """Configurar el webhook automáticamente"""
    if not BOT_TOKEN:
        print("❌ No se puede configurar webhook sin BOT_TOKEN")
        return
    
    webhook_url = f"{WEBAPP_URL}/webhook"
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    
    try:
        response = requests.post(api_url, json={"url": webhook_url})
        result = response.json()
        
        if result.get("ok"):
            print(f"✅ Webhook configurado: {webhook_url}")
        else:
            print(f"❌ Error configurando webhook: {result}")
    except Exception as e:
        print(f"❌ Error al configurar webhook: {str(e)}")

# ---------------- EJECUCIÓN ----------------
if __name__ == '__main__':
    port = int(os.getenv("PORT", 10000))
    
    print("🌐 Iniciando servidor Flask...")
    print(f"🔗 URL: {WEBAPP_URL}")
    print(f"📡 Webhook: {WEBAPP_URL}/webhook")
    
    # Configurar webhook automáticamente
    setup_webhook()
    
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=False)
