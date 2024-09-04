import pytest
import visidata

class TestCompleteExpr:
    def test_completer(self):
        vs = visidata.DirSheet('test', source=visidata.Path('.'))
        vs.reload()
        cexpr = visidata.CompleteExpr(vs)
        assert cexpr('fi', 0) == 'filename'  # visible column first
        assert cexpr('fi', 1) == 'filetype'  # hidden column second
        assert cexpr('logn', 0) == 'lognormvariate'  # global from math
        assert cexpr('a+logn', 0) == 'a+lognormvariate'

        assert cexpr('testv', 0) == 'testv'  # no match returns same

        visidata.vd.memoValue('testvalue', 42, '42')
        cexpr = visidata.CompleteExpr(vs)
        assert cexpr('testv', 0) == 'testvalue'
