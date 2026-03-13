"""
disk.py — Raw disk access via Windows API.

Responsibilities:
  - Enumerate physical disks
  - Open disks for reading/writing
  - Read and write raw sectors in chunks
"""

import ctypes
import ctypes.wintypes as wintypes
import json
import subprocess
from dataclasses import dataclass
from typing import Callable

# ── Windows API constants ─────────────────────────────────────────────────────

GENERIC_READ        = 0x80000000
GENERIC_WRITE       = 0x40000000
FILE_SHARE_READ     = 0x00000001
FILE_SHARE_WRITE    = 0x00000002
OPEN_EXISTING       = 3
INVALID_HANDLE      = wintypes.HANDLE(-1).value
SECTOR_SIZE         = 512
DEFAULT_CHUNK_BYTES = 1 * 1024 * 1024  # 1 MB

IOCTL_DISK_GET_LENGTH_INFO = 0x0007405C
MAX_DISKS                  = 64          # probe up to this disk number
MIN_CHUNK_BYTES            = SECTOR_SIZE
MAX_CHUNK_BYTES            = 128 * 1024 * 1024  # 128 MB ceiling

# ── Disk info ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DiskInfo:
    number: int
    path: str
    size_bytes: int
    friendly_name: str = "Unknown Disk"

    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024 ** 3)

    def __str__(self) -> str:
        return f"Disk {self.number}  {self.friendly_name}  ({self.size_gb:.1f} GB)"


# ── Friendly name lookup (single PowerShell call) ────────────────────────────

def _get_friendly_names() -> dict[int, str]:
    """Return {disk_number: friendly_name} using Get-PhysicalDisk."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-PhysicalDisk | Select-Object DeviceId, FriendlyName | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        if isinstance(data, dict):
            data = [data]  # single disk returns object, not array
        return {int(d["DeviceId"]): d["FriendlyName"] for d in data}
    except (json.JSONDecodeError, KeyError, ValueError, subprocess.TimeoutExpired, OSError):
        return {}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _open_disk(path: str, write: bool = False) -> wintypes.HANDLE:
    access = GENERIC_READ | (GENERIC_WRITE if write else 0)
    share  = FILE_SHARE_READ | FILE_SHARE_WRITE
    handle = ctypes.windll.kernel32.CreateFileW(
        path, access, share, None, OPEN_EXISTING, 0, None
    )
    if handle == INVALID_HANDLE:
        err = ctypes.windll.kernel32.GetLastError()
        raise OSError(f"Cannot open {path} (error {err}). Run as Administrator.")
    return handle


def _get_disk_size(handle: wintypes.HANDLE) -> int:
    size = ctypes.c_int64(0)
    returned = wintypes.DWORD(0)
    ok = ctypes.windll.kernel32.DeviceIoControl(
        handle,
        IOCTL_DISK_GET_LENGTH_INFO,
        None, 0,
        ctypes.byref(size), ctypes.sizeof(size),
        ctypes.byref(returned),
        None,
    )
    if not ok:
        err = ctypes.windll.kernel32.GetLastError()
        raise OSError(f"DeviceIoControl failed (error {err})")
    return size.value


def _close(handle: wintypes.HANDLE) -> None:
    ctypes.windll.kernel32.CloseHandle(handle)


# ── Public API ────────────────────────────────────────────────────────────────

def list_disks() -> list[DiskInfo]:
    """Return a list of available physical disks."""
    names = _get_friendly_names()
    disks = []
    for n in range(MAX_DISKS):
        path = f"\\\\.\\PhysicalDrive{n}"
        try:
            handle = _open_disk(path)
            size   = _get_disk_size(handle)
            _close(handle)
            disks.append(DiskInfo(
                number=n,
                path=path,
                size_bytes=size,
                friendly_name=names.get(n, f"Disk {n}"),
            ))
        except OSError:
            continue
    return disks


def clone(src: int, dst: int, chunk_bytes: int = DEFAULT_CHUNK_BYTES,
          progress_cb: Callable[[int, int], None] | None = None) -> None:
    """
    Clone physical disk `src` to physical disk `dst`, sector by sector.

    progress_cb(bytes_done, total_bytes) is called after each chunk if provided.
    Raises ValueError on safety violations, OSError on I/O failure.
    """
    if src == dst:
        raise ValueError("Source and destination are the same disk.")
    if chunk_bytes < MIN_CHUNK_BYTES or chunk_bytes > MAX_CHUNK_BYTES:
        raise ValueError(
            f"chunk_bytes must be between {MIN_CHUNK_BYTES} and {MAX_CHUNK_BYTES}, "
            f"got {chunk_bytes}."
        )

    src_path = f"\\\\.\\PhysicalDrive{src}"
    dst_path = f"\\\\.\\PhysicalDrive{dst}"

    src_handle = _open_disk(src_path, write=False)
    try:
        src_size = _get_disk_size(src_handle)
        dst_handle = _open_disk(dst_path, write=True)
        try:
            dst_size = _get_disk_size(dst_handle)
            if dst_size < src_size:
                raise ValueError(
                    f"Destination ({dst_size} bytes) is smaller than "
                    f"source ({src_size} bytes)."
                )
            _stream_copy(src_handle, dst_handle, src_size, chunk_bytes, progress_cb)
        finally:
            _close(dst_handle)
    finally:
        _close(src_handle)


def _stream_copy(src, dst, total_bytes, chunk_bytes, progress_cb) -> None:
    """Read src in chunks and write to dst."""
    kernel32    = ctypes.windll.kernel32
    bytes_done  = 0
    buf         = ctypes.create_string_buffer(chunk_bytes)
    read_out    = wintypes.DWORD(0)
    write_out   = wintypes.DWORD(0)

    while bytes_done < total_bytes:
        remaining = total_bytes - bytes_done
        to_read   = min(chunk_bytes, remaining)

        ok = kernel32.ReadFile(src, buf, to_read, ctypes.byref(read_out), None)
        if not ok or read_out.value == 0:
            err = kernel32.GetLastError()
            raise OSError(f"Read failed at byte {bytes_done} (error {err})")

        ok = kernel32.WriteFile(dst, buf, read_out.value, ctypes.byref(write_out), None)
        if not ok or write_out.value != read_out.value:
            err = kernel32.GetLastError()
            raise OSError(f"Write failed at byte {bytes_done} (error {err})")

        bytes_done += read_out.value
        if progress_cb:
            progress_cb(bytes_done, total_bytes)
