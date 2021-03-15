import unicodedata

from visidata import *

enumvalues = {
  'category': {
    'Lu': 'Letter, uppercase',
    'Ll': 'Letter, lowercase',
    'Lt': 'Letter, titlecase',
    'Lm': 'Letter, modifier',
    'Lo': 'Letter, other',
    'Mn': 'Mark, nonspacing',
    'Mc': 'Mark, spacing combining',
    'Me': 'Mark, enclosing',
    'Nd': 'Number, decimal digit',
    'Nl': 'Number, letter',
    'No': 'Number, other',
    'Pc': 'Punctuation, connector',
    'Pd': 'Punctuation, dash',
    'Ps': 'Punctuation, open',
    'Pe': 'Punctuation, close',
    'Pi': 'Punctuation, initial quote',
    'Pf': 'Punctuation, final quote',
    'Po': 'Punctuation, other',
    'Sm': 'Symbol, math',
    'Sc': 'Symbol, currency',
    'Sk': 'Symbol, modifier',
    'So': 'Symbol, other',
    'Zs': 'Separator, space',
    'Zl': 'Separator, line',
    'Zp': 'Separator, paragraph',
    'Cc': 'Other, control',
    'Cf': 'Other, format',
    'Cs': 'Other, surrogate',
    'Co': 'Other, private use',
    'Cn': 'Other, not assigned',
  },

  'bidirectional': {
    'L': 'Left_To_Right',  # any strong left-to-right character
    'R': 'Right_To_Left',  # any strong right-to-left (non-Arabic-type) character
    'AL': 'Arabic_Letter',  # any strong right-to-left (Arabic-type) character
#Weak Types
    'EN': 'European_Number',  # any ASCII digit or Eastern Arabic-Indic digit
    'ES': 'European_Separator',  # plus and minus signs
    'ET': 'European_Terminator',  # a terminator in a numeric format context, includes currency signs
    'AN': 'Arabic_Number',  # any Arabic-Indic digit
    'CS': 'Common_Separator',  # commas, colons, and slashes
    'NSM': 'Nonspacing_Mark',  # any nonspacing mark
    'BN': 'Boundary_Neutral',  # most format characters, control codes, or noncharacters
#Neutral Types
    'B': 'Paragraph_Separator',  # various newline characters
    'S': 'Segment_Separator',  # various segment-related control codes
    'WS': 'White_Space',  # spaces
    'ON': 'Other_Neutral',  # most other symbols and punctuation marks
#Explicit Formatting Types
    'LRE': 'Left_To_Right_Embedding',  # U+202A: the LR embedding control
    'LRO': 'Left_To_Right_Override',  # U+202D: the LR override control
    'RLE': 'Right_To_Left_Embedding',  # U+202B: the RL embedding control
    'RLO': 'Right_To_Left_Override',  # U+202E: the RL override control
    'PDF': 'Pop_Directional_Format',  # U+202C: terminates an embedding or override control
    'LRI': 'Left_To_Right_Isolate',  # U+2066: the LR isolate control
    'RLI': 'Right_To_Left_Isolate',  # U+2067: the RL isolate control
    'FSI': 'First_Strong_Isolate',  # U+2068: the first strong isolate control
    'PDI': 'Pop_Directional_Isolate',  # U+2069: terminates an isolate control
  },
  'east_asian_width': {
    'A': 'Ambiguous',
    'F': 'Fillwidth',
    'H': 'Halfwidth',
    'N': 'Neutral',
    'Na': 'Narrow',
    'W': 'Wide',
  },
  'mirrored': { 0: 'No', 1: 'Yes' },
}


class UnicodeDataColumn(Column):
    def __init__(self, name, *args, **kwargs):
        super().__init__(name, expr=name, *args, **kwargs)

    def calcValue(self, row):
        r = getattr(unicodedata, self.expr)(row.text)
        if self.expr in enumvalues:
            return enumvalues[self.expr][r]
        return r


class UnicodeBrowser(Sheet):
    rowtype='chars' # rowdef: AttrDict(.text=ch)
    precious=False
    columns = [
        Column('num', fmtstr='%04X', type=int, getter=lambda c,r: ord(r.text)),
        Column('text', getter=lambda c,r: unicodedata.normalize('NFC', r.text)),
        UnicodeDataColumn('name', width=20),
        UnicodeDataColumn('category'),
#        UnicodeDataColumn('decimal'),
#        UnicodeDataColumn('digit'),
        UnicodeDataColumn('numeric'),
        UnicodeDataColumn('bidirectional'),
        UnicodeDataColumn('east_asian_width'),
        UnicodeDataColumn('combining'),
        UnicodeDataColumn('mirrored'),
#        UnicodeDataColumn('decomposition'),
#        UnicodeDataColumn('normalize'),
#        UnicodeDataColumn('is_normalized', width=0),
    ]


@VisiData.lazy_property
def unibrowser(vd):
    return UnicodeBrowser('unicode_chars', rows=[AttrDict(text=chr(i)) for i in range(32, 0x100000) if unicodedata.category(chr(i))[0] not in 'CM'])
