import json
import time
import collections
import random
from functools import cached_property
from base64 import b64encode

from visidata import vd, VisiData, Canvas, Animation, Path, asyncthread, clipdraw, colors, ItemColumn, Sheet, wraptext

vd.theme_option('color_hint', 'black on yellow', '')

@VisiData.api
def getNoahsPath(vd, name):
    return Path(vd.pkg_resources_files('visidata')/f'experimental/noahs_tapestry/{name}')

@VisiData.api
def openNoahsText(vd, name):
    return vd.getNoahsPath(name).open(encoding='utf-8')

@VisiData.cached_property
def noahsDatabase(vd):
    return vd.open_sqlite(vd.getNoahsPath('noahs.sqlite'))

class NoahsPuzzle(Sheet):
    guide = '''
        # Puzzle {sheet.puznum}
        - `Shift+A` to input a solution to the puzzle
        - `Shift+Y` to attempt the current cell as the solution
        - `Shift+B` to open Noah's Database Backup
        - `Shift+V` to view Noah's Tapestry
    '''
    rowtype = 'lines'  # rowdef: [linenum, text]
    filetype = 'txt'
    columns = [
        ItemColumn('linenum', 0, type=int, width=0),
        ItemColumn('text', 1, width=80, displayer='full'),
    ]
    precious = False

    def iterload(self):
        clues = json.loads(vd.getNoahsPath(f'clues.json').read_text())
        source = vd.getNoahsPath(f'puzzle{self.puznum}.md')
        winWidth = 78
        formatted_text = source.open(encoding='utf-8').read().format(**clues)
        for startingLine, text in enumerate(formatted_text.splitlines()):
            text = text.strip()
            if text:
                for i, (L, _) in enumerate(wraptext(str(text), width=winWidth)):
                    yield [startingLine+i+1, L]
            else:
                yield [startingLine+1, text]

@VisiData.cached_property
def noahsSolutions(vd):
    return json.loads(vd.getNoahsPath(f'solutions.json').read_text())

@VisiData.api
def solve_puzzle(vd, answer):
    puznum = vd.noahsCurrentPuznum
    if b64encode(answer.encode()).decode() != vd.noahsSolutions[f'p{puznum}']:
        vd.fail("Hmmm, that doesn't seem right. Try again?")

    vd.noahsTapestry.solved.add(puznum)
    vd.status(f'Correct! The candle is now lit.')
    vd.push(vd.noahsTapestry)


class Tapestry(Canvas):
    @property
    def guide(self):
        ret = ''
        if vd.screenWidth < 120 or vd.screenHeight < 50:
            ret = f'''
            # [:black on yellow]WARNING: TERMINAL TOO SMALL[/]
            Please expand your terminal to at least 120x50 (currently {vd.screenWidth}x{vd.screenHeight})
        '''

        ret += '''
            # Noah's Tapestry
            An interactive data game

            - `Shift+N` to open the next puzzle
        '''

        return ret

    solved = set()
    def reload(self):
        self.noahs_menorah = Animation(vd.openNoahsText('menorah.ddw'))
        self.noahs_tapestry = Animation(vd.openNoahsText('tapestry.ddw'))
        self.noahs_flame = Animation(vd.openNoahsText('flame.ddw'))
        self.solved = set()

#        self.keep_running()

    @asyncthread
    def keep_running(self):
        while True:
            time.sleep(1)

    def draw(self, scr):
        solvedays = ['menorah']+[f'day{i}' for i in self.solved]
        t = time.time()
        self.noahs_menorah.draw(scr, t=0, y=30, x=19)
        if not self.solved:
            clipdraw(scr, 22, 52, "Light the [:italic]shamash[/]", colors['255'])
            return

        self.noahs_menorah.draw(scr, t=0.1, y=30, x=19, tags=solvedays)
        self.noahs_tapestry.draw(scr, t=t, tags=solvedays)

        for i in self.solved:
            xs = [58, 22+9*8, 22+9*7, 22+9*6, 22+9*5, 22+27, 22+18, 22+9, 22, 22]
            ys = [28, 32, 32, 32, 32, 32, 32, 32, 32, 32]
            x = xs[i]
            y = ys[i]

            self.noahs_flame.draw(scr, t=t+(i+random.random())*0.2, y=y, x=x)

    def open_puzzle(self, puznum=None):
        if puznum is None:
            puznum = 0
            if self.solved:
                puznum = max(self.solved)+1

        vs = NoahsPuzzle('puzzle', str(puznum), source=self, puznum=puznum)
        vs.ensureLoaded()
        vd.noahsCurrentPuznum = puznum
        return vs


@VisiData.lazy_property
def noahsTapestry(vd):
    vd.curses_timeout = 50
    return Tapestry('noahs', 'tapestry')


NoahsPuzzle.options.color_default = '178 yellow on 232 black'

vd.addCommand('Shift+B', 'open-noahs-database', 'vd.push(noahsDatabase)', "open database for Noah's Tapestry")
vd.addCommand('Shift+V', 'open-noahs-tapestry', 'vd.push(noahsTapestry)', "open Noah's Tapestry")
Tapestry.addCommand('Shift+N', 'open-puzzle-next', 'vd.push(open_puzzle())', 'open next unsolved puzzle')
NoahsPuzzle.addCommand('Shift+A', 'solve-puzzle-input', 'solve_puzzle(input("Answer: "))', 'input an answer to the current puzzle')
Sheet.addCommand('Shift+Y', 'solve-puzzle-cell', 'solve_puzzle(cursorValue)', 'input an answer to the current puzzle')
for i in range(9):
    Tapestry.addCommand(f'{i}', f'open-puzzle-{i}', f'vd.push(open_puzzle({i}))')
    Tapestry.addCommand(f'Alt+{i}', f'solve-puzzle-force-{i}', f'sheet.solved.add({i})')
