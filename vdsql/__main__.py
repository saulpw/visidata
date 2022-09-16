#!/usr/bin/env python3

def main():
    import ibis
    from visidata import main, vd

    import vdsql as _  # noqa: F401

    for ext in "db ddb duckdb sqlite sqlite3".split():
        setattr(vd, f"open_{ext}", vd.open_vdsql)

    for entry_point in ibis.util.backend_entry_points():
        attrname = f"openurl_{entry_point.name}"
        if not hasattr(vd, attrname):
            setattr(vd, attrname, vd.open_vdsql)

    main.vd_cli()


if __name__ == "__main__":
    main()
