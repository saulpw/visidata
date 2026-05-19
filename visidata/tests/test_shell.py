import re
import shlex

from visidata.shell import SHELL_COLREF_RE


def _substitute(expr, ctx):
    'Mirror ColumnShell.calcValue substitution for unit testing. #3026'
    return re.sub(SHELL_COLREF_RE,
                  lambda m: shlex.quote(str(ctx[m.group(1) or m.group(2)])),
                  expr)


class TestSubstituteShellVars:
    def test_quotes_value_with_spaces(self):  # #3026
        assert _substitute('ls $filename', {'filename': 'filename with space.txt'}) \
            == "ls 'filename with space.txt'"

    def test_preserves_unquoted_pipe(self):  # #3026
        assert _substitute('echo $filename |sed -e s/space//', {'filename': 'a b.txt'}) \
            == "echo 'a b.txt' |sed -e s/space//"

    def test_preserves_quoted_pipe_literal(self):  # #2415
        # bash sees | inside double quotes as literal; no $col, so re.sub is a no-op
        assert _substitute('echo "what | not-a-command"', {}) \
            == 'echo "what | not-a-command"'

    def test_preserves_redirects(self):  # #3026
        assert _substitute('cat $filename >out.txt', {'filename': 'in.txt'}) \
            == "cat in.txt >out.txt"

    def test_bare_dollar_stops_at_hyphen(self):
        # bash-compatible: $foo-bar is $foo then literal -bar
        assert _substitute('ls $first-suffix', {'first': 'Joe'}) == 'ls Joe-suffix'

    def test_bare_dollar_stops_at_dot(self):
        assert _substitute('ls $f.txt', {'f': 'name'}) == 'ls name.txt'

    def test_braced_allows_hyphen(self):
        assert _substitute('ls ${first-name}', {'first-name': 'Joe X'}) \
            == "ls 'Joe X'"

    def test_braced_allows_dot(self):
        assert _substitute('ls ${user.home}', {'user.home': '/home/jo'}) \
            == "ls /home/jo"

    def test_braced_allows_spaces(self):
        assert _substitute('ls ${col with spaces}', {'col with spaces': 'val'}) \
            == 'ls val'

    def test_braced_followed_by_literal(self):
        assert _substitute('${a}bc', {'a': 'X'}) == 'Xbc'

    def test_underscore_in_bare_name(self):
        assert _substitute('echo $my_col', {'my_col': 'v'}) == 'echo v'

    def test_simple_value_unquoted(self):
        # shlex.quote returns bare token when no quoting is needed
        assert _substitute('ls $f', {'f': 'plain.txt'}) == 'ls plain.txt'

    def test_stringifies_non_strings(self):
        assert _substitute('echo $n', {'n': 42}) == 'echo 42'

    def test_adjacent_dollar_refs(self):
        assert _substitute('$a$b', {'a': 'x', 'b': 'y'}) == 'xy'

    def test_no_substitution_when_no_dollar(self):
        assert _substitute('ls -la', {}) == 'ls -la'

    def test_unclosed_brace_left_literal(self):
        # ${foo without } matches neither alternative; passes through to bash
        assert _substitute('echo ${foo', {}) == 'echo ${foo'


class TestShellColrefRegex:
    def _names(self, s):
        return [m.group(1) or m.group(2) for m in re.finditer(SHELL_COLREF_RE, s)]

    def test_finds_simple_name(self):
        assert self._names('echo $foo bar') == ['foo']

    def test_finds_underscore_name(self):
        assert self._names('echo $my_col') == ['my_col']

    def test_bare_form_stops_at_hyphen(self):
        assert self._names('echo $first-name') == ['first']

    def test_bare_form_stops_at_dot(self):
        assert self._names('echo $user.home') == ['user']

    def test_braced_finds_hyphenated_name(self):
        assert self._names('echo ${first-name}') == ['first-name']

    def test_braced_finds_dotted_name(self):
        assert self._names('echo ${user.home}') == ['user.home']

    def test_braced_finds_name_with_spaces(self):
        assert self._names('echo ${col with spaces}') == ['col with spaces']

    def test_stops_at_pipe(self):
        assert self._names('echo $f|sed') == ['f']

    def test_stops_at_space(self):
        assert self._names('echo $f $g') == ['f', 'g']

    def test_mixed_forms(self):
        assert self._names('echo $a ${b-c} $d') == ['a', 'b-c', 'd']
