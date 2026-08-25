import asyncio
import json
from threading import Thread
import flet as ft
from pretty_midi import PrettyMIDI, Instrument, Note
import time
from pathlib import Path
import pystray
from PIL import Image
from importlib.resources import files
from .keyboard import init_keyboard
from .midi_player import player
from .chordbtn import ChordBtn
from . import query



current_page = None
async def main(page: ft.Page):
    global current_page
    current_page = page
    page.clean()
    page.window.icon = str(files('chord_box') / 'chord_box.ico')
    page.title = "chord box"
    page.window.min_width = 1200
    page.window.min_height = 600
    page.window.maximized = True

    menubar = ft.MenuBar([
        ft.SubmenuButton(save_btn := ft.Button('保存')),
        ft.SubmenuButton(open_btn := ft.Button('打开')),
        ft.SubmenuButton(confirm := ft.Button('确认')),
        ft.SubmenuButton(ft.Button('删除', on_click=ChordBtn.delete)),
        ft.SubmenuButton(ft.Button('插入', on_click=ChordBtn.insert)),
        reselect := ft.SubmenuButton(ft.Button('重选'), visible=False)
    ], expand=True)
    prediction_area = ft.Container(
        padding=20,
        bgcolor=ft.Colors.BLUE_100,
        border_radius=ft.BorderRadius.all(12),
        border=ft.Border.all(3, ft.Colors.GREY_900),
        expand=True
    )
    keyboard = ft.Container(
        width=page.window.min_width,
        padding=5,
        border=ft.Border.all(3, ft.Colors.with_opacity(0.8, ft.Colors.GREY_900)),
        bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
        expand=True
    )
    chords = ft.GridView(
        ChordBtn.all,
        expand=True,
        max_extent=150,
        spacing=10,
        run_spacing=10
    )
    editing_area = ft.Column([
        ft.Container(
            chords,
            border=ft.Border.all(3, ft.Colors.with_opacity(0.8, ft.Colors.GREY_900)),
            border_radius=ft.BorderRadius.all(12),
            expand=4,
            padding=10
        ),
        ft.Row([keyboard], expand=1)
    ], expand=True)
    
    keys = (
        i for i in 
        [
            'Z', 'S', 'X', 'D', 'C', 'V', 'G', 'B', 'H', 'N', 'J', 'M',
            'Q', '2', 'W', '3', 'E', 'R', '5', 'T', '6', 'Y', '7', 'U',
            'I', '9', 'O', '0', 'P', '[', '=', ']'
        ]
    )
    KEY_MAP = {}
    def update_btn_color(btn): btn.bgcolor = {'part': ft.Colors.GREEN, 'root': ft.Colors.AMBER}.get(btn.selected_as, btn.original_color)
    def update_reselect(): reselect.visible = any(i.selected_as for i in BTNS)
    BTNS = []
    def init_btn(btn: ft.Button, index: int):
        BTNS.append(btn)
        btn.index = index
        btn.selected_as = None
        btn.original_color = btn.bgcolor
        btn.last_click = time.time()
        def on_click():
            midi = PrettyMIDI()
            midi.instruments.append(instr := Instrument(0))
            instr.notes.append(Note(127, 48 + index, 0, 2))
            player.play_th(midi)
            if btn.selected_as:
                btn.selected_as = None
            else:
                btn.selected_as = 'part'
            if time.time()  - btn.last_click < 0.2:
                btn.selected_as = 'root'
            update_btn_color(btn)
            update_reselect()
            btn.last_click = time.time()
        btn.on_click = on_click
        try:
            KEY_MAP[next(keys)] = on_click
        except StopIteration:
            pass
    init_keyboard(keyboard, init_btn)

    def clean_key():
        reselect.visible = False
        for btn in BTNS:
            btn.selected_as = None
            btn.bgcolor = btn.original_color
    reselect.content.on_click = clean_key

    def on_chordbtn_click(chordbtn):
        root = ChordBtn.current.root
        part = ChordBtn.current.part
        for i, btn in enumerate(BTNS):
            if i == root:
                btn.selected_as = 'root'
            elif i in (part or []):
                btn.selected_as = 'part'
            else:
                btn.selected_as = None
            update_btn_color(btn)
        update_reselect()
        if part:
            midi = PrettyMIDI()
            midi.instruments.append(instr := Instrument(0))
            instr.notes.extend(Note(127, 48 + i, 0, 2) for i in part)
            player.stop_th()
            player.play_th(midi)
        try:
            former = later = None
            current_index = ChordBtn.all.index(ChordBtn.current)
            former = ChordBtn.all[current_index - 1]
            later = ChordBtn.all[current_index + 1]
        except IndexError:
            pass
        if (former is None) or (former.root is None) or (former.part is None):
            former = None
        if (later is None) or (later.root is None) or (later.part is None):
            later = None
        if (former is not None) and (later is not None):
            query.connect(prediction_area, former.root, former.part, later.root, later.part)
        elif former:
            query.predict(prediction_area, former.root, former.part)
        elif later:
            query.reverse(prediction_area, later.root, later.part)
        else:
            query.void(prediction_area)
    ChordBtn.on_chordbtn_click = on_chordbtn_click

    if not ChordBtn.all:
        ChordBtn().on_click()
    else:
        ChordBtn.all[0].on_click()

    def next_chord():
        root = None
        part = []
        for i, btn in enumerate(BTNS):
            match btn.selected_as:
                case 'root':
                    if root is not None:
                        page.show_dialog(ft.SnackBar(ft.Text('只能选择一个根音')))
                        return
                    root = i
                    part.append(i)
                case 'part':
                    part.append(i)
        if root is None:
            page.show_dialog(ft.SnackBar(ft.Text('缺少根音')))
            return
        ChordBtn.next_chordbtn(root, part)
    confirm.on_click = next_chord

    async def save():
        picker = ft.FilePicker()
        path = await picker.save_file(
            dialog_title='保存',
            file_name='chords.json',
            allowed_extensions=['json'],
            file_type=ft.FilePickerFileType.CUSTOM,
        )
        if path:
            Path(path).write_text(json.dumps(ChordBtn.to_list(), indent=4), 'utf-8')
    save_btn.on_click = save

    async def open():
        picker = ft.FilePicker()
        files = await picker.pick_files(
            dialog_title='打开',
            allowed_extensions=['json'],
            file_type=ft.FilePickerFileType.CUSTOM,
        )
        if files:
            if len(files) > 1:
                page.show_dialog(ft.SnackBar(ft.Text('不可选择多个文件')))
                return
            ChordBtn.from_list(json.loads(Path(files[0].path).read_text('utf-8')))
    open_btn.on_click = open

    def on_keyboard_event(e: ft.KeyboardEvent):
        if e.alt or e.ctrl or e.shift:
            if (not e.alt) and (not e.shift):
                match e.key:
                    case 'S':
                        save()
                    case 'O':
                        open()
            return
        match e.key:
            case 'Tab':
                clean_key()
            case 'Insert':
                ChordBtn.insert()
            case 'Enter':
                next_chord()
            case 'Delete':
                ChordBtn.delete()
            case k if k in KEY_MAP:
                KEY_MAP[k]()
    page.on_keyboard_event = on_keyboard_event
    
    page.add(
        ft.Column([
            ft.Row([menubar]),
            ft.Row([
                ft.Column([prediction_area], expand=1), ft.Column([editing_area], expand=4)
            ], expand=True)
        ], expand=True)
    )

def run():
    display_mark = False
    def _run():
        global current_page
        ft.run(main)
        current_page = None
    def app_exit():
        if current_page:
            asyncio.run_coroutine_threadsafe(current_page.window.close(), current_page.loop)
        icon.stop()
    def display():
        nonlocal display_mark
        if not current_page:
            display_mark = True
    icon = pystray.Icon(
        'chord box', Image.open(str(files('chord_box') / 'chord_box.ico')), 'chord box', [
            pystray.MenuItem('退出应用', app_exit),
            pystray.MenuItem('启动窗口', display, default=True)
        ]
    )
    icon_th = Thread(target=icon.run, daemon=True)
    icon_th.start()
    _run()
    while icon_th.is_alive():
        if display_mark:
            _run()
            display_mark = False
        time.sleep(0.1)
