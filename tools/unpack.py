"""Unpack an F1 Manager 24 .sav into its SQLite databases.

Layout (found in step 1a):
    [GVAS header ...]
    u32 compressed_size   # bytes of zlib data that follow
    u32 db_size[3]        # size of each database after decompression
    [zlib data]           # the three databases, back to back

Read-only: the .sav is never modified.
Usage: python unpack.py <file.sav> [out_dir]
"""
import re
import sqlite3
import struct
import sys
import zlib
from pathlib import Path

SQLITE_MAGIC = b"SQLite format 3\x00"


def find_block(data: bytes) -> int:
    """Return the offset where the zlib data starts."""
    for m in re.finditer(rb"\x78[\x01\x5e\x9c\xda]", data):
        start = m.start()
        if start < 16:
            continue
        (compressed_size,) = struct.unpack_from("<I", data, start - 16)
        if compressed_size != len(data) - start:
            continue
        try:
            head = zlib.decompressobj().decompress(data[start:], len(SQLITE_MAGIC))
        except zlib.error:
            continue
        if head == SQLITE_MAGIC:
            return start
    raise ValueError("no database block found")


def unpack(sav_path: Path, out_dir: Path) -> list[Path]:
    data = sav_path.read_bytes()
    start = find_block(data)
    db_sizes = struct.unpack_from("<3I", data, start - 12)
    raw = zlib.decompress(data[start:])
    if len(raw) != sum(db_sizes):
        raise ValueError(f"size mismatch: got {len(raw)}, header says {sum(db_sizes)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    paths, offset = [], 0
    for i, size in enumerate(db_sizes, 1):
        chunk = raw[offset:offset + size]
        offset += size
        if not chunk.startswith(SQLITE_MAGIC):
            raise ValueError(f"database {i} is not SQLite")
        path = out_dir / f"{sav_path.stem}_db{i}.sqlite"
        path.write_bytes(chunk)
        paths.append(path)
    return paths


def main() -> None:
    sav = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else sav.parent
    for path in unpack(sav, out_dir):
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        con.close()
        print(f"{path.name}: {path.stat().st_size:,} bytes, {len(tables)} tables")


if __name__ == "__main__":
    main()
