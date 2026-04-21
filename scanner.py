import socket
import threading

def grab_banner(sock):
    try:
        sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
        banner = sock.recv(1024)
        return banner.decode(errors="ignore").strip().splitlines()[0]
    except:
        return ""

def scan_port(target, port, results, lock):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        if sock.connect_ex((target, port)) == 0:
            banner = grab_banner(sock)
            with lock:
                results.append((port, banner))
        sock.close()
    except:
        pass

def scan_ports(target, start_port, end_port, max_threads=100):
    results = []
    lock = threading.Lock()
    threads = []

    for port in range(start_port, end_port + 1):
        t = threading.Thread(target=scan_port, args=(target, port, results, lock))
        threads.append(t)
        t.start()
        if len(threads) >= max_threads:
            for t in threads:
                t.join()
            threads = []

    for t in threads:
        t.join()

    return sorted(results)
