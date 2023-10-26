'''Colorbrewer scales for plotting in Visidata.

Thanks to:
  - Prof. Cynthia Brewer et al. @ colorbrewer.org
  - @dsc https://github.com/dsc/colorbrewer-python
  - @MicahElliott https://gist.github.com/MicahElliott/719710
  - @er1kb https://github.com/er1kb/visidata-plugins

   This feature adds these commands which can be used while viewing a plot (GraphSheet):
       - color-cycle: change plot colors to another palette
       - color-reset:
'''
from visidata import vd, VisiData, GraphSheet, BaseSheet, Sheet, ItemColumn, CellColorizer, ENTER

# https://raw.githubusercontent.com/er1kb/colorbrewer-python/master/colorbrewer.py
# https://gist.githubusercontent.com/er1kb/02f1fee3453431d5c0ccad5e62326a99/raw/73d047f0a3ffc35f0655488547e7f24fa3f04ea6/colortrans.py

vd.option('plot_palette', 'Set3', 'colorbrewer palette to use')


colorbrewer_palettes = dict(
    Accent='114 146 216 228 61 198 130 59',
    Dark2='36 166 97 162 70 178 136 59',
    Paired='152 31 150 70 210 160 215 208 182 60 228 130',
    Pastel1='217 152 194 188 223 230 187 225 231',
    Pastel2='152 223 188 224 194 229 224 188',
    Set1='160 67 71 97 208 227 130 211 102',
    Set2='73 209 110 176 149 220 186 145',
    Set3='116 229 146 209 110 215 149 224 188 139 194 227',

YellowGreen = {
3: '229 150 71',
4: '230 150 114 29',
5: '230 150 114 71 23',
6: '230 193 150 114 71 23',
7: '230 193 150 114 71 29 23',
8: '230 229 193 150 114 71 29 23',
9: '230 229 193 150 114 71 29 23 22',
},
YellowGreenBlue = {
3: '229 115 31',
4: '230 151 74 25',
5: '230 151 74 31 24',
6: '230 187 115 74 31 24',
7: '230 187 115 74 31 25 18',
8: '230 229 187 115 74 31 25 18',
9: '230 229 187 115 74 31 25 24 17',
},
GreenBlue = {
3: '194 151 74',
4: '230 151 116 31',
5: '230 151 116 74 25',
6: '230 194 151 116 74 25',
7: '230 194 151 116 74 31 25',
8: '231 194 194 151 116 74 31 25',
9: '231 194 194 151 116 74 31 25 24',
},
BlueGreen = {
3: '195 116 35',
4: '231 152 73 29',
5: '231 152 73 35 22',
6: '231 194 116 73 35 22',
7: '231 194 116 73 72 29 22',
8: '231 195 194 116 73 72 29 22',
9: '231 195 194 116 73 72 29 22 22',
},
PurpleBlueGreen = {
3: '225 146 30',
4: '231 152 74 30',
5: '231 152 74 30 23',
6: '231 188 146 74 30 23',
7: '231 188 146 74 67 30 23',
8: '231 225 188 146 74 67 30 23',
9: '231 225 188 146 74 67 30 23 23',
},
PurpleBlue = {
3: '225 146 31',
4: '231 152 110 25',
5: '231 152 110 31 24',
6: '231 188 146 110 31 24',
7: '231 188 146 110 67 25 24',
8: '231 225 188 146 110 67 25 24',
9: '231 225 188 146 110 67 25 24 23',
},
BluePurple = {
3: '195 146 97',
4: '231 152 104 97',
5: '231 152 104 97 90',
6: '231 152 146 104 97 90',
7: '231 152 146 104 97 97 53',
8: '231 195 152 146 104 97 97 53',
9: '231 195 152 146 104 97 97 90 53',
},
RedPurple = {
3: '224 217 162',
4: '230 217 205 126',
5: '230 217 205 162 90',
6: '230 223 217 205 162 90',
7: '230 223 217 205 168 126 90',
8: '231 224 223 217 205 168 126 90',
9: '231 224 223 217 205 168 126 90 53',
},
PurpleRed = {
3: '189 176 162',
4: '231 182 169 161',
5: '231 182 169 162 89',
6: '231 182 176 169 162 89',
7: '231 182 176 169 162 161 89',
8: '231 189 182 176 169 162 161 89',
9: '231 189 182 176 169 162 161 89 52',
},
OrangeRed = {
3: '224 216 167',
4: '230 222 209 166',
5: '230 222 209 167 124',
6: '230 223 216 209 167 124',
7: '230 223 216 209 203 166 88',
8: '231 224 223 216 209 203 166 88',
9: '231 224 223 216 209 203 166 124 88',
},
YellowOrangeRed = {
3: '229 215 202',
4: '229 221 209 160',
5: '229 221 209 202 124',
6: '229 222 215 209 202 124',
7: '229 222 215 209 202 160 124',
8: '230 229 222 215 209 202 160 124',
9: '230 229 222 215 209 202 160 124 88',
},
YellowOrangeBrown= {
3: '229 221 166',
4: '230 222 208 166',
5: '230 222 208 166 94',
6: '230 222 221 208 166 94',
7: '230 222 221 208 202 166 88',
8: '230 229 222 221 208 202 166 88',
9: '230 229 222 221 208 202 166 94 52',
},
Purples = {
3: '231 146 97',
4: '231 188 140 61',
5: '231 188 140 97 54',
6: '231 189 146 140 97 54',
7: '231 189 146 140 103 61 54',
8: '231 231 189 146 140 103 61 54',
9: '231 231 189 146 140 103 61 54 54',
},
Blues = {
3: '195 152 67',
4: '231 152 74 25',
5: '231 152 74 67 25',
6: '231 189 152 74 67 25',
7: '231 189 152 74 68 25 24',
8: '231 195 189 152 74 68 25 24',
9: '231 195 189 152 74 68 25 25 23',
},
Greens = {
3: '194 151 71',
4: '230 151 114 29',
5: '230 151 114 71 22',
6: '230 187 151 114 71 22',
7: '230 187 151 114 71 29 23',
8: '231 194 187 151 114 71 29 23',
9: '231 194 187 151 114 71 29 22 22',
},
Oranges = {
3: '224 215 166',
4: '230 216 209 166',
5: '230 216 209 166 130',
6: '230 223 215 209 166 130',
7: '230 223 215 209 202 166 88',
8: '231 224 223 215 209 202 166 88',
9: '231 224 223 215 209 202 166 130 88',
},
Reds = {
3: '224 209 160',
4: '224 216 203 160',
5: '224 216 203 160 124',
6: '224 217 209 203 160 124',
7: '224 217 209 203 202 160 88',
8: '231 224 217 209 203 202 160 88',
9: '231 224 217 209 203 202 160 124 52',
},
Greys = {
3: '231 145 59',
4: '231 188 102 59',
5: '231 188 102 59 16',
6: '231 188 145 102 59 16',
7: '231 188 145 102 102 59 16',
8: '231 231 188 145 102 102 59 16',
9: '231 231 188 145 102 102 59 16 16',
},
PurpleOrange = {
3: '215 231 104',
4: '166 215 146 60',
5: '166 215 231 146 60',
6: '130 215 223 189 104 54',
7: '130 215 223 231 189 104 54',
8: '130 172 215 223 189 146 103 54',
9: '130 172 215 223 231 189 146 103 54',
10: '94 130 172 215 223 189 146 103 54 17',
11: '94 130 172 215 223 231 189 146 103 54 17',
},
BrownGreen = {
3: '179 231 73',
4: '130 180 115 29',
5: '130 180 231 115 29',
6: '94 179 224 188 73 23',
7: '94 179 224 231 188 73 23',
8: '94 136 180 224 188 115 66 23',
9: '94 136 180 224 231 188 115 66 23',
10: '58 94 136 180 224 188 115 66 23 23',
11: '58 94 136 180 224 231 188 115 66 23 23',
},
PurpleGreen = {
3: '140 231 108',
4: '96 146 151 29',
5: '96 146 231 151 29',
6: '90 140 188 194 108 29',
7: '90 140 188 231 194 108 29',
8: '90 97 146 188 194 151 71 29',
9: '90 97 146 188 231 194 151 71 29',
10: '53 90 97 146 188 194 151 71 29 22',
11: '53 90 97 146 188 231 194 151 71 29 22',
},
PinkYellowGreen = {
3: '182 231 149',
4: '162 218 150 70',
5: '162 218 231 150 70',
6: '162 182 225 194 149 64',
7: '162 182 225 231 194 149 64',
8: '162 175 218 225 194 150 107 64',
9: '162 175 218 225 231 194 150 107 64',
10: '89 162 175 218 225 194 150 107 64 22',
11: '89 162 175 218 225 231 194 150 107 64 22',
},
RedBlue = {
3: '209 231 74',
4: '160 216 116 25',
5: '160 216 231 116 25',
6: '124 209 224 189 74 25',
7: '124 209 224 231 189 74 25',
8: '124 167 216 224 189 116 68 25',
9: '124 167 216 224 231 189 116 68 25',
10: '52 124 167 216 224 189 116 68 25 23',
11: '52 124 167 216 224 231 189 116 68 25 23',
},
RedGrey = {
3: '209 231 102',
4: '160 216 145 59',
5: '160 216 231 145 59',
6: '124 209 224 188 102 59',
7: '124 209 224 231 188 102 59',
8: '124 167 216 224 188 145 102 59',
9: '124 167 216 224 231 188 145 102 59',
10: '52 124 167 216 224 188 145 102 59 16',
11: '52 124 167 216 224 231 188 145 102 59 16',
},
RedYellowBlue = {
3: '209 229 110',
4: '160 215 152 31',
5: '160 215 229 152 31',
6: '166 209 222 195 110 67',
7: '166 209 222 229 195 110 67',
8: '166 203 215 222 195 152 110 67',
9: '166 203 215 222 229 195 152 110 67',
10: '124 166 203 215 222 195 152 110 67 60',
11: '124 166 203 215 222 229 195 152 110 67 60',
},
Spectral = {
3: '209 229 114',
4: '160 215 151 31',
5: '160 215 229 151 31',
6: '167 209 222 192 114 67',
7: '167 209 222 229 192 114 67',
8: '167 203 215 222 192 151 73 67',
9: '167 203 215 222 229 192 151 73 67',
10: '125 167 203 215 222 192 151 73 67 61',
11: '125 167 203 215 222 229 192 151 73 67 61',
},
RedYellowGreen = {
3: '209 229 113',
4: '160 215 149 29',
5: '160 215 229 149 29',
6: '166 209 222 192 113 29',
7: '166 209 222 229 192 113 29',
8: '166 203 215 222 192 149 71 29',
9: '166 203 215 222 229 192 149 71 29',
10: '124 166 203 215 222 192 149 71 29 23',
11: '124 166 203 215 222 229 192 149 71 29 23',
},
)

vd.colorbrewer_choices = [dict(key=k, colors=v) for k, v in colorbrewer_palettes.items()]


class PalettesSheet(Sheet):
    colorizers = [
        CellColorizer(2, None, lambda s,c,r,v: f'black on {v.value}' if c and r and c.name.startswith('c') else None)
    ]
    columns = [
        ItemColumn('name', 0),
        ItemColumn('n', 1, type=int),
    ] + [
        ItemColumn(f'c{i}', i+1)
          for i in range(1, 13)
    ]

    def iterload(self):
        for palname, pals in colorbrewer_palettes.items():
            if isinstance(pals, str):
                yield [palname, len(pals.split())] + pals.split()
            else:
                for n, pal in pals.items():
                    yield [palname, n] + pal.split()


@GraphSheet.api
def cycle_palette(obj):
    pals = list(colorbrewer_palettes.keys())
    i = pals.index(obj.options.plot_palette)
    i = (i+1)%len(pals)
    n = len(obj.legends) if getattr(obj, 'legends', None) else 8
    obj.set_palette(pals[i], n)


@GraphSheet.api
def set_palette(obj, palname, n):
    r = colorbrewer_palettes[palname]
    if not isinstance(r, str):
        n = max(n, min(r.keys()))
        n = min(n, max(r.keys()))
        r = r[n]

    vd.status(f'Using {palname} {n}-color palette')
    obj.options.plot_palette = palname
    obj.options.plot_colors = r

    if isinstance(obj, GraphSheet):
        obj.reload()


VisiData.set_palette  = GraphSheet.set_palette
VisiData.cycle_palette = GraphSheet.cycle_palette


BaseSheet.addCommand(None, 'open-palettes', 'vd.push(PalettesSheet("palettes", source=vd))', 'open color palettes sheet for graphs')
BaseSheet.addCommand(None, 'cycle-palette', 'vd.cycle_palette()', 'cycle to next color palette for graphs')
BaseSheet.addCommand(None, 'unset-palette', 'vd.options.unset("plot_colors")', 'reset to default color palette for graphs')

GraphSheet.addCommand('C', 'open-palettes-sheet', 'vd.push(PalettesSheet("palettes", source=sheet))', 'open color palettes sheet for this graph')
GraphSheet.addCommand('zc', 'cycle-palette-sheet', 'sheet.cycle_palette()', 'cycle to next color palette for this graph')
GraphSheet.addCommand(None, 'unset-palette-sheet', 'sheet.options.unset("plot_colors"); reload()', 'reset to default color palette for this graph')

PalettesSheet.addCommand(ENTER, 'choose-palette', 'source.set_palette(cursorRow[0], cursorRow[1])', 'set current palette for source graph')

vd.addMenuItems('''
    Plot > Palette > cycle > cycle-palette-sheet
    Plot > Palette > unset > unset-palette-sheet
    Plot > Palette > choose > open-palettes
''')

vd.addGlobals(PalettesSheet=PalettesSheet)
