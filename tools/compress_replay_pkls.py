#!/usr/bin/env python3
"""Gzip existing replay.pkl files in place (keep the filename).

Does not change collect/eval: new runs still write uncompressed pickle.
Already-gzipped files are skipped.

  python tools/compress_replay_pkls.py data/trajectories/no_turn_left/final
  python tools/compress_replay_pkls.py data/trajectories/no_turn_left/final --jobs 8
"""
from __future__ import annotations

import argparse
import gzip
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

GZIP_MAGIC = b"\x1f\x8b"


def gzip_file_inplace(path: str, compresslevel: int = 1) -> tuple[str, int, int]:
    p = Path(path)
    if not p.is_file():
        return ("missing", 0, 0)
    before = p.stat().st_size
    if before <= 0:
        return ("empty", before, before)
    with open(p, "rb") as f:
        magic = f.read(2)
        if magic == GZIP_MAGIC:
            return ("skip", before, before)
        f.seek(0)
        tmp = p.with_name(p.name + ".gztmp")
        try:
            with gzip.open(tmp, "wb", compresslevel=compresslevel) as out:
                shutil.copyfileobj(f, out, 1024 * 1024)
            after = tmp.stat().st_size
            os.replace(tmp, p)
            return ("ok", before, after)
        except Exception:
            if tmp.exists():
                tmp.unlink()
            raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="Sign final/ dir or any tree of replay.pkl")
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--compresslevel", type=int, default=1)
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    files = [str(x) for x in root.rglob("replay.pkl") if x.is_file()]
    n = len(files)
    print(f"found {n} replay.pkl under {root}  jobs={args.jobs}", flush=True)
    if n == 0:
        return 0

    t0 = time.time()
    ok = skip = empty = fail = 0
    before = after = 0
    done = 0
    with ProcessPoolExecutor(max_workers=max(1, args.jobs)) as ex:
        futs = [
            ex.submit(gzip_file_inplace, f, args.compresslevel) for f in files
        ]
        for fut in as_completed(futs):
            done += 1
            try:
                status, b, a = fut.result()
            except Exception as exc:
                fail += 1
                print(f"FAIL {exc}", file=sys.stderr, flush=True)
                continue
            before += b
            after += a
            if status == "ok":
                ok += 1
            elif status == "skip":
                skip += 1
            else:
                empty += 1
            if done % 200 == 0 or done == n:
                saved = before - after
                print(
                    f"  {done}/{n}  ok={ok} skip={skip} empty={empty} fail={fail}  "
                    f"saved={saved/1e9:.2f} GB  elapsed={time.time()-t0:.0f}s",
                    flush=True,
                )

    dt = time.time() - t0
    saved = before - after
    remain = (after / before) if before else 1.0
    print(
        f"done  ok={ok} skip={skip} empty={empty} fail={fail}  "
        f"before={before/1e9:.2f} GB  after={after/1e9:.2f} GB  "
        f"freed={saved/1e9:.2f} GB  ({remain:.1%} remain)  {dt:.0f}s",
        flush=True,
    )
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
