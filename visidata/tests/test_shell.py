import re
import shlex

import pytest

from visidata.shell import SHELL_COLREF_RE


def _substitute(expr, ctx):
    'Mirror ColumnShell.calcValue substitution for unit testing. #3026'
    return re.sub(SHELL_COLREF_RE,
                  lambda m: shlex.quote(str(ctx[m.group(1) or m.group(2)])),
                  expr)


@pytest.mark.parametrize('expr, ctx, expected', [
    # #3026 — symptoms from the issue
    ('ls $filename',                   {'filename': 'filename with space.txt'}, "ls 'filename with space.txt'"),
    ('echo $filename |sed -e s/space//', {'filename': 'a b.txt'},               "echo 'a b.txt' |sed -e s/space//"),
    ('cat $filename >out.txt',         {'filename': 'in.txt'},                  'cat in.txt >out.txt'),
    # #2415 — quoted | inside double quotes is literal to bash; no $col, so re.sub is a no-op
    ('echo "what | not-a-command"',    {},                                      'echo "what | not-a-command"'),
    # bare $word follows bash word rules (\w+)
    ('ls $first-suffix',               {'first': 'Joe'},                        'ls Joe-suffix'),
    ('ls $f.txt',                      {'f': 'name'},                           'ls name.txt'),
    ('echo $my_col',                   {'my_col': 'v'},                         'echo v'),
    # ${...} escape hatch for non-\w characters in column names
    ('ls ${first-name}',               {'first-name': 'Joe X'},                 "ls 'Joe X'"),
    ('ls ${user.home}',                {'user.home': '/home/jo'},               'ls /home/jo'),
    ('ls ${col with spaces}',          {'col with spaces': 'val'},              'ls val'),
    ('${a}bc',                         {'a': 'X'},                              'Xbc'),
    # misc
    ('ls $f',                          {'f': 'plain.txt'},                      'ls plain.txt'),  # shlex.quote leaves bare token
    ('echo $n',                        {'n': 42},                               'echo 42'),       # non-string values stringified
    ('$a$b',                           {'a': 'x', 'b': 'y'},                    'xy'),
    ('ls -la',                         {},                                      'ls -la'),
    ('echo ${foo',                     {},                                      'echo ${foo'),    # unclosed brace matches neither alt
])
def test_substitute(expr, ctx, expected):
    assert _substitute(expr, ctx) == expected


@pytest.mark.parametrize('expr, names', [
    ('echo $foo bar',           ['foo']),
    ('echo $my_col',            ['my_col']),
    ('echo $first-name',        ['first']),       # bare stops at -
    ('echo $user.home',         ['user']),        # bare stops at .
    ('echo ${first-name}',      ['first-name']),  # braced allows -
    ('echo ${user.home}',       ['user.home']),   # braced allows .
    ('echo ${col with spaces}', ['col with spaces']),
    ('echo $f|sed',             ['f']),
    ('echo $f $g',              ['f', 'g']),
    ('echo $a ${b-c} $d',       ['a', 'b-c', 'd']),
])
def test_colref_regex(expr, names):
    assert [m.group(1) or m.group(2) for m in re.finditer(SHELL_COLREF_RE, expr)] == names
