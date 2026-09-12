import os
import sys
import re
import shutil
import subprocess
import time

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URL_FILE = os.path.join(BASE_DIR, "tunnel_url.txt")
CLOUDFLARED_EXE = os.path.join(BASE_DIR, "cloudflared.exe")


def run_ssh_tunnel(port=8080):
    """Uses built-in Windows OpenSSH with localhost.run for reliable HTTP 200 responses"""
    ssh_exe = shutil.which("ssh")
    if not ssh_exe:
        return None, None

    print(f"[Tunnel] Запуск надёжного SSH-туннеля (localhost.run) для порта {port}...", flush=True)
    proc = subprocess.Popen(
        [
            ssh_exe,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=10",
            "-o", "ServerAliveCountMax=99999",
            "-o", "ConnectTimeout=10",
            "-R", f"80:127.0.0.1:{port}",
            "nokey@localhost.run"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    tunnel_url = None
    start_time = time.time()

    while time.time() - start_time < 25:
        line = proc.stdout.readline()
        if not line:
            continue
        line_clean = line.strip()
        match = re.search(r'(https://[a-zA-Z0-9-]+\.lhr\.life)', line_clean)
        if match:
            tunnel_url = match.group(1)
            break

    if tunnel_url:
        with open(URL_FILE, "w", encoding="utf-8") as f:
            f.write(tunnel_url)

        print("\n" + "=" * 60, flush=True)
        print(f"[HTTPS URL] ВАШЕ МИНИ-ПРИЛОЖЕНИЕ ДОСТУПНО: {tunnel_url}", flush=True)
        print("=" * 60 + "\n", flush=True)
        return tunnel_url, proc

    return None, None


def start_single_tunnel(port=8080):
    # 1. Primary: Cloudflare Tunnel (rock solid, permanent, global edge, no random disconnects)
    if os.path.exists(CLOUDFLARED_EXE):
        try:
            print(f"[Tunnel] Запуск надёжного Cloudflare туннеля для порта {port}...", flush=True)
            proc = subprocess.Popen(
                [CLOUDFLARED_EXE, "tunnel", "--url", f"http://127.0.0.1:{port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )

            tunnel_url = None
            start_time = time.time()
            while time.time() - start_time < 25:
                line = proc.stdout.readline()
                if not line:
                    continue
                m = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
                if m:
                    tunnel_url = m.group(1)
                    break

            if tunnel_url:
                with open(URL_FILE, "w", encoding="utf-8") as f:
                    f.write(tunnel_url)
                print("\n" + "=" * 60, flush=True)
                print(f"[HTTPS URL] ВАШЕ МИНИ-ПРИЛОЖЕНИЕ ДОСТУПНО: {tunnel_url}", flush=True)
                print("=" * 60 + "\n", flush=True)
                return tunnel_url, proc
        except Exception as e:
            print(f"[Tunnel] Ошибка Cloudflare: {e}", flush=True)

    # 2. Fallback: SSH localhost.run
    url, proc = run_ssh_tunnel(port)
    if url and proc:
        return url, proc

    return None, None
