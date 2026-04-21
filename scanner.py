import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

# These protocols send a greeting banner immediately when you connect.
# You don't need to send anything first — just listen.
PASSIVE_BANNER_PORTS = {
    21,   # FTP   → "220 Welcome to FTP server"
    22,   # SSH   → "SSH-2.0-OpenSSH_8.4"
    25,   # SMTP  → "220 mail.example.com ESMTP"
    110,  # POP3  → "+OK Dovecot ready"
    143,  # IMAP  → "* OK Dovecot IMAP ready"
    587,  # SMTP submission
    993,  # IMAPS
    995,  # POP3S
    3306, # MySQL
    5432, # PostgreSQL
}

# HTTP ports — need to send a request to get a response
HTTP_PORTS = {80, 8080, 8000, 8443}

def grab_banner(sock, port):
    try:
        sock.settimeout(2)

        if port in PASSIVE_BANNER_PORTS:
            # Server speaks first — just listen
            raw = sock.recv(1024).decode(errors="ignore").strip()
            return raw.splitlines()[0] if raw else ""

        if port in HTTP_PORTS:
            # HTTP: we must send a request first
            sock.send(b"HEAD / HTTP/1.0\r\nHost: localhost\r\n\r\n")
            raw = sock.recv(1024).decode(errors="ignore").strip()
            return raw.splitlines()[0] if raw else ""

        # Unknown port: try passive first, fall back to HTTP probe
        try:
            raw = sock.recv(512).decode(errors="ignore").strip()
            if raw:
                return raw.splitlines()[0]
        except socket.timeout:
            pass

        sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
        raw = sock.recv(512).decode(errors="ignore").strip()
        return raw.splitlines()[0] if raw else ""

    except Exception:
        return ""

def scan_port(target, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        if sock.connect_ex((target, port)) == 0:
            banner = grab_banner(sock, port)
            sock.close()
            return (port, banner)
        sock.close()
    except:
        pass
    return None

def scan_ports(target, start_port, end_port, max_threads=100):
    port_range = range(start_port, end_port + 1)
    results = []

    scan = partial(scan_port, target)

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        all_results = executor.map(scan, port_range)
        for result in all_results:
            if result is not None:
                results.append(result)

    return sorted(results)
