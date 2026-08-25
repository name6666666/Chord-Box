import asyncio
from importlib.resources import files
from pathlib import Path
import flet as ft
from ..show_error import show_error
try:
    from pyswip import Prolog
except Exception as e:
    show_error(str(e))


if not Path('harmony.qlf').is_file():
    try:
        public = {'count': 0, 'total': 4}
        tmp_prolog = Prolog()
        @tmp_prolog.register_foreign
        def py_counter():
            public['count'] += 1
            public['update']()
            print(f'Compiling prolog: {public["count"]}/{public['total']}')
            return True
        tmp_pl = Path('harmony.pl')
        tmp_pl.write_bytes(Path(str(files('chord_box.query') / 'harmony.pl')).read_bytes())
        def qcompile():
            for _ in tmp_prolog.query("qcompile('harmony.pl')"):
                pass

        async def tmp_page(page: ft.Page):
            page.window.icon = str(files('chord_box') / 'chord_box.ico')
            page.title = '编译prolog中'
            page.add(
                ft.Column([
                    ft.Container(
                        ft.ProgressRing(align=ft.Alignment.BOTTOM_CENTER, width=100, height=100, stroke_width=8),
                        expand=1
                    ),
                    ft.Container(
                        text := ft.Text(align=ft.Alignment.TOP_CENTER, size=30, text_align=ft.TextAlign.CENTER),
                        expand=1
                    )
                ], expand=True)
            )
            loop = asyncio.get_running_loop()
            public['update'] = lambda: (
                setattr(text, 'value', f'{public["count"]}/{public['total']}\n初次启动，编译prolog文件中...'),
                loop.call_soon_threadsafe(page.update)
            )
            public['update']()
            complete = False
            def on_close(): nonlocal complete; exit(0) if not complete else None
            page.on_close = on_close
            page.update()
            try:
                await loop.run_in_executor(None, qcompile)
            except Exception:
                pass
            complete = True
            await page.window.close()
        ft.run(tmp_page)
    finally:
        tmp_pl.unlink(True)
    if not Path('harmony.qlf').is_file():
        show_error('编译prolog文件失败')

prolog = Prolog()
prolog.consult('harmony.qlf')

from .predict import *
