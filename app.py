import flet as ft
import os
import sys
import subprocess
import threading
import re
from yt_dlp import YoutubeDL

escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
carpeta_salida = os.path.join(escritorio, "YTdownloader")
os.makedirs(carpeta_salida, exist_ok=True)
ruta_salida = os.path.join(carpeta_salida, '%(title)s [%(id)s].%(ext)s')

youtube_regex = re.compile(r'(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+')

traducciones = {
    "es": {
        "titulo": "🎬 YTDownloader por Gabriel",
        "url_label": "URL de YouTube",
        "calidad_label": "Calidad de video",
        "descargar": "⬇ Descargar",
        "abrir_carpeta": "📁 Abrir carpeta de descargas",
        "url_vacia": "❌ La URL está vacía.",
        "url_invalida": "❌ La URL no es válida.",
        "iniciando_descarga": "Iniciando descarga ({})...",
        "descargando": "⏳ {:.1f}% | {} de {} @ {}",
        "descarga_completada": "✅ ¡Descarga completada!",
        "error_descarga": "❌ Error: {}",
        "no_abrir_carpeta": "❌ No se pudo abrir la carpeta: {}",
        "idioma_label": "Idioma",
        "historial_label": "Historial de descargas"
    },
    "en": {
        "titulo": "🎬 YTDownloader by Gabriel",
        "url_label": "YouTube URL",
        "calidad_label": "Video quality",
        "descargar": "⬇ Download",
        "abrir_carpeta": "📁 Open download folder",
        "url_vacia": "❌ URL is empty.",
        "url_invalida": "❌ URL is not valid.",
        "iniciando_descarga": "Starting download ({})...",
        "descargando": "⏳ {:.1f}% | {} of {} @ {}",
        "descarga_completada": "✅ Download completed!",
        "error_descarga": "❌ Error: {}",
        "no_abrir_carpeta": "❌ Could not open folder: {}",
        "idioma_label": "Language",
        "historial_label": "Download history"
    }
}

def main(page: ft.Page):
    idioma_actual = "es"
    page.title = traducciones[idioma_actual]["titulo"]
    page.scroll = "auto"
    page.theme_mode = "light"
    page.window_width = 500
    page.window_height = 700

    titulo = ft.Text(traducciones[idioma_actual]["titulo"], size=22, weight="bold", text_align="center")
    entrada = ft.TextField(label=traducciones[idioma_actual]["url_label"], width=400, text_align="center")
    calidad_selector = ft.Dropdown(
        width=200,
        label=traducciones[idioma_actual]["calidad_label"],
        options=[
            ft.dropdown.Option("1080p"),
            ft.dropdown.Option("720p"),
            ft.dropdown.Option("480p"),
            ft.dropdown.Option("Solo audio MP3")
        ],
        value="1080p"
    )
    progreso_bar = ft.ProgressBar(width=400, value=0)
    estado = ft.Text(text_align="center")
    historial = ft.ListView(height=150, spacing=10, auto_scroll=True)
    historial_titulo = ft.Text(traducciones[idioma_actual]["historial_label"], weight="bold")

    idioma_selector = ft.Dropdown(
        width=150,
        label=traducciones[idioma_actual]["idioma_label"],
        options=[
            ft.dropdown.Option("es"),
            ft.dropdown.Option("en")
        ],
        value=idioma_actual
    )

    def traducir():
        page.title = traducciones[idioma_actual]["titulo"]
        titulo.value = traducciones[idioma_actual]["titulo"]
        entrada.label = traducciones[idioma_actual]["url_label"]
        calidad_selector.label = traducciones[idioma_actual]["calidad_label"]
        descargar_btn.text = traducciones[idioma_actual]["descargar"]
        abrir_carpeta_btn.text = traducciones[idioma_actual]["abrir_carpeta"]
        idioma_selector.label = traducciones[idioma_actual]["idioma_label"]
        historial_titulo.value = traducciones[idioma_actual]["historial_label"]
        page.update()

    def limpiar():
        entrada.value = ""
        progreso_bar.value = 0
        estado.value = ""
        page.update()

    def format_bytes(b):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if b < 1024:
                return f"{b:.2f} {unit}"
            b /= 1024
        return f"{b:.2f} TB"

    def format_speed(bps):
        return f"{format_bytes(bps)}/s"

    def hook_factory():
        def hook(d):
            if d['status'] == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
                speed = d.get('speed') or 0
                porcentaje = (downloaded / total) * 100

                try:
                    progreso_bar.value = porcentaje / 100
                    estado.value = traducciones[idioma_actual]["descargando"].format(
                        porcentaje,
                        format_bytes(downloaded),
                        format_bytes(total),
                        format_speed(speed)
                    )
                except Exception as err:
                    print(f"[Hook error] {err}")
                page.update()

            elif d['status'] == 'finished':
                progreso_bar.value = 1
                estado.value = traducciones[idioma_actual]["descarga_completada"]
                page.update()
                threading.Timer(3, limpiar).start()
        return hook

    def descargar(e):
        url = entrada.value.strip()
        if not url:
            estado.value = traducciones[idioma_actual]["url_vacia"]
            page.update()
            return
        if not youtube_regex.match(url):
            estado.value = traducciones[idioma_actual]["url_invalida"]
            page.update()
            return

        seleccion = calidad_selector.value
        progreso_bar.value = 0
        estado.value = traducciones[idioma_actual]["iniciando_descarga"].format(seleccion)
        page.update()

        def proceso():
            opciones = {
                'outtmpl': ruta_salida,
                'progress_hooks': [hook_factory()]
            }

            if seleccion == "Solo audio MP3":
                opciones.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                })
            elif seleccion == "1080p":
                opciones['format'] = 'bestvideo[height<=1080]+bestaudio/best'
            elif seleccion == "720p":
                opciones['format'] = 'bestvideo[height<=720]+bestaudio/best'
            elif seleccion == "480p":
                opciones['format'] = 'bestvideo[height<=480]+bestaudio/best'

            try:
                with YoutubeDL(opciones) as ydl:
                    info = ydl.extract_info(url, download=True)
                    titulo_video = info.get('title', 'Video')
                    historial.controls.append(ft.Text(f"✅ {titulo_video} ({seleccion})"))
                    page.update()
                    try:
                        if sys.platform == 'win32':
                            import winsound
                            winsound.MessageBeep()
                        else:
                            print('\a')
                    except:
                        pass
            except Exception as e:
                estado.value = traducciones[idioma_actual]["error_descarga"].format(str(e))
                page.update()

        threading.Thread(target=proceso).start()

    def abrir_carpeta(e):
        try:
            if sys.platform == 'win32':
                os.startfile(carpeta_salida)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', carpeta_salida])
            else:
                subprocess.Popen(['xdg-open', carpeta_salida])
        except Exception as e:
            estado.value = traducciones[idioma_actual]["no_abrir_carpeta"].format(str(e))
            page.update()

    def cambiar_idioma(e):
        nonlocal idioma_actual
        idioma_actual = idioma_selector.value
        traducir()

    descargar_btn = ft.ElevatedButton(traducciones[idioma_actual]["descargar"], on_click=descargar, width=220)
    abrir_carpeta_btn = ft.ElevatedButton(traducciones[idioma_actual]["abrir_carpeta"], on_click=abrir_carpeta, width=220)
    idioma_selector.on_change = cambiar_idioma

    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    titulo,
                    entrada,
                    calidad_selector,
                    descargar_btn,
                    progreso_bar,
                    estado,
                    abrir_carpeta_btn,
                    historial_titulo,
                    historial,
                    idioma_selector
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15
            ),
            alignment=ft.alignment.center,
            padding=20
        )
    )


ft.app(target=main, view=ft.WEB_BROWSER, port=8080)