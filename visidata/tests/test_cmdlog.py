import pytest

import visidata
from visidata import vd


@pytest.mark.usefixtures('curses_setup')
class TestCmdlog:
    def test_go_commands_not_loggable(self):
        loggable = sorted({c.longname
                           for cmds in vd.commands.values()
                           for c in cmds.values()
                           if c.longname.startswith('go-') and vd.isLoggableCommand(c)})
        assert loggable == []

    def test_movement_does_not_replace_last_command(self):
        vs = visidata.PyobjSheet('rows', source=[dict(a=3), dict(a=1), dict(a=2)])
        vd.push(vs)
        vs.ensureLoaded()
        vd.sync()
        vd.cmdlog.openHook(vs, vs.source)
        vs.execCommand('sort-asc')
        vs.execCommand('go-bottom')
        vs.execCommand('go-top')
        vd.cmdlog.afterExecSheet(vs, False, '')
        assert [r.longname for r in vs.cmdlog_sheet.rows] == ['open-file', 'sort-asc']
        assert vd.prevCmdlogRow.longname == 'sort-asc'
