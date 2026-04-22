import socket
import logging
from concurrent.futures import ThreadPoolExecutor

# switched from using print() for errors to logging after i kept missing
# failures during test scans — still getting used to how logging works in Python
# (in Java i'd use a Logger class, this feels a bit different)
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

# ports where the service sends a message immediately when you connect
# found this out when SSH kept returning empty banners — turns out SSH speaks
# first, you don't need to send anything. had to split these out from HTTP ports.
PASSIVE_BANNER_PORTS = {
    21,   # FTP
    22,   # SSH
    25,   # SMTP
    110,  # POP3
    143,  # IMAP
}

# HTTP needs you to send a request before it responds
HTTP_PORTS = {80, 8080, 8000}

# common port-to-service mapping — just for display
COMMON_SERVICES = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 8080: "HTTP-Alt"
}


def grab_banner(sock, port):
    try:
        sock.settimeout(2)  # not sure if 2 seconds is always enough, worked fine on localhost

        if port in PASSIVE_BANNER_PORTS:
            # server sends banner on its own, just read it
            raw = sock.recv(1024).decode(errors="ignore").strip()
            return raw.splitlines()[0] if raw else ""

        if port in HTTP_PORTS:
            # HTTP requires sending a request first
            sock.send(b"HEAD / HTTP/1.0\r\nHost: localhost\r\n\r\n")
            raw = sock.recv(1024).decode(errors="ignore").strip()
            return raw.splitlines()[0] if raw else ""

        # for unknown ports: try listening first, fall back to HTTP probe
        # TODO: there are probably other protocol patterns i'm not covering here
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
        # if banner grabbing fails just return empty — don't want it crashing the scan
        return ""


def scan_port(target, port):
    # using a dict so i can add more fields later without breaking things
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
            # 0 = connection succeeded, port is open
            result["state"] = "open"
            result["banner"] = grab_banner(sock, port)
        else:
            result["state"] = "closed"

        sock.close()

    except socket.timeout:
        # no response usually means a firewall is silently dropping packets
        result["state"] = "filtered"

    except socket.gaierror as e:
        # hostname couldn't be resolved
        logging.error(f"Could not resolve hostname '{target}': {e}")
        result["state"] = "error"

    except OSError as e:
        logging.warning(f"Port {port}: {e}")
        result["state"] = "error"

    return result


def scan_ports(target, start_port, end_port, max_threads=100):
    port_range = range(start_port, end_port + 1)
    open_ports = []

    # ThreadPoolExecutor replaced the manual threading version —
    # the old approach batched threads and waited for an entire batch to finish
    # before starting the next one. if one port in the batch was slow, everything
    # waited. this version keeps threads running as soon as any port finishes.
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        all_results = executor.map(lambda port: scan_port(target, port), port_range)

        for result in all_results:
            if result["state"] == "open":
                open_ports.append(result)

    return sorted(open_ports, key=lambda x: x["port"])
