#!/usr/bin/env python3
'''Build orders-flat.jsonl, tinyshop.jsonl and petshop.sqlite from the canonical tables in sample_data/petshop/petshop.vds.'''

import json
import os
import sqlite3
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
PETSHOP = REPO/'sample_data'/'petshop'

TABLES = {
    'customers': 'customerid integer, name text, address text, citystatezip text, birthdate text, phone text, location json',
    'products': 'sku text, desc text, live, wholesale_cost text, dims_cm json',
    'orders': 'orderid text, customerid, ordered text, source text, shipped timestamp, total text, total_usd text',
    'orders_items': 'orderid integer, sku text, qty integer, unit_price text',
}

ORDER_TOTALS_VIEW = '''
CREATE VIEW order_totals AS
    SELECT o.orderid, o.customerid, o.ordered, count(i.orderid) AS nitems, sum(i.qty) AS qty, o.total_usd
    FROM orders o LEFT JOIN orders_items i ON i.orderid = CAST(o.orderid AS integer)
    GROUP BY o.orderid
    ORDER BY CAST(o.orderid AS integer)
'''

WIDE_COLUMNS = 'ordered source name sku desc live qty unit_price wholesale_cost total total_usd'.split()

ORDER_COLUMNS = 'ordered source total total_usd'.split()
CUSTOMER_COLUMNS = 'name'.split()
ITEM_COLUMNS = 'qty unit_price'.split()
PRODUCT_COLUMNS = 'desc live wholesale_cost'.split()

# (orderid, sku) in orders-flat.jsonl: clean, fully matched lines only
TINYSHOP = [(5001, 'FUD0213'), (5005, 'PET0342'), (5007, 'COL0523'), (5011, 'TOY0235'),
           (5010, 'FUD0167'), (5038, 'FUD0215'), (5040, 'PET0110'), (5040, 'FUD0130'),
           (5041, 'PET0095'), (5041, 'HOM0120'), (5046, 'PET0115'), (5051, 'FUD0219')]

MISSING = object()


def read_vds(path):
    'Return {sheetname: [rowdict]} from the .vds at *path*; fail on any typed column.'
    sheets, rows = {}, None
    with open(path, encoding='utf-8') as fp:
        for line in fp:
            if line.startswith('#{'):
                d = json.loads(line[1:])
                if 'col' not in d:
                    rows = sheets[d['name']] = []
                elif d.get('typestr'):
                    raise SystemExit(f'{path}: column {d["name"]} has type {d["typestr"]}; canonical columns stay untyped')
            elif line.strip():
                rows.append(json.loads(line))
    return sheets


def write_jsonl(path, rows):
    'Write the WIDE_COLUMNS of *rows* with every column on row 0 (null where missing), so loaders fix the column order.'
    tmp = path.with_name(path.name + '.tmp')
    with open(tmp, 'w', encoding='utf-8') as fp:
        for i, row in enumerate(rows):
            row = {c: row[c] for c in WIDE_COLUMNS}
            if i == 0:
                d = {k: (None if v is MISSING else v) for k, v in row.items()}
            else:
                d = {k: v for k, v in row.items() if v is not MISSING}
            fp.write(json.dumps(d, ensure_ascii=False) + '\n')
    os.replace(tmp, path)


def int_key(v):
    'Return *v* as an int join key, or None if it is null or not a number (a phone number typed into customerid).'
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def take(src, cols):
    'Return {col: value} from *src*, keeping keys that *src* lacks as MISSING; all None if no *src*.'
    if src is None:
        return {c: None for c in cols}
    return {c: src.get(c, MISSING) for c in cols}


def first(*vals):
    return next((v for v in vals if v is not None), None)


def wide_row(item, order, cust, prod):
    r = dict.fromkeys(WIDE_COLUMNS)
    r['orderid'] = int_key(first(item and item.get('orderid'), order and order.get('orderid')))
    r['sku'] = first(item and item.get('sku'), prod and prod.get('sku'))
    r.update(take(order, ORDER_COLUMNS))
    r.update(take(cust, CUSTOMER_COLUMNS))
    r.update(take(item, ITEM_COLUMNS))
    r.update(take(prod, PRODUCT_COLUMNS))
    return r


def join_wide(customers, products, orders, items):
    '''Full outer join at line grain: orders_items, orders on orderid, customers on customerid, products on sku.
    Keys match as int across the str/int split; null and empty keys never match.'''
    orders_by_id = {}
    for o in orders:
        orders_by_id.setdefault(int_key(o['orderid']), []).append(o)
    custs_by_id = {}
    for c in customers:
        custs_by_id.setdefault(int_key(c['customerid']), []).append(c)
    prods_by_sku = {}
    for p in products:
        prods_by_sku.setdefault(p['sku'], []).append(p)

    used_orders, used_custs, used_prods = set(), set(), set()

    def lines(item, order):
        custs = custs_by_id.get(int_key(order and order.get('customerid')), [None]) if order else [None]
        sku = item and item.get('sku')
        prods = prods_by_sku.get(sku, [None]) if sku else [None]
        for c in custs:
            if c is not None:
                used_custs.add(id(c))
            for p in prods:
                if p is not None:
                    used_prods.add(id(p))
                yield wide_row(item, order, c, p)

    rows = []
    for item in items:
        for order in orders_by_id.get(int_key(item['orderid']), [None]):
            if order is not None:
                used_orders.add(id(order))
            rows.extend(lines(item, order))

    for order in orders:
        if id(order) not in used_orders:
            rows.extend(lines(None, order))

    rows.sort(key=lambda r: r['orderid'])  # stable: lines of one order keep item order

    rows.extend(wide_row(None, None, c, None) for c in customers if id(c) not in used_custs)
    rows.extend(wide_row(None, None, None, p) for p in products if id(p) not in used_prods)
    return rows


def sqlvalue(v):
    return json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v


def write_sqlite(path, tables):
    tmp = path.with_name(path.name + '.tmp')
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    for name, schema in TABLES.items():
        cols = [c.split()[0] for c in schema.split(', ')]
        con.execute(f'CREATE TABLE {name} ({schema})')
        con.executemany(f'INSERT INTO {name} VALUES ({",".join("?"*len(cols))})',
                        [[sqlvalue(r.get(c)) for c in cols] for r in tables[name]])
    con.execute(ORDER_TOTALS_VIEW)
    con.commit()
    con.close()
    os.replace(tmp, path)


def build_canonical():
    tables = read_vds(PETSHOP/'petshop.vds')
    wide = join_wide(tables['customers'], tables['products'], tables['orders'], tables['orders_items'])
    assert len(wide) == 71, f'wide join has {len(wide)} rows, not 71'

    write_jsonl(PETSHOP/'orders-flat.jsonl', wide)
    write_jsonl(PETSHOP/'tinyshop.jsonl', [r for r in wide if (r['orderid'], r['sku']) in TINYSHOP])
    write_sqlite(PETSHOP/'petshop.sqlite', tables)


if __name__ == '__main__':
    build_canonical()
