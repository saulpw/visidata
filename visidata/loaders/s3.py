"""Allow VisiData to work directly with Amazon S3 paths.

Functionality is more limited than local paths, but supports:

* Navigating among directories (S3 prefixes)
* Opening supported filetypes, including compressed files
* Versioned buckets
"""

import textwrap
from functools import cached_property

from visidata import (
    Column,
    ItemColumn,
    Path,
    Sheet,
    VisiData,
    asyncthread,
    date,
    vd,
)

vd.option(
    "s3_endpoint",
    "",
    "alternate S3 endpoint, used for local testing or alternative S3-compatible services",
    replay=True,
)
vd.option("s3_glob", True, "enable glob-matching for S3 paths", replay=True)
vd.option(
    "s3_version_aware",
    False,
    "show all object versions in a versioned bucket",
    replay=True,
)


class S3Path(Path):
    """A Path-like object representing an S3 file (object) or directory (prefix)."""

    _fs = None

    def __init__(self, path, version_aware=None, version_id=None):
        super().__init__(path)
        self.given = path
        self.version_aware = version_aware or vd.options.s3_version_aware
        self.version_id = self.version_aware and version_id or None

    @property
    def fs(self):
        if self._fs is None:
            s3fs_core = vd.importExternal("s3fs.core", "s3fs")
            self._fs = s3fs_core.S3FileSystem(
                client_kwargs={"endpoint_url": vd.options.s3_endpoint or None},
                version_aware=self.version_aware,
                anon=vd.options.s3_anon,
            )

        return self._fs

    @fs.setter
    def fs(self, val):
        self._fs = val

    def open(self, mode='r', **kwargs):
        """Open the current S3 path, decompressing along the way if needed."""

        fp = self.fs.open(self.given, mode="rb" if self.compression else mode, version_id=self.version_id)

        # Workaround for https://github.com/ajkerrigan/visidata-plugins/issues/12
        if hasattr(fp, "cache") and fp.cache.size != fp.size:
            vd.debug(
                f"updating cache size from {fp.cache.size} to {fp.size} to match object size"
            )
            fp.cache.size = fp.size

        if self.compression == "gz":
            import gzip

            return gzip.open(fp, mode, **kwargs)

        if self.compression == "bz2":
            import bz2

            return bz2.open(fp, mode, **kwargs)

        if self.compression == "xz":
            import lzma

            return lzma.open(fp, mode, **kwargs)

        return fp


class S3DirSheet(Sheet):
    """Display a listing of files and directories (objects and prefixes) in an S3 path.

    Allow single or multiple entries to be opened in separate sheets.
    """

    columns = [
        Column("name", getter=lambda col, row: col.sheet.object_display_name(row)),
        ItemColumn("type"),
        ItemColumn("size", type=int),
        ItemColumn("modtime", "LastModified", type=date),
        ItemColumn("latest", "IsLatest", type=bool),
        ItemColumn("version_id", "VersionId", type=str, width=0),
    ]

    def __init__(self, name, source, version_aware=None):
        import re

        super().__init__(name=name, source=source)
        self.rowtype = "files"
        self.nKeys = 1
        self.use_glob_matching = vd.options.s3_glob and re.search(
            r"[*?\[\]]", self.source.given
        )
        self.version_aware = (
            vd.options.s3_version_aware if version_aware is None else version_aware
        )
        self.fs = source.fs

    @cached_property
    def _display_prefix(self):
        """The source prefix to strip from row names for display."""
        prefix = self.source.given
        if prefix.startswith("s3://"):
            prefix = prefix[5:]
        return prefix.rstrip("/") + "/"

    def object_display_name(self, row):
        """Provide a friendly display name for an S3 path.

        When listing the contents of a single S3 prefix, the name can chop off
        prefix bits to imitate a directory browser. When glob matching,
        include the full key name for each entry.
        """
        if self.use_glob_matching:
            return row.get("name")
        name = row.get("name", "")
        if name.startswith(self._display_prefix):
            return name[len(self._display_prefix):]
        return name.rpartition("/")[2]

    def _yield_entry(self, key, info):
        """Yield row(s) for an S3 key, expanding versions if version-aware."""
        if self.version_aware and info.get("type") == "file":
            yield from (
                {**obj_version, "name": key, "type": "file"}
                for obj_version in self.fs.object_version_info(key)
                if key.partition("/")[2] == obj_version["Key"]
            )
        else:
            yield info

    def _iterdir(self, path, dir_depth, depth=0):
        """Walk S3 path, recursing into directories up to dir_depth levels."""
        for info in self.fs.ls(path, detail=True):
            key = info["name"]
            yield from self._yield_entry(key, info)
            if info.get("type") == "directory" and depth < dir_depth:
                yield from self._iterdir(key, dir_depth, depth + 1)

    def iterload(self):
        """Delegate to the underlying filesystem to fetch S3 entries."""
        if not (
            self.use_glob_matching
            or self.fs.exists(self.source.given)
            or self.fs.isdir(self.source.given)
        ):
            vd.fail(f"unable to open S3 path: {self.source.given}")

        if self.version_aware:
            self.column("latest").hide(False)
        else:
            self.column("latest").hide(True)

        if self.use_glob_matching:
            for info in self.fs.glob(str(self.source), detail=True).values():
                yield from self._yield_entry(info["name"], info)
        else:
            yield from self._iterdir(str(self.source), self.options.dir_depth)

    @asyncthread
    def download(self, rows, savepath):
        """Download files and directories to a local path.

        Recurse through through subdirectories.
        """
        remote_files = [row["name"] for row in rows]
        self.fs.download(remote_files, str(savepath), recursive=True)

    def open_rows(self, rows):
        """Open new sheets for the target rows."""
        return (
            vd.openSource(
                S3Path(
                    "s3://{}".format(row["name"]),
                    version_aware=self.version_aware,
                    version_id=row.get("VersionId"),
                )
            )
            for row in rows
        )

    def join_rows(self, rows):
        """Open new sheets for the target rows and concatenate their contents."""
        sheets = list(self.open_rows(rows))
        for sheet in vd.Progress(sheets):
            sheet.reload()

        # Wait for all sheets to fully load before joining them.
        # 'append' is the only join type that makes sense here,
        # since we're joining freshly opened sheets with no key
        # columns.
        vd.sync()
        return sheets[0].openJoin(sheets[1:], jointype="append")

    def refresh_path(self, path=None):
        """Clear the s3fs cache for the given path and reload.

        By default, clear the entire cache.
        """
        self.fs.invalidate_cache(path)
        self.reload()

    def toggle_versioning(self):
        """Enable or disable support for S3 versioning."""
        self.version_aware = not self.version_aware
        self.fs.version_aware = self.version_aware
        vd.status(f's3 versioning {"enabled" if self.version_aware else "disabled"}')
        if self.currentThreads:
            vd.debug("cancelling threads before reloading")
            vd.cancelThread(*self.currentThreads)
        self.reload()


@VisiData.api
def openurl_s3(vd, p, filetype):
    """Open a sheet for an S3 path.

    S3 directories (prefixes) require special handling, but files (objects)
    can use standard VisiData "open" functions.
    """

    # Non-obvious behavior here: For the default case, we don't want to send
    # a custom endpoint to s3fs. However, using None as a default trips up
    # VisiData's type detection for the endpoint option. So we use an empty
    # string as the default instead, and convert back to None here.
    endpoint = vd.options.s3_endpoint or None

    p = S3Path(
        str(p.given),
        version_aware=getattr(p, "version_aware", vd.options.s3_version_aware),
        version_id=getattr(p, "version_id", None),
    )

    p.fs.version_aware = p.version_aware
    if p.fs.client_kwargs.get("endpoint_url", "") != endpoint:
        p.fs.client_kwargs = {"endpoint_url": endpoint}
        p.fs.connect()

    if not p.fs.isfile(str(p.given)):
        return S3DirSheet(p.base_stem, source=p, version_aware=p.version_aware)

    if not filetype:
        filetype = p.ext or "txt"

    openfunc = getattr(vd, f"open_{filetype.lower()}")
    if not openfunc:
        vd.warning(f"no loader found for {filetype} files, falling back to txt")
        filetype = "txt"
        openfunc = vd.open_txt

    assert callable(openfunc), f"no function/method available to open {p.given}"
    vs = openfunc(p)
    vd.status(
        f'opening {p.given} as {filetype} (version id: {p.version_id or "latest"})'
    )
    return vs


S3DirSheet.addCommand(
    'Enter',
    "s3-open-row",
    "vd.push(next(sheet.open_rows([cursorRow])))",
    "open the current S3 entry",
)
S3DirSheet.addCommand(
    "gEnter",
    "s3-open-rows",
    "for vs in sheet.open_rows(selectedRows): vd.push(vs)",
    "open all selected S3 entries",
)
S3DirSheet.addCommand(
    "zCtrl+R",
    "s3-refresh-sheet",
    "sheet.refresh_path(str(sheet.source))",
    "clear the s3fs cache for this path, then reload",
)
S3DirSheet.addCommand(
    "gzCtrl+R",
    "s3-refresh-sheet-all",
    "sheet.refresh_path()",
    "clear the entire s3fs cache, then reload",
)
S3DirSheet.addCommand(
    "Ctrl+V",
    "s3-toggle-versioning",
    "sheet.toggle_versioning()",
    "enable/disable support for S3 versioning",
)
S3DirSheet.addCommand(
    "&",
    "s3-join-rows",
    "vd.push(sheet.join_rows(selectedRows))",
    "open and join sheets for selected S3 entries",
)
S3DirSheet.addCommand(
    "gx",
    "s3-download-rows",
    textwrap.dedent(
        """
        savepath = inputPath("download selected rows to: ", value=".")
        sheet.download(selectedRows, savepath)
    """
    ),
    "download selected files and directories",
)

S3DirSheet.addCommand(
    "x",
    "s3-download-row",
    textwrap.dedent(
        """
        savepath = inputPath("download to: ", value=Path(cursorRow["name"]).name)
        sheet.download([cursorRow], savepath)
    """
    ),
    "download the file or directory in the cursor row",
)

vd.addMenuItems(
    """
    File > Toggle versioning > s3-toggle-versioning
    File > Refresh > Current path > s3-refresh-sheet
    File > Refresh > All > s3-refresh-sheet-all
    Row > Download > Current row > s3-download-row
    Row > Download > Selected rows > s3-download-rows
    Data > Join > Selected rows > s3-join-rows
"""
)

vd.addGlobals(S3DirSheet=S3DirSheet)
