"""
cli.py — Command-line interface for Clonr.

Commands:
  clonr list              List all physical disks
  clonr clone <src> <dst> Clone disk <src> to disk <dst>
"""

import sys
import time
import argparse
from clonr import disk
from clonr.constants import ETA_CAP_SECONDS


# ── Progress display ──────────────────────────────────────────────────────────

def _make_progress_cb(start_time: float):
    def cb(done: int, total: int) -> None:
        pct     = done / total * 100
        elapsed = time.monotonic() - start_time
        speed   = done / elapsed if elapsed > 0 else 0
        if speed > 0:
            eta_secs = (total - done) / speed
            eta_str  = f"{eta_secs:.0f}s" if eta_secs <= ETA_CAP_SECONDS else "calculating..."
        else:
            eta_str  = "calculating..."
        bar_len = 30
        filled  = int(bar_len * done / total)
        bar     = "#" * filled + "-" * (bar_len - filled)
        print(
            f"\r  [{bar}] {pct:5.1f}%  "
            f"{done / 1e9:.2f}/{total / 1e9:.2f} GB  "
            f"{speed / 1e6:.1f} MB/s  "
            f"ETA {eta_str}   ",
            end="", flush=True
        )
        if done == total:
            print()
    return cb


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_list(_args) -> int:
    disks = disk.list_disks()
    if not disks:
        print("No disks found. Run as Administrator.")
        return 1
    print(f"\n  {'#':<4} {'Name':<30} {'Size':>10}\n  " + "-" * 48)
    for d in disks:
        print(f"  {d.number:<4} {d.friendly_name:<30} {d.size_gb:>9.1f} GB")
    print()
    return 0


def cmd_clone(args) -> int:
    src, dst = args.src, args.dst

    disks = {d.number: d for d in disk.list_disks()}
    if src not in disks:
        print(f"Error: Disk {src} not found.")
        return 1
    if dst not in disks:
        print(f"Error: Disk {dst} not found.")
        return 1

    src_info = disks[src]
    dst_info = disks[dst]

    # Size check before asking for confirmation — don't waste the user's time
    if dst_info.size_bytes < src_info.size_bytes:
        print(
            f"\n  Error: destination ({dst_info.size_gb:.1f} GB) is smaller "
            f"than source ({src_info.size_gb:.1f} GB). Aborting."
        )
        return 1

    print(f"\n  Source : {src_info}")
    print(f"  Dest   : {dst_info}")
    print(f"\n  WARNING: All data on Disk {dst} will be permanently erased.")
    answer = input("  Type YES to continue: ").strip()
    if answer != "YES":
        print("  Aborted.")
        return 0

    print(f"\n  Cloning Disk {src} -> Disk {dst} ...\n")
    start = time.monotonic()
    try:
        disk.clone(src, dst, progress_cb=_make_progress_cb(start))
    except (ValueError, OSError) as e:
        print(f"\n  Error: {e}")
        return 1

    elapsed = time.monotonic() - start
    print(f"  Done in {elapsed:.1f}s.")
    return 0


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="clonr",
        description="Clonr -- free, open-source disk cloning tool",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all physical disks")

    p_clone = sub.add_parser("clone", help="Clone one disk to another")
    p_clone.add_argument("src", type=int, metavar="SRC", help="Source disk number")
    p_clone.add_argument("dst", type=int, metavar="DST", help="Destination disk number")

    args = parser.parse_args()

    if args.command == "list":
        sys.exit(cmd_list(args))
    elif args.command == "clone":
        sys.exit(cmd_clone(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
