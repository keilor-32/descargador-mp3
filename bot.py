        import os
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
        from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

        TOKEN = os.getenv("BOT_TOKEN")  # Añade BOT_TOKEN en Render (Environment variables)
        WEBAPP_URL = "https://tu-app-en-render.onrender.com"  # Reemplaza por tu URL cuando despliegues

        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            keyboard = [
                [InlineKeyboardButton("🎧 Abrir descargador", web_app=WebAppInfo(url=WEBAPP_URL))]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "👋 Hola — soy el bot descargador.

Pulsa el botón para abrir la mini app y descargar MP3 o MP4.",
                reply_markup=reply_markup
            )

        def main():
            if TOKEN is None:
                print("ERROR: La variable de entorno BOT_TOKEN no está configurada.")
                return
            app = ApplicationBuilder().token(TOKEN).build()
            app.add_handler(CommandHandler("start", start))
            print("Bot iniciado. Esperando mensajes...")
            app.run_polling()

        if __name__ == '__main__':
            main()
