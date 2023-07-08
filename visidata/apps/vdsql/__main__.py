#!/usr/bin/env python3

def main():
    import ibis
    import visidata
    from visidata import main, vd

    from . import __version__
    visidata.__version_info__ = f'vdsql {__version__}'

    for ext in "db ddb duckdb sqlite sqlite3".split():
        setattr(vd, f"open_{ext}", vd.open_vdsql)

    for entry_point in ibis.util.backend_entry_points():
        if entry_point.name in ['bigquery', 'clickhouse', 'snowflake']:
            # these have their own custom openurl_ funcs already installed
            continue

        attrname = f"openurl_{entry_point.name}"
        # when running vdsql directly, override visidata builtin loader with vdsql loader #1929
        setattr(vd, attrname, vd.open_vdsql)

    main.vd_cli()


if __name__ == "__main__":
    main()
