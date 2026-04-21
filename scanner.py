import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

PASSIVE_BANNER_PORTS = {
    21, 22, 25, 110, 143, 587, 993, 995, 3306, 5432,
}

HTTP_PORTS = {80, 8080, 8000, 8443}

COMMON_SERVICES = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 587: "SMTP-Sub", 993: "IMAPS",
    995: "POP3S", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB"
}

def grab_banner(sock, port):
    try:
        sock.settimeout(2)
        if port in PASSIVE_BANNER_PORTS:
            raw = sock.recv(1024).decode(errors="ignore").strip()
            return raw.splitlines()[0] if raw else ""
        if port in HTTP_PORTS:
            sock.send(b"HEAD / HTTP/1.0\r\nHost: localhost\r\n\r\n")
            raw = sock.recv(1024).decode(errors="ignore").strip()
            return raw.splitlines()[0] if raw else ""
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
    # Results are now dicts instead of tuples — needed for JSON output
    # and makes the data structure explicit and extensible
    result = {
        "port": port,
        "state": "closed",
        "service": COMMON_SERVICES.get(port, "unknown"),
        "banner": ""
    }

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        return_code = sock.connect_ex((target, port))

        if return_code == 0:
            result["state"] = "open"
            result["banner"] = grab_banner(sock, port)
        else:
            result["state"] = "closed"

        sock.close()

    except socket.timeout:
        result["state"] = "filtered"
    except socket.gaierror as e:
        logging.error(f"DNS resolution failed for '{target}': {e}")
        result["state"] = "error"
    except OSError as e:
        logging.warning(f"Port {port} OS error: {e}")
        result["state"] = "error"

    return result

def scan_ports(target, start_port, end_port, max_threads=100):
    port_range = range(start_port, end_port + 1)
    open_ports = []

    scan = partial(scan_port, target)

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        all_results = executor.map(scan, port_range)
        for result in all_results:
            if result["state"] == "open":
                open_ports.append(result)

    return sorted(open_ports, key=lambda x: x["port"])
