from flask import Flask, render_template, request, send_file, redirect, url_for
import yt_dlp
import os, uuid, pathlib, shutil

app = Flask(__name__)

TMP_DIR = "/tmp/descargador_mp3"
os.makedirs(TMP_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url', '').strip()
    formato = request.form.get('formato', 'mp3').lower()

    if not url or "youtube.com" not in url and "youtu.be" not in url:
        return "❌ Enlace no válido. Usa un enlace de YouTube."

    file_id = str(uuid.uuid4())
    out_template = os.path.join(TMP_DIR, f"{file_id}.%(ext)s")
    output_mp3 = os.path.join(TMP_DIR, f"{file_id}.mp3")
    output_mp4 = os.path.join(TMP_DIR, f"{file_id}.mp4")

    # Opciones base
    ydl_opts = {
        'outtmpl': out_template,
        'quiet': True,
        'noplaylist': True,
    }

    try:
        if formato == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })
        else:  # mp4 (video)
            ydl_opts.update({
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Encontrar archivo generado
        if formato == 'mp3' and os.path.exists(output_mp3):
            return send_file(output_mp3, as_attachment=True, download_name="audio.mp3")
        else:
            # buscar .mp4 si existe
            # yt-dlp puede generar varios nombres (ext variable), buscamos por prefix file_id
            candidates = list(pathlib.Path(TMP_DIR).glob(f"{file_id}.*"))
            mp4_candidate = None
            for c in candidates:
                if c.suffix.lower() == '.mp4':
                    mp4_candidate = str(c)
                    break
            if formato == 'mp4' and mp4_candidate and os.path.exists(mp4_candidate):
                return send_file(mp4_candidate, as_attachment=True, download_name="video.mp4")

        return "⚠️ No se pudo generar el archivo. Es posible que el video tenga restricciones de edad o región."

    except Exception as e:
        err = str(e)
        if 'Sign in' in err or 'age' in err:
            return "⚠️ Este video parece tener restricciones (edad / inicio de sesión). No se puede descargar."
        return f"❌ Error al procesar: {err}"

@app.route('/health')
def health():
    return "OK"

# Limpieza periódica simple: al iniciar, eliminar archivos antiguos (mayores a 1 hora)
def cleanup_tmp():
    import time
    cutoff = time.time() - 3600
    for p in pathlib.Path(TMP_DIR).iterdir():
        try:
            if p.stat().st_mtime < cutoff:
                if p.is_file():
                    p.unlink()
                else:
                    shutil.rmtree(p)
        except Exception:
            pass

cleanup_tmp()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
