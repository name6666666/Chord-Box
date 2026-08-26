from pychord import find_chords_from_notes
from dataclasses import field
from typing import Callable, ClassVar
import flet as ft
from . import query

@ft.control
class ChordBtn(ft.Button):
    all: ClassVar[list['ChordBtn']] = []
    current: ClassVar['ChordBtn'] = None
    on_chordbtn_click: ClassVar[Callable[['ChordBtn'], None]] = None

    style: ft.ButtonStyle = field(
        default_factory=lambda: ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=0)
        )
    )
    root: int = None
    part: list[int] = None
    original_color = ft.Colors.GREY_200
    selection_color = ft.Colors.GREY_500
    bgcolor: ft.Colors = original_color
    append: bool = True
    key_mark: str | list[str, str] = None

    def __post_init__(self, ref):
        cls = self.__class__
        if self.append: cls.all.append(self)
        def on_click():
            if cls.current:
                cls.current.bgcolor = cls.original_color
            self.bgcolor = cls.selection_color
            cls.current = self
            if cls.on_chordbtn_click:
                cls.on_chordbtn_click(self)
        self.on_click = on_click
        self.content = self.update_content()
        return super().__post_init__(ref)
    
    def update_content(self):
        if self.root is None or self.part is None:
            return ft.Text('待编辑', color=ft.Colors.BLACK)
        part = list(dict.fromkeys(query.note_name(i % 12) for i in self.part))
        chords = [
            c for c in find_chords_from_notes(part) if c.root == query.note_name(self.root % 12)
        ]
        subtext = f'{query.note_name(self.root % 12)} ({' '.join(part)})'
        if chords:
            c = chords[0]
            return ft.Column([
                ft.Container(
                    ft.Text(c.chord, align=ft.Alignment.BOTTOM_CENTER, size=max(50 - len(c.chord) * 5, 20), no_wrap=True),
                    expand=2
                ),
                ft.Text(
                    subtext,
                    expand=1,
                    align=ft.Alignment.CENTER,
                    color=ft.Colors.GREY_900
                )
            ])
        else:
            return ft.Text(subtext, expand=True, size=20, color=ft.Colors.GREY_900)
        
    @classmethod
    def next_chordbtn(cls, root: int, part: list[int]):
        if not cls.current:
            return
        cls.current.root = root
        cls.current.part = part
        cls.current.content = cls.current.update_content()
        try:
            target = cls.all[cls.all.index(cls.current) + 1]
            target.on_click()
        except IndexError:
            cls().on_click()
    
    @classmethod
    def delete(cls):
        if not cls.current:
            return
        if len(cls.all) <= 1:
            return
        index = cls.all.index(cls.current)
        del cls.all[index]
        try:
            new = cls.all[index]
        except IndexError:
            new = cls.all[-1]
        new.on_click()

    @classmethod
    def insert(cls):
        new = cls(append=False)
        cls.all.insert(cls.all.index(cls.current), new)
        new.on_click()
    
    @classmethod
    def to_list(cls):
        ret = []
        for i in cls.all:
            ret.append({
                'root': i.root,
                'notes': i.part,
                'selected_key': i.key_mark
            })
        return ret
    
    @classmethod
    def from_list(cls, lst):
        cls.all.clear()
        for i in lst:
            cls(root=i['root'], part=i['notes'], key_mark=i.get('selected_key', None))
        if cls.all:
            cls.all[0].on_click()
