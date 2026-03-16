from visidata.shell import _buildShellExpr


class TestShellExpr:
    def test_quotes_expanded_columns_with_spaces(self):  # #3026
        cmd = _buildShellExpr('ls $filename', {'filename': 'filename with space.txt'})

        assert cmd == "ls 'filename with space.txt'"

    def test_preserves_shell_pipe_syntax(self):  # #3026
        cmd = _buildShellExpr(
            'echo $filename |sed -e s/space//',
            {'filename': 'filename with space.txt'},
        )

        assert cmd == "echo 'filename with space.txt' | sed -e s/space//"

    def test_preserves_quoted_pipe_literals(self):  # #2415
        cmd = _buildShellExpr('echo "what | not-a-command"', {})

        assert cmd == 'echo "what | not-a-command"'
