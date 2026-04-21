import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import partial

def grab_banner(sock):
    try:
        sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
        banner = sock.recv(1024)
        return banner.decode(errors="ignore").strip().splitlines()[0]
    except:
        return ""

def scan_port(target, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        if sock.connect_ex((target, port)) == 0:
            banner = grab_banner(sock)
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

    # ThreadPoolExecutor replaces manual thread batching.
    # Worker threads pick up the next port as soon as they finish one —
    # no more waiting for an entire batch to complete before continuing.
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        all_results = executor.map(scan, port_range)
        for result in all_results:
            if result is not None:
                results.append(result)

    return sorted(results)