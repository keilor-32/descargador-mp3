from flask import Flask, render_template, request, send_file
import os
import yt_dlp
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import threading
import asyncio

app = Flask(__name__)

# --- Página principal ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Descargar desde la web ---
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

# --- BOT TELEGRAM ---
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("👋 ¡Hola! Envíame un enlace de YouTube y te lo descargo en MP3 o MP4.")

async def handle_message(update, context):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("Por favor envíame un enlace válido de YouTube 🎥")
        return

    await update.message.reply_text("Descargando tu video... ⏳")

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
    except Exception as e:
        await update.message.reply_text(f"❌ Error al descargar: {str(e)}")

def iniciar_bot():
    if not BOT_TOKEN:
        print("⚠️ No se ha configurado BOT_TOKEN.")
        return
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot de Telegram iniciado...")
    app_telegram.run_polling()

# --- Ejecutar Flask + Bot juntos ---
if __name__ == "__main__":
    threading.Thread(target=iniciar_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
