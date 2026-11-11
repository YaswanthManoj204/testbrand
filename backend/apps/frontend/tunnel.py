import os
import re
import time
import shutil
import subprocess
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TUNNEL_URL_FILE = BASE_DIR / '.tunnel_url'
TUNNEL_PID_FILE = BASE_DIR / '.tunnel_pid'
TUNNEL_LOCK = threading.Lock()


def is_pid_alive(pid):
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        return False

    try:
        res = subprocess.run(['ps', '-p', str(pid), '-o', 'comm='], capture_output=True, text=True, timeout=1)
        if res.returncode == 0:
            return 'cloudflared' in res.stdout
    except Exception:
        pass
    return True


def cleanup_tunnel_files():
    try:
        if TUNNEL_URL_FILE.exists():
            TUNNEL_URL_FILE.unlink()
        if TUNNEL_PID_FILE.exists():
            TUNNEL_PID_FILE.unlink()
    except Exception:
        pass


def get_current_tunnel_url():
    """
    Returns the active tunnel URL if the tunnel process is running.
    If the process is dead, cleans up the stale URL file.
    """
    if TUNNEL_PID_FILE.exists() and TUNNEL_URL_FILE.exists():
        try:
            pid = int(TUNNEL_PID_FILE.read_text().strip())
            if is_pid_alive(pid):
                url = TUNNEL_URL_FILE.read_text().strip()
                if url.startswith('https://') and 'trycloudflare.com' in url:
                    return url
            else:
                cleanup_tunnel_files()
        except Exception:
            cleanup_tunnel_files()
    return None


def start_tunnel_process():
    """
    Spawns cloudflared in the background and extracts the active public URL.
    """
    cloudflared_bin = shutil.which('cloudflared') or '/opt/homebrew/bin/cloudflared'
    if not os.path.exists(cloudflared_bin) and not shutil.which(cloudflared_bin):
        return None

    active_url = get_current_tunnel_url()
    if active_url:
        return active_url

    with TUNNEL_LOCK:
        active_url = get_current_tunnel_url()
        if active_url:
            return active_url

        cleanup_tunnel_files()

        log_path = BASE_DIR / 'cloudflared.log'
        log_file = open(log_path, 'w')

        try:
            proc = subprocess.Popen(
                [cloudflared_bin, 'tunnel', '--url', 'http://127.0.0.1:8000'],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setpgrp,
                close_fds=True
            )
            TUNNEL_PID_FILE.write_text(str(proc.pid))
        except Exception as e:
            print(f"Error launching cloudflared: {e}")
            return None

        # Wait up to 10 seconds for the URL to appear in the log file
        found_url = None
        for _ in range(20):
            time.sleep(0.5)
            if not is_pid_alive(proc.pid):
                break
            try:
                with open(log_path, 'r') as f:
                    content = f.read()
                    m = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', content)
                    if m:
                        found_url = m.group(0)
                        break
            except Exception:
                pass

        if found_url:
            TUNNEL_URL_FILE.write_text(found_url)
            return found_url

    return None


def get_or_start_tunnel_url():
    """
    Returns an active, verified tunnel URL. If none is running, launches it automatically.
    """
    url = get_current_tunnel_url()
    if url:
        return url
    return start_tunnel_process()


def stop_tunnel():
    """
    Kills the active cloudflared process and deletes the state files.
    """
    if TUNNEL_PID_FILE.exists():
        try:
            pid = int(TUNNEL_PID_FILE.read_text().strip())
            if is_pid_alive(pid):
                os.kill(pid, 15)  # SIGTERM
                time.sleep(0.5)
                if is_pid_alive(pid):
                    os.kill(pid, 9)  # SIGKILL
        except Exception:
            pass
    cleanup_tunnel_files()
