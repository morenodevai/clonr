"""
test_clone.py — Verify clone correctness against VHD test disks.

Writes a known pattern to Disk 4, clones to Disk 5, reads back and compares.
Run as Administrator.
"""

import ctypes
import ctypes.wintypes as wintypes
import sys
from clonr import disk
from clonr.disk import (
    GENERIC_READ, GENERIC_WRITE,
    FILE_SHARE_READ, FILE_SHARE_WRITE,
    OPEN_EXISTING, SECTOR_SIZE,
)

SRC     = 4
DST     = 5
PATTERN = b"CLONR_TEST_PATTERN_" * 26   # 494 bytes — fits cleanly within one 512-byte sector


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except OSError:
        return False


def write_pattern(drive_number: int, pattern: bytes) -> None:
    path   = f"\\\\.\\PhysicalDrive{drive_number}"
    handle = ctypes.windll.kernel32.CreateFileW(
        path, GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None, OPEN_EXISTING, 0, None
    )
    if handle == wintypes.HANDLE(-1).value:
        raise OSError(f"Cannot open {path}")

    buf          = ctypes.create_string_buffer(SECTOR_SIZE)
    buf[:len(pattern)] = pattern
    written      = wintypes.DWORD(0)
    ok = ctypes.windll.kernel32.WriteFile(handle, buf, SECTOR_SIZE, ctypes.byref(written), None)
    ctypes.windll.kernel32.CloseHandle(handle)
    if not ok:
        raise OSError("Write failed")


def read_sector(drive_number: int) -> bytes:
    path   = f"\\\\.\\PhysicalDrive{drive_number}"
    handle = ctypes.windll.kernel32.CreateFileW(
        path, GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None, OPEN_EXISTING, 0, None
    )
    if handle == wintypes.HANDLE(-1).value:
        raise OSError(f"Cannot open {path}")

    buf  = ctypes.create_string_buffer(SECTOR_SIZE)
    read = wintypes.DWORD(0)
    ok   = ctypes.windll.kernel32.ReadFile(handle, buf, SECTOR_SIZE, ctypes.byref(read), None)
    ctypes.windll.kernel32.CloseHandle(handle)
    if not ok:
        raise OSError("Read failed")
    return bytes(buf)


def progress(done, total):
    pct = done / total * 100
    bar = "#" * int(30 * done / total) + "-" * (30 - int(30 * done / total))
    print(f"\r  [{bar}] {pct:.1f}%", end="", flush=True)
    if done == total:
        print()


def main():
    if not is_admin():
        print("ERROR: Must run as Administrator.")
        sys.exit(1)

    print(f"\n[1] Writing test pattern to Disk {SRC}...")
    write_pattern(SRC, PATTERN)
    print("    Done.")

    print(f"\n[2] Cloning Disk {SRC} -> Disk {DST}...")
    disk.clone(SRC, DST, progress_cb=progress)

    print(f"\n[3] Reading back first sector from Disk {DST}...")
    result = read_sector(DST)

    # Verify the full pattern fits within the sector and matches exactly
    assert len(PATTERN) <= SECTOR_SIZE, "Pattern exceeds sector size — fix the test"
    match = result[:len(PATTERN)] == PATTERN

    if match:
        print("\n  PASS - Clone verified. Pattern matches.")
    else:
        print("\n  FAIL - Mismatch detected.")
        print(f"  Expected: {PATTERN[:32]}")
        print(f"  Got:      {result[:32]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
