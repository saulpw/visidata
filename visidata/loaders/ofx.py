from decimal import Decimal
from datetime import datetime
from visidata import vd, VisiData, IndexSheet, PyobjSheet, TableSheet, ColumnAttr
from visidata.type_date import date


@VisiData.api
def open_ofx(vd, p):
    return OfxIndexSheet(p.base_stem, source=p)


class OfxIndexSheet(IndexSheet):
    rowtype = "sheets"  # rowdef: IndexSheet

    # Not sure how to add these columns without losing the default
    # IndexSheet columns
    # columns = [
    #     ColumnAttr('curdef'),
    #     ColumnAttr('bankid'),
    #     ColumnAttr('acctid'),
    #     ColumnAttr('accttype'),
    #     ColumnAttr('dtstart', date),
    #     ColumnAttr('dtend', date),
    #     ColumnAttr('ledgerbal', Decimal),
    #     ColumnAttr('dtasof', date),
    # ]

    def iterload(self):
        # https://ofxtools.readthedocs.io/en/latest/parser.html#parser
        ofxtools = vd.importExternal("ofxtools")
        OFXTree = ofxtools.Parser.OFXTree
        parser = OFXTree()
        parser.parse(self.source)

        ofx = parser.convert()

        statement_tables = ["transactions", "account", "balances"]

        if statements := getattr(ofx, "statements", None):
            for statement in statements:
                yield OfxStatementTransactionsSheet(statement.acctid, source=statement)


class OfxStatementTransactionsSheet(TableSheet):
    rowtype = "sheets"  # rowdef: ofxtools.models.bank.stmt.STMTTRN

    columns = [
        ColumnAttr("dtposted", type=date),
        ColumnAttr("fitid"),
        ColumnAttr("trntype"),
        ColumnAttr("trnamt", type=float),
        ColumnAttr("memo"),
    ]

    def iterload(self):
        for transaction in self.source.transactions:
            yield transaction


    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    #     self.curdef = self.source.curdef
    #     self.bankid = self.source.bankid
    #     self.acctid = self.source.acctid
    #     self.accttype = self.source.accttype
    #     self.dtstart = self.source.dtstart
    #     self.dtend = self.source.dtend
    #     self.ledgerbal = self.source.ledgerbal
    #     self.dtasof = self.source.dtasof
