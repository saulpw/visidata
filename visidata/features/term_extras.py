import os

from visidata import VisiData


@VisiData.api
def ansi(*args):
    os.write(1, b'\x1b'+b''.join([str(x).encode('utf-8') for x in args]))


@VisiData.api
def set_titlebar(vd, title:str):
    ansi(']2;', title, '\x07')
