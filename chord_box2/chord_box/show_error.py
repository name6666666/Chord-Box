import sys
import flet as ft
from importlib.resources import files

def show_error(message: str):
    async def error(page: ft.Page):
        page.window.icon = str(files('chord_box') / 'chord_box.ico')
        page.title = '错误'
        dialog = ft.AlertDialog(
            ft.Text(message),
            title='错误'
        )
        async def on_dismiss(e = None):
            await page.window.close()
        dialog.on_dismiss = on_dismiss
        page.show_dialog(dialog)
    ft.run(error)
    sys.exit(1)
