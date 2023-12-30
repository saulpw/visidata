"""
Column types and utility commands related to IP addresses.
"""
from ipaddress import ip_address, ip_network, _BaseNetwork

from visidata import vd
from visidata.sheets import Column, TableSheet


vd.addType(ip_address, icon=":", formatter=lambda fmt, ip: str(ip))
vd.addType(ip_network, icon="/", formatter=lambda fmt, ip: str(ip))


def isSupernet(cell, network, isNull):
    """Is `cell` a supernet of `network`?

    Treat nulls as false, and perform conversions to IP network objects only
    if necessary.
    """
    if isNull(cell):
        return False
    if not isinstance(cell, _BaseNetwork):
        try:
            cell = ip_network(str(cell).strip())
        except ValueError:
            return False
    return cell.supernet_of(network)


@Column.api
def selectSupernets(col, ip):
    """Select rows based on network containment

    Given an IP address (e.g. 10.0.0.0) or network (e.g. 10.0.0.0/8) as input,
    select rows whose network address space completely contains the input network.
    """
    if not ip:
        return

    sheet = col.sheet
    network = ip_network(ip.strip())
    isNull = sheet.isNullFunc()

    vd.status(f'selecting rows where {col.name} is a supernet of "{str(network)}"')
    sheet.select(
        [
            row
            for row in sheet.rows
            if isSupernet(col.getTypedValue(row), network, isNull)
        ]
    )


TableSheet.addCommand(
    None,
    "type-ipaddr",
    "cursorCol.type=ip_address",
    "set type of current column to IP address",
)
TableSheet.addCommand(
    None,
    "type-ipnet",
    "cursorCol.type=ip_network",
    "set type of current column to IP network",
)
TableSheet.addCommand(
    None,
    "select-supernets",
    'cursorCol.selectSupernets(input("ip or cidr block: "))',
    "select rows where the CIDR block value includes the input address space",
)

vd.addGlobals(ip_address=ip_address, ip_network=ip_network)
