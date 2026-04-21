# Port Scanner — What It Does and How to Talk About It

This document explains the project so you can answer any question a professor
throws at you. No assumed background knowledge.

---

## What does this project actually do?

A port scanner checks which "doors" (ports) are open on a computer connected
to a network.

Every computer has 65,535 TCP ports. Think of them like numbered apartment
mailboxes. When a service runs on a machine, it "listens" on a specific port:
- Port 22 → SSH (remote login)
- Port 80 → HTTP (web traffic)
- Port 443 → HTTPS (encrypted web traffic)

This scanner tries to connect to each port in a range and reports which ones
are open, what service is probably running there, and any identifying text
(called a "banner") the service sends back.

---

## File structure — what each file does

```
main.py     → Entry point. Reads command-line arguments, coordinates everything.
scanner.py  → Core logic. Opens sockets, detects open ports, grabs banners.
utils.py    → Output. Prints the table, writes CSV/JSON files.
```

This separation is called "separation of concerns" — each file has one job.
If you want to change how output works, you only touch utils.py. If you want
to change scanning logic, you only touch scanner.py.

---

## Key concept: What is a socket?

A socket is a software object that represents one end of a network connection.
When your browser connects to a website, it creates a socket. This scanner
does the same thing programmatically.

```python
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```

- AF_INET → IPv4 (the standard internet address format, e.g. 192.168.1.1)
- SOCK_STREAM → TCP (a reliable, connection-based protocol)

```python
return_code = sock.connect_ex((target, port))
```

`connect_ex` tries to connect. If it returns 0, the connection worked → port
is open. Any other number means it failed → port is closed or filtered.

---

## Key concept: TCP connect scan

This scanner uses TCP connect scanning. It's the simplest scan type:

1. Send a SYN packet (asking to connect)
2. If the server replies with SYN-ACK → port is open, complete the handshake
3. If the server replies with RST → port is closed
4. If there's no reply at all → port is likely filtered by a firewall

`connect_ex` does all of this automatically. You don't manually control the
TCP handshake.

### Why not SYN scan (half-open scan)?

SYN scanning sends the SYN but never completes the handshake — it's faster and
stealthier, but requires raw socket access, which needs root/admin privileges.
TCP connect scan is fine for educational purposes and works without elevated
permissions.

---

## Key concept: Port states

| State    | Meaning                                              |
|----------|------------------------------------------------------|
| open     | A service is actively listening on this port         |
| closed   | Nothing is listening, but the host responded (RST)   |
| filtered | No response — firewall is silently dropping packets  |
| error    | Scanner-side problem (DNS failure, OS error)         |

---

## Key concept: Threading — why do we need it?

If you scanned one port at a time and each connection waited 1 second for a
response, scanning ports 20–1024 would take 1004 seconds (≈17 minutes).

Threading lets the scanner wait for many connections at the same time.
Each thread handles one port, and they all run concurrently.

### Old approach (manual threading — what was in the original code):

```python
threads = []
for port in ports:
    t = threading.Thread(target=scan_port, ...)
    threads.append(t)
    t.start()
    if len(threads) >= max_threads:
        for t in threads:
            t.join()   # WAIT for ALL threads to finish before continuing
        threads = []
```

Problem: This is batching. You start 100 threads, wait for all 100 to finish
(even the fast ones), then start the next 100. A slow port in one batch holds
up the entire batch.

### New approach (ThreadPoolExecutor — what this version uses):

```python
with ThreadPoolExecutor(max_workers=100) as executor:
    all_results = executor.map(scan, port_range)
```

A pool of 100 worker threads is created once. As soon as one thread finishes a
port, it immediately picks up the next one. There's no batching delay. This is
genuine concurrency.

Analogy: Old approach = a restaurant where all tables must finish eating before
the waiter takes new orders. New approach = a waiter who takes the next order
as soon as any table is done.

---

## Key concept: Banner grabbing

When a service is open, it often sends a greeting message. This is called a
banner. Example banners:

- SSH:  `SSH-2.0-OpenSSH_8.4p1 Ubuntu-6ubuntu2.1`
- FTP:  `220 ProFTPD 1.3.5 Server ready`
- HTTP: `HTTP/1.1 200 OK` followed by server headers

These banners reveal the software and sometimes the version — useful for
identifying services and (in security research) known vulnerabilities.

### Protocol differences matter

Not all protocols behave the same way:

| Protocol | Who speaks first?  | What to do                      |
|----------|--------------------|----------------------------------|
| SSH      | Server speaks first | Just listen (recv immediately)  |
| FTP      | Server speaks first | Just listen                     |
| SMTP     | Server speaks first | Just listen                     |
| HTTP     | Client speaks first | Send "HEAD / HTTP/1.0\r\n\r\n"  |
| Unknown  | Unclear             | Try passive first, then HTTP    |

The original code always sent an HTTP probe — so it got no banner from SSH
or FTP. The updated version handles each protocol correctly.

---

## Key concept: Error handling

Original code had:
```python
except:
    pass
```

This silently ignores every possible error — including ones you'd want to
know about, like the target hostname not existing, or running out of file
descriptors.

Updated code distinguishes:
```python
except socket.timeout:        → port is filtered (firewall dropping packets)
except socket.gaierror:       → DNS failed (hostname doesn't resolve)
except OSError:               → OS-level error (log it, don't crash)
```

This is important for both software quality and for diagnosing incorrect
results. Hiding errors hides bugs.

---

## Key concept: JSON vs CSV output

CSV is a flat text format — one row per result. Simple, opens in Excel.

JSON is structured — each result is an object with named fields. Better for:
- Feeding into other scripts
- Comparing two scans programmatically
- Extending the data model (add fields without breaking format)

Example JSON output:
```json
[
  {
    "port": 22,
    "state": "open",
    "service": "SSH",
    "banner": "SSH-2.0-OpenSSH_8.4"
  },
  {
    "port": 80,
    "state": "open",
    "service": "HTTP",
    "banner": "HTTP/1.1 200 OK"
  }
]
```

---

## Design decisions you should be able to explain

**Why TCP connect scan and not SYN scan?**
> SYN scan requires raw sockets, which require root privileges and are more
> complex to implement. TCP connect is sufficient to demonstrate the concept
> and works in any user environment.

**Why ThreadPoolExecutor and not manual threading?**
> ThreadPoolExecutor is the standard library's recommended approach for thread
> pools. It avoids the batching inefficiency of manual thread management, handles
> exceptions cleanly, and is significantly fewer lines of code.

**Why is there a timeout set on the socket?**
> Without a timeout, the scanner would block indefinitely on filtered ports
> (where the firewall drops packets with no response). A 1-second timeout means
> filtered ports are classified correctly within a predictable time.

**Why the ethical/legal warning?**
> Port scanning without permission is illegal in Germany under §202a StGB
> (unauthorized access to computer systems). Including the warning shows
> awareness of the legal context — especially relevant in a German university
> setting.

**Why separate PASSIVE_BANNER_PORTS from HTTP_PORTS?**
> Different protocols have different communication conventions. Sending an HTTP
> probe to an SSH port just wastes time and produces garbage. Grouping ports by
> behavior makes the banner grabbing logic explicit and correct.

---

## Limitations you should acknowledge

These are not weaknesses to hide — professors respect students who know their
system's limits:

1. **TCP only** — UDP scanning is not implemented. Many services (DNS, DHCP,
   SNMP) use UDP and would not be detected.

2. **No SYN scan** — requires raw sockets / root. Not included by design.

3. **connect_ex doesn't distinguish filtered vs timeout reliably** — we infer
   "filtered" from a socket.timeout exception, but some closed ports also time
   out if the host silently drops RST packets.

4. **Banner grabbing is best-effort** — encrypted ports (HTTPS, IMAPS) won't
   reveal useful banner content without TLS negotiation.

5. **No CIDR range support** — can only scan one host at a time.

---

## What you could extend this with (mention this proactively)

- **Async scanning with asyncio** — potentially faster than threading for
  I/O-bound workloads; would be an interesting performance comparison.
- **CIDR input support** (e.g. 192.168.1.0/24) — scan entire subnets.
- **Nmap comparison** — run both on the same target, compare results and
  timing; good mini research angle.
- **UDP scanning** — requires raw sockets but reveals a different set of
  services.

---

## How to introduce this in a 30-second pitch

> "I built a multithreaded TCP port scanner in Python to understand how network
> reconnaissance tools work at the socket level. I ran into the batching
> inefficiency of manual thread management, so I refactored to ThreadPoolExecutor.
> I also extended the banner grabbing to handle different protocol behaviors —
> SSH and FTP send banners immediately on connect, while HTTP requires sending
> a request first. The scanner outputs to both CSV and JSON."

That's it. Concrete, self-aware, covers a real engineering decision.

---

## Quick reference: how to run it

```bash
# Basic scan
python main.py -t 127.0.0.1 -p 20-1024

# Save as JSON
python main.py -t 127.0.0.1 -p 20-1024 -o results.json --format json

# Fewer threads (slower but less aggressive)
python main.py -t 192.168.1.1 -p 1-1024 --threads 50

# Single port
python main.py -t example.com -p 80-80
```

No dependencies to install — stdlib only.
