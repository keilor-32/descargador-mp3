from flask import Flask, render_template, request, send_file
import os
import threading
import yt_dlp

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
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! Envíame un enlace de YouTube y te lo descargo en MP3 o MP4.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Envíame un enlace válido de YouTube.")
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
    except Exception as e:
        await update.message.reply_text(f"❌ Error al descargar: {str(e)}")

def iniciar_bot():
    if not BOT_TOKEN:
        print("⚠️ No se ha configurado BOT_TOKEN.")
        return
    print("🤖 Iniciando bot de Telegram...")
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.run_polling(drop_pending_updates=True)

# ---------------- EJECUCIÓN ----------------
def iniciar_todo():
    threading.Thread(target=iniciar_bot, daemon=True).start()

iniciar_todo()
