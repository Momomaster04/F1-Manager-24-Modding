"""Repack SQLite databases into an F1 Manager 24 .sav.

Takes the original .sav (for its GVAS header) and the three databases,
and writes a new .sav. The original .sav is never modified, and an
existing output file is never overwritten.

Usage: python repack.py <original.sav> <db1> <db2> <db3> <out.sav>
"""
import struct
import sys
import zlib
from pathlib import Path

from unpack import find_block


def repack(original: Path, dbs: list[Path], out: Path, level: int = 6) -> None:
    if out.exists():
        raise FileExistsError(f"{out} already exists, refusing to overwrite")
    data = original.read_bytes()
    header = data[:find_block(data) - 16]

    chunks = [db.read_bytes() for db in dbs]
    compressed = zlib.compress(b"".join(chunks), level)
    sizes = struct.pack("<4I", len(compressed), *(len(c) for c in chunks))
    out.write_bytes(header + sizes + compressed)


def main() -> None:
    original, *dbs, out = map(Path, sys.argv[1:])
    if len(dbs) != 3:
        sys.exit(__doc__)
    repack(original, dbs, out)
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
