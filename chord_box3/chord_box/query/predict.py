from pretty_midi import Instrument, Note, PrettyMIDI
from ..chordbtn import ChordBtn
from . import prolog
import flet as ft
from functools import cache, lru_cache
from ..midi_player import player

def first(code: str):
    gen = prolog.query(code)
    ret = next(gen)
    gen.close()
    return ret

def all(code: str) -> list[dict]:
    return list(prolog.query(code))

@cache
def note_name(num: int):
    if not (0 <= num < 12):
        raise ValueError('0 <= num < 12')
    return first(f"harmony:note_name(N, {num})")['N']


def integrate(lst: list[dict[str, str]], key: str):
    ret: dict[str, list] = {}
    for i in lst:
        val = i[key]
        del i[key]
        i = {k: v for k, v in i.items() if not k.startswith('_')}
        if val in ret:
            ret[val].append(i)
        else:
            ret[val] = [i]
    return ret

def bytes_to_str(lst: list[dict], *keys: str):
    for i in lst:
        for key in keys:
            i[key] = bytes(i[key]).decode()
    return lst

@lru_cache(128)
def __predict(r: int, n: tuple[int]):
    result = all(f'predict(chord({r}, {list(n)}), K, GN, NewTmplR, NewTmplN, NewG)')
    x = integrate(result, 'K')
    x = {k: integrate(bytes_to_str(v, 'GN', 'NewG'), 'GN') for k, v in x.items()}
    return x
def _predict(r: int, n: list[int]):
    r = r % 12
    n = sorted(set(i % 12 for i in n))
    return __predict(r, tuple(n))

@lru_cache(128)
def __reverse(r: int, n: tuple[int]):
    result = all(f'reverse(chord({r}, {list(n)}), K, GN, NewTmplR, NewTmplN, NewG)')
    x = integrate(result, 'K')
    x = {k: integrate(bytes_to_str(v, 'GN', 'NewG'), 'GN') for k, v in x.items()}
    return x
def _reverse(r: int, n: list[int]):
    r = r % 12
    n = sorted(set(i % 12 for i in n))
    return __reverse(r, tuple(n))

@lru_cache(128)
def __connect(r1: int, n1: tuple[int], r2: int, n2: tuple[int]):
    result = all(f'connect(chord({r1}, {list(n1)}), chord({r2}, {list(n2)}), G1, G2, K1, K2, NewG1, NewG2, NewTmplR, NewTmplN)')
    result = bytes_to_str(result, 'G1', 'G2', 'NewG1', 'NewG2')
    x: dict[str, list] = {}
    for i in result:
        key = (i['K1'], i['K2'])
        del i['K1']
        del i['K2']
        if key in x:
            x[key].append(i)
        else:
            x[key] = [i]
    return x
def _connect(r1: int, n1: list[int], r2: int, n2: list[int]):
    r1 = r1 % 12
    n1 = sorted(set(i % 12 for i in n1))
    r2 = r2 % 12
    n2 = sorted(set(i % 12 for i in n2))
    return __connect(r1, tuple(n1), r2, tuple(n2))

def find_order(r, new):
    len_r = len(r)
    set_r = set(r)
    for j in range(7):
        slice = set()
        for k in range(len_r):
            slice.add(new[(j + k) % 7])
        if set_r == slice:
            return (new[j:] + new[:j])[:4]

def on_tmpl_clicked(r: list[int], n: list[int]):
    midi = PrettyMIDI()
    midi.instruments.append(instr := Instrument(0))
    start = n.index(r[0])
    new = []
    for i in range(0, 13, 2):
        new.append(n[(start + i) % 7])
    lst = find_order(r, new)
    if not lst:
        raise ValueError(f'Invalible value {lst}')
    last = None
    for i in lst:
        if last is not None:
            while i < last: i += 12
        instr.notes.append(Note(127, 48 + i, 0, 2))
        last = i
    def inner():
        player.stop_th()
        player.play_th(midi)
    return inner

def on_keybtn_clicked(content: ft.ListView, data: dict, predict: bool):
    def inner():
        content.controls = []
        for k, v in data.items():
            column = ft.Column([
                ft.Text('从' + k + '去往：' if predict else '去往' + k + '从：', expand=1, align=ft.Alignment.CENTER, size=25, weight=ft.FontWeight.BOLD)
            ])
            for i in v:
                column.controls.append(ft.Row(ft.Button(
                    ft.Text(
                        f'{i['NewG']}\n根音：{'  '.join(note_name(i) for i in i['NewTmplR'])}\n组成：{'  '.join(note_name(i) for i in i['NewTmplN'])}',
                        text_align=ft.TextAlign.LEFT,
                        align=ft.Alignment.CENTER_LEFT,
                        expand=True
                    ),
                    expand=True,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0)),
                    margin=ft.Margin.all(5),
                    on_click=on_tmpl_clicked(i['NewTmplR'], i['NewTmplN'])
                ), expand=3))
            content.controls.append(column)
    return inner

def make_ui(data: dict, predict: bool):
    keys = ft.MenuBar(expand=True)
    content = ft.ListView(expand=True)
    def on_click_factory(btn: ft.Button, content: ft.ListView, data: dict, predict: bool):
        def inner():
            btn.bgcolor = ft.Colors.BLACK_12
            ChordBtn.current.key_mark = btn.content
            for i in keys.controls:
                j: ft.Button = i.content
                if j is not btn:
                    j.bgcolor = None
            on_keybtn_clicked(content, data, predict)()
        return inner
    for i in data:
        btn = ft.Button(i, style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=0)
        ), expand=1, margin=ft.Margin.all(-5))
        btn.on_click = on_click_factory(btn, content, data[i], predict)
        if ChordBtn.current.key_mark == i:
            btn.on_click()
        keys.controls.append(ft.SubmenuButton(btn, expand=1, margin=ft.Margin.all(-5)))
    return ft.Column([
        ft.Row(keys, expand=1),
        ft.Container(
            content,
            bgcolor=ft.Colors.BLUE_50,
            border=ft.Border.all(3),
            border_radius=ft.BorderRadius.all(10),
            expand=20
        )
    ], expand=True)

"""AI begin"""
def on_connect_keybtn_clicked(content: ft.ListView, k1: str, k2: str, items: list):
    def inner():
        content.controls = []
        column = ft.Column()
        for i in items:
            column.controls.append(ft.Row(ft.Button(
                ft.Text(
                    f"{i['G1']} →\n{i['NewG1']} | {i['NewG2']} →\n{i['G2']}\n根音：{'  '.join(note_name(j) for j in i['NewTmplR'])}\n组成：{'  '.join(note_name(j) for j in i['NewTmplN'])}",
                    text_align=ft.TextAlign.LEFT,
                    align=ft.Alignment.CENTER_LEFT,
                    expand=True
                ),
                expand=True,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0)),
                margin=ft.Margin.all(5),
                on_click=on_tmpl_clicked(i['NewTmplR'], i['NewTmplN'])
            ), expand=3))
        content.controls.append(column)
    return inner

def make_ui_connect(data: dict):
    keys = ft.MenuBar(expand=True)
    content = ft.ListView(expand=True)
    def on_click_factory(btn: ft.Button, content: ft.ListView, k1: str, k2: str, items: list):
        def inner():
            btn.bgcolor = ft.Colors.BLACK_12
            ChordBtn.current.key_mark = [k1, k2]
            for i in keys.controls:
                j: ft.Button = i.content
                if j is not btn:
                    j.bgcolor = None
            on_connect_keybtn_clicked(content, k1, k2, items)()
        return inner
    for k1, k2 in data:
        btn = ft.Button(f'{k1}→{k2}', style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=0)
        ), expand=1, margin=ft.Margin.all(-5))
        btn.on_click = on_click_factory(btn, content, k1, k2, data[(k1, k2)])
        if ChordBtn.current.key_mark == [k1, k2]:
            btn.on_click()
        keys.controls.append(ft.SubmenuButton(btn, expand=1, margin=ft.Margin.all(-5)))
    return ft.Column([
        ft.Row(keys, expand=1),
        ft.Container(
            content,
            bgcolor=ft.Colors.BLUE_50,
            border=ft.Border.all(3),
            border_radius=ft.BorderRadius.all(10),
            expand=20
        )
    ], expand=True)
"""AI end"""


def predict(area: ft.Container, r: int, n: list[int]):
    data = _predict(r, n)
    area.content = make_ui(data, True)

def reverse(area: ft.Container, r: int, n: list[int]):
    data = _reverse(r, n)
    area.content = make_ui(data, False)

def connect(area: ft.Container, r1: int, n1: list[int], r2: int, n2: list[int]):
    data = _connect(r1, n1, r2, n2)
    area.content = make_ui_connect(data)

def void(area: ft.Container):
    area.content = ft.Text('让和弦块处于有效上下文之中', align=ft.Alignment.CENTER, size=20)
