from pretty_midi import PrettyMIDI, Instrument, Note
from pathlib import Path
from threading import Thread, current_thread, Lock
import time
from ..show_error import show_error


try:
    from ._fluidsynth import Synth
except Exception as e:
    show_error(str(e))

class Player:
    def __init__(self, sf: Path | str) -> None:
        self.__sf = sf
        self.__synths: list[Synth] = []
        self.__th = None
        self.__lock = Lock()
        midi = PrettyMIDI()
        midi.instruments.append(Instrument(0))
        self.play(midi)

    def __set_programs(self, midi: PrettyMIDI):
        with self.__lock:
            current_synths_count = len(self.__synths)
            for i in range(len(midi.instruments)):
                synth_index = i // 16
                if synth_index >= current_synths_count:
                    synth = Synth(gain=0.8)
                    synth.start()
                    synth.sf = synth.sfload(str(self.__sf))
                    self.__synths.append(synth)
                else:
                    synth: Synth = self.__synths[synth_index]
                instr: Instrument = midi.instruments[i]
                synth.program_select(0, synth.sf, 0 if not instr.is_drum else 128, instr.program)
    
    def __noteon(self, num: int, key, vel):
        self.__synths[num // 16].noteon(num % 16, key, vel)
    
    def __noteoff(self, num: int, key):
        self.__synths[num // 16].noteoff(num % 16, key)

    def play(self, midi: PrettyMIDI):
        self.stop_th()

        self.__set_programs(midi)

        note_event: list[Note] = []
        for i in range(len(midi.instruments)):
            for n in midi.instruments[i].notes:
                n: Note
                note_event.append((True, i, n.start, n.pitch, n.velocity))
                note_event.append((False, i, n.end, n.pitch))
        note_event.sort(key=lambda n: n[2])

        if not note_event:
            return
        time.sleep(note_event[0][2])
        for i in range(len(note_event) - 1):
            n1 = note_event[i]
            n2 = note_event[i + 1]
            if n1[0]:
                self.__noteon(n1[1], n1[3], n1[4])
            else:
                self.__noteoff(n1[1], n1[3])
            time.sleep(n2[2] - n1[2])
    
    def play_th(self, midi: PrettyMIDI):
        def th_func():
            self.__set_programs(midi)
            if current_thread().stop: return

            note_event: list[Note] = []
            for i in range(len(midi.instruments)):
                for n in midi.instruments[i].notes:
                    n: Note
                    note_event.append((True, i, n.start, n.pitch, n.velocity))
                    note_event.append((False, i, n.end, n.pitch))
            note_event.sort(key=lambda n: n[2])

            if not note_event:
                return
            time.sleep(note_event[0][2])
            if current_thread().stop: return
            for i in range(len(note_event) - 1):
                n1 = note_event[i]
                n2 = note_event[i + 1]
                if n1[0]:
                    if not current_thread().stop: self.__noteon(n1[1], n1[3], n1[4])
                else:
                    if not current_thread().stop: self.__noteoff(n1[1], n1[3])
                time.sleep(n2[2] - n1[2])
                if current_thread().stop: return

        th = Thread(daemon=True, target=th_func, name='play-midi')
        th.stop = False
        th.start()
        self.__th = th

    def stop_th(self):
        with self.__lock:
            if self.__th is None:
                return False
            self.__th.stop = True
            self.__th = None
            for i in self.__synths:
                for j in range(16):
                    i.all_notes_off(j)
            return True

for i in Path.cwd().iterdir():
    if i.suffix == '.sf2':
        target = i
        break
else:
    show_error('工作目录下未找到.sf2文件')
player = Player(target)
