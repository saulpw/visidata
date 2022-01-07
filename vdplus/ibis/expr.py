import ibis
import ibis.expr.types as ir
from itertools import zip_longest
from collections import defaultdict, abc
from typing import Any, Dict, Set

import ibis.expr.operations as ops
import ibis.expr.types as ir
import ibis.util as util

from visidata import Sheet, AttrColumn, VisiData, vd


class IbisNode:
    __slots__ = 'expr parents children props'.split()
    def __init__(self, expr, parents=[], **kwargs):
        self.expr = expr
        self.parents = parents  # list of IbisNode references up to the expression root
        self.children = []  # list of IbisNode
        self.props = kwargs  #  dict of property_name -> value or list of values or nested dict

    def __setitem__(self, k, v):
        self.props[k] = v

    def __getitem__(self, k):
        return self.props[k]

    def __getattr__(self, k):
        if k in self.__slots__:
            return super().__getattr__(k)
        else:
            self.__getitem__(k)

    def __setattr__(self, k, v):
        if k in self.__slots__:
            super().__setattr__(k, v)
        else:
            self.__setitem__(k, v)


# source is ibis expr
class IbisExprSheet(Sheet):
    columns = [
        AttrColumn('expr'),
        AttrColumn('props'),
        AttrColumn('children'),
        AttrColumn('parents'),
    ]

    def iterload(self):
        self.rows = []
        yield from self.iter_expr(self.source)

    def iter_expr(self, expr, parents=[]):
        x = IbisNode(expr, parents, name=expr._safe_name)

        yield x

        op = expr.op()
        if isinstance(op, ops.PhysicalTable):
            x.name = op.name
            x.type = f'{type(op).__name__}[{expr._type_display()}]'
            x.schema = dict(zip(op.schema.names, op.schema.types))

        for name, arg in zip_longest(op.argnames, op.args):
            if not isinstance(arg, abc.Iterable) or isinstance(arg, str):
                x[name] = arg
                continue

            x[name] = []
            for a in arg:
                if isinstance(a, ir.Expr):
                    n = IbisNode(a, parents)
                    x[name].append(n)
                    x.children.append(n)
                    yield from self.iter_expr(a, parents=parents + [x])
                else:
                    x[name].append(a)


@VisiData.api
def open_tpch22(vd, p):
    con = ibis.sqlite.connect(str(p))
    return IbisExprSheet('tpch22', source=tpc_h22(con))


def tpc_h22(con, COUNTRY_CODES=(13, 31, 23, 29, 30, 18, 17)):
    try:
        customer = con.table('customer')
        orders = con.table('orders')

        q = customer.filter([
            customer.C_ACCTBAL > 0.00,
            customer.C_PHONE.substr(1,2).isin(COUNTRY_CODES),
        ])
        q = q.group_by().aggregate(avg_bal=customer.C_ACCTBAL.mean())

#    q2 = orders.filter([orders.O_CUSTKEY == customer.C_CUSTKEY])
        custsale = customer.filter([
            customer.C_PHONE.substr(1,2).isin(COUNTRY_CODES),
            customer.C_ACCTBAL > q.avg_bal,
            ~(orders.O_CUSTKEY == customer.C_CUSTKEY).any()
        ])
        custsale = custsale[
            customer.C_PHONE.substr(1,2).name('cntrycode'),
            customer.C_ACCTBAL
        ]

        gq = q.group_by(custsale.cntrycode)
        q = gq.aggregate(totacctbal=custsale.C_ACCTBAL.sum())

        q = q.sort_by(q.cntrycode)
    except Exception as e:
        vd.warning(str(e))
        if vd.options.debug:
            raise

    return q
