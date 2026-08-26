from typing import Callable
import flet as ft
from . import query

def generate_keys(group_count: int, init_btn: Callable[[ft.Button, int], None]) -> tuple[list[ft.Button], list[ft.Button]]:
    count = group_count * 12
    white = []
    void = lambda: ft.Text('', expand=1)
    black = [void() for _ in range(2)]
    gen = ([1, 4, 1, 1, 4][i % 5] for i in range((count // 12 + 1) * 21))
    for i in range(count):
        name = query.note_name(i % 12)
        if '#' in name:
            btn = ft.Button(
                content=ft.Container(
                    alignment=ft.Alignment.BOTTOM_CENTER,
                    expand=True
                ),
                bgcolor=ft.Colors.BLACK_87,
                color=ft.Colors.WHITE,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=0),
                ),
                margin=ft.Margin.all(-5),
                expand=2
            )
            init_btn(btn, i)
            black.append(btn)
            black.extend(void() for _ in range(next(gen)))
        else:
            btn = ft.Button(
                content=ft.Container(
                    content=ft.Text(name),
                    alignment=ft.Alignment.BOTTOM_CENTER,
                    expand=True
                ),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=0),
                ),
                margin=ft.Margin.all(-5),
                expand=1
            )
            init_btn(btn, i)
            white.append(btn)
    return white, black[:-2]

def init_keyboard(keyboard: ft.Container, init_btn: Callable[[ft.Button, int], None]):
    white_keys, black_keys = generate_keys(3, init_btn)
    stack = ft.Stack([
        ft.Row(white_keys, expand=True),
        ft.Column([ft.Row(black_keys, expand=2, height=50), ft.Text(expand=1)], expand=True)
    ], expand=True)
    keyboard.content = stack
