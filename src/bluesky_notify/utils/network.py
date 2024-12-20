"""Network utility functions."""

import socket
import psutil
import platform
import subprocess

def is_port_in_use(port: int) -> bool:
    """Check if a port is in use.

    Args:
        port: Port number to check

    Returns:
        bool: True if port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def check_service_status() -> dict:
    """Check if the bluesky-notify service is running.

    Returns:
        dict: Service status information
    """
    system = platform.system()
    status = {
        'running': False,
        'mode': None,
        'pid': None,
        'pids': []  # List of all related process IDs
    }

    # First check for daemon mode
    if system == 'Darwin':  # macOS
        try:
            result = subprocess.run(
                ['launchctl', 'list', 'com.bluesky-notify'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                status['running'] = True
                status['mode'] = 'daemon'
                # Try to get PID from launchctl
                try:
                    pid_result = subprocess.run(
                        ['pgrep', '-f', 'bluesky-notify'],
                        capture_output=True,
                        text=True
                    )
                    if pid_result.returncode == 0:
                        pids = [int(pid) for pid in pid_result.stdout.strip().split()]
                        status['pids'] = pids
                        status['pid'] = pids[0] if pids else None
                except:
                    pass
        except Exception:
            pass

    elif system == 'Linux':
        try:
            result = subprocess.run(
                ['systemctl', '--user', 'is-active', 'bluesky-notify'],
                capture_output=True,
                text=True
            )
            if 'active' in result.stdout:
                status['running'] = True
                status['mode'] = 'daemon'
                # Try to get PID using pgrep
                try:
                    pid_result = subprocess.run(
                        ['pgrep', '-f', 'bluesky-notify'],
                        capture_output=True,
                        text=True
                    )
                    if pid_result.returncode == 0:
                        pids = [int(pid) for pid in pid_result.stdout.strip().split()]
                        status['pids'] = pids
                        status['pid'] = pids[0] if pids else None
                except:
                    pass
        except Exception:
            pass

    # If not running in daemon mode, check for terminal mode
    if not status['running']:
        pids = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.cmdline())
                if 'bluesky-notify' in cmdline and 'start' in cmdline:
                    if not status['running']:  # First match sets the main info
                        status['running'] = True
                        status['mode'] = 'terminal'
                        status['pid'] = proc.pid
                    pids.append(proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        status['pids'] = pids

    return status
