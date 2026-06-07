from __future__ import annotations

import argparse
import os
from pathlib import Path
import signal
import socket
import sys
import time


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def _project_root() -> Path:
    candidate = Path(__file__).resolve()
    for parent in [candidate.parent, *candidate.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def _listening_socket_inodes(port: int) -> set[str]:
    inodes: set[str] = set()
    for proc_file in (Path("/proc/net/tcp"), Path("/proc/net/tcp6")):
        if not proc_file.exists():
            continue

        for line in proc_file.read_text(encoding="utf-8").splitlines()[1:]:
            columns = line.split()
            if len(columns) < 10:
                continue
            local_address = columns[1]
            state = columns[3]
            inode = columns[9]
            try:
                local_port = int(local_address.rsplit(":", 1)[1], 16)
            except (IndexError, ValueError):
                continue
            if local_port == port and state == "0A":
                inodes.add(inode)
    return inodes


def _pids_for_socket_inodes(inodes: set[str]) -> set[int]:
    if not inodes:
        return set()

    pids: set[int] = set()
    try:
        proc_dirs = tuple(Path("/proc").iterdir())
    except OSError:
        return pids

    for proc_dir in proc_dirs:
        if not proc_dir.name.isdigit():
            continue
        fd_dir = proc_dir / "fd"
        try:
            fd_paths = tuple(fd_dir.iterdir())
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            continue

        for fd_path in fd_paths:
            try:
                target = os.readlink(fd_path)
            except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
                continue
            if target.startswith("socket:[") and target.removeprefix("socket:[").removesuffix("]") in inodes:
                pids.add(int(proc_dir.name))
                break
    return pids


def _cmdline(pid: int) -> str:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return ""
    return raw.replace(b"\x00", b" ").decode("utf-8", errors="replace").strip()


def _is_marbts_ui_process(pid: int) -> bool:
    cmdline = _cmdline(pid)
    return "marbts_ui.server" in cmdline or "marbts-ui" in cmdline


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _terminate_pid(pid: int, timeout_seconds: float = 5.0) -> None:
    print(f"Stopping existing MARBTS UI process pid={pid}", flush=True)
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _pid_exists(pid):
            return
        time.sleep(0.1)

    if _pid_exists(pid):
        print(f"Process pid={pid} did not exit after SIGTERM; sending SIGKILL", flush=True)
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            return


def _find_listening_pids(port: int) -> set[int]:
    return _pids_for_socket_inodes(_listening_socket_inodes(port))


def _port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def _stop_existing_server(host: str, port: int, *, force: bool) -> None:
    pids = _find_listening_pids(port)
    if not pids:
        print(f"No existing listener found on {host}:{port}; starting server", flush=True)
        return

    unknown_pids = sorted(pid for pid in pids if not _is_marbts_ui_process(pid))
    if unknown_pids and not force:
        details = ", ".join(f"{pid} ({_cmdline(pid) or 'unknown command'})" for pid in unknown_pids)
        raise SystemExit(
            f"Port {port} is already in use, but not by a recognized MARBTS UI process: {details}\n"
            "Use --force to stop the process anyway."
        )

    for pid in sorted(pids):
        _terminate_pid(pid)

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if _port_is_free(host, port):
            print(f"Port {port} is free; restarting server", flush=True)
            return
        time.sleep(0.1)
    raise SystemExit(f"Port {port} is still busy after stopping existing process(es)")


def _server_env(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    src_path = str(root / "src")
    existing_pythonpath = env.get("PYTHONPATH", "")
    paths = [src_path]
    if existing_pythonpath:
        paths.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Restart the local MARBTS UI server, or start it if it is not running.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Stop any process using the selected port, even if it is not recognized as MARBTS UI.",
    )
    args = parser.parse_args()

    root = _project_root()
    if os.geteuid() == 0 and not sys.executable.startswith(str(root / ".venv")):
        print(
            "Warning: running with sudo is usually unnecessary and may bypass the repo .venv. "
            "Prefer: python scripts/restart_marbts_ui.py",
            flush=True,
        )

    os.chdir(root)
    _stop_existing_server(args.host, args.port, force=args.force)

    command = [
        sys.executable,
        "-m",
        "marbts_ui.server",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    print(f"Starting MARBTS UI at http://{args.host}:{args.port}", flush=True)
    os.execvpe(sys.executable, command, _server_env(root))


if __name__ == "__main__":
    main()
