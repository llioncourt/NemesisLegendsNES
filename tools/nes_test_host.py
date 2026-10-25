#!/usr/bin/env python3
"""Headless libretro NES QA host. Test tooling only, never part of the cartridge.
The public libretro callback ABI is used directly. A core path is explicit;
no code, BIOS or ROM is downloaded. Keep the core's own licence with the core.
"""
from __future__ import annotations
import ctypes as C
import pathlib
import tempfile

class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p),
                ('size', C.c_size_t), ('meta', C.c_char_p)]
class Variable(C.Structure):
    _fields_ = [('key', C.c_char_p), ('value', C.c_char_p)]

class NES:
    BUTTONS = {'B': 0, 'SELECT': 2, 'START': 3, 'UP': 4, 'DOWN': 5,
               'LEFT': 6, 'RIGHT': 7, 'A': 8}
    def __init__(self, core: str | pathlib.Path, rom: bytes, capture=False):
        self.lib = C.CDLL(str(pathlib.Path(core).resolve()))
        self.temp = tempfile.TemporaryDirectory(prefix='nemesis-native-qa-')
        self.directory = str(self.temp.name).encode()
        self.variables = {b'fceumm_ramstate': b'fill $00'}
        self.buttons = [set(), set()]
        self.capture = capture
        self.pixel_format = 0
        self.picture = None
        self.samples = bytearray()
        self.frames = 0
        self.loaded = False
        self.closed = False
        envtype = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
        vtype = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
        atype = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
        btype = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
        ptype = C.CFUNCTYPE(None)
        itype = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)
        self.callbacks = {
            'environment': envtype(self.environment),
            'video_refresh': vtype(self.video),
            'audio_sample': atype(lambda *_: None),
            'audio_sample_batch': btype(self.audio),
            'input_poll': ptype(lambda: None),
            'input_state': itype(self.input),
        }
        for name, callback in self.callbacks.items():
            setter = getattr(self.lib, 'retro_set_' + name)
            setter.argtypes = [type(callback)]
            setter.restype = None
            setter(callback)
        for name in ('init', 'deinit', 'run', 'reset', 'unload_game'):
            f = getattr(self.lib, 'retro_' + name)
            f.argtypes = []; f.restype = None
        self.lib.retro_load_game.argtypes = [C.POINTER(GameInfo)]
        self.lib.retro_load_game.restype = C.c_bool
        self.lib.retro_get_memory_data.argtypes = [C.c_uint]
        self.lib.retro_get_memory_data.restype = C.c_void_p
        self.lib.retro_get_memory_size.argtypes = [C.c_uint]
        self.lib.retro_get_memory_size.restype = C.c_size_t
        self.lib.retro_init()
        self.buffer = C.create_string_buffer(rom)
        rom_path = pathlib.Path(self.temp.name) / 'test.nes'
        rom_path.write_bytes(rom)
        self.path = str(rom_path).encode()
        info = GameInfo(self.path, C.cast(self.buffer, C.c_void_p), len(rom), None)
        self.loaded = bool(self.lib.retro_load_game(C.byref(info)))
        if not self.loaded:
            self.close()
            raise RuntimeError('NES core rejected test cartridge')
    def environment(self, command, data):
        if command in (9, 30, 31):
            C.cast(data, C.POINTER(C.c_char_p))[0] = self.directory
            return True
        if command == 3:
            C.cast(data, C.POINTER(C.c_bool))[0] = True
            return True
        if command == 10:
            self.pixel_format = C.cast(data, C.POINTER(C.c_uint))[0]
            return self.pixel_format in (0, 1, 2)
        if command == 15:
            variable = C.cast(data, C.POINTER(Variable)).contents
            variable.value = self.variables.get(variable.key)
            return variable.value is not None
        if command == 16:
            entries = C.cast(data, C.POINTER(Variable)); i = 0
            while entries[i].key:
                choices = entries[i].value.split(b'; ', 1)[-1]
                self.variables.setdefault(entries[i].key, choices.split(b'|')[0])
                i += 1
            return True
        if command == 17:
            C.cast(data, C.POINTER(C.c_bool))[0] = False
            return True
        if command == 52:
            C.cast(data, C.POINTER(C.c_uint))[0] = 0
            return True
        return command in (11, 18, 32, 35, 36, 37, 44)
    def video(self, data, width, height, pitch):
        if self.capture and data and data != C.c_void_p(-1).value:
            self.picture = (C.string_at(data, height * pitch), width,
                            height, pitch, self.pixel_format)
    def audio(self, data, count):
        if self.capture and data:
            self.samples.extend(C.string_at(data, count * 4))
        return count
    def input(self, port, device, index, button):
        return int(port < 2 and button in self.buttons[port])
    def run(self, frames=1):
        if self.closed: raise RuntimeError('Core has been closed')
        for _ in range(frames):
            self.lib.retro_run(); self.frames += 1
    def memory(self, memory_id=2):
        pointer = self.lib.retro_get_memory_data(memory_id)
        size = self.lib.retro_get_memory_size(memory_id)
        if not pointer or not size:
            raise RuntimeError('Requested memory is unavailable')
        return pointer, size
    def read(self, offset, count, memory_id=2):
        pointer, size = self.memory(memory_id)
        if offset < 0 or count < 0 or offset + count > size:
            raise ValueError('Memory read out of bounds')
        return C.string_at(pointer + offset, count)
    def write(self, offset, data, memory_id=2):
        data = bytes(data); pointer, size = self.memory(memory_id)
        if offset < 0 or offset + len(data) > size:
            raise ValueError('Memory write out of bounds')
        C.memmove(pointer + offset, data, len(data))
    def png(self, path):
        if self.picture is None: raise RuntimeError('No captured video frame')
        import numpy as np
        from PIL import Image
        raw, width, height, pitch, fmt = self.picture
        dtype, step = ('<u4', 4) if fmt == 1 else ('<u2', 2)
        values = np.frombuffer(raw, dtype=dtype).reshape(height, pitch // step)[:, :width]
        if fmt == 1:
            rgb = np.stack(((values >> 16) & 255, (values >> 8) & 255, values & 255), -1)
        elif fmt == 2:
            rgb = np.stack((((values >> 11) & 31) * 255 // 31,
                            ((values >> 5) & 63) * 255 // 63,
                            (values & 31) * 255 // 31), -1)
        else:
            rgb = np.stack((((values >> 10) & 31) * 255 // 31,
                            ((values >> 5) & 31) * 255 // 31,
                            (values & 31) * 255 // 31), -1)
        Image.fromarray(rgb.astype('uint8'), 'RGB').save(path)
    def close(self):
        if self.closed: return
        if self.loaded: self.lib.retro_unload_game()
        self.lib.retro_deinit()
        self.temp.cleanup()
        self.closed = True
    def __enter__(self): return self
    def __exit__(self, *_): self.close()
