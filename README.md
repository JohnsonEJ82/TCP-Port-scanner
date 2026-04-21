# TCP Port Scanner

A Python port scanner I built to understand how tools like Nmap work under the hood.
No external libraries — just Python's standard socket and threading modules.

---

## Background

I started this to get hands-on with socket programming and network protocols.
The first version used manual thread batching which turned out to be inefficient —
threads were waiting on each other unnecessarily. Fixing that led me to dig into
Python's `concurrent.futures` module, which was the most interesting part of the project.

---

## What it does

Connects to each port in a given range using TCP, checks if it's open, and tries
to read whatever greeting message the service sends back (the "banner"). Different
protocols behave differently here — SSH sends a banner the moment you connect, while
HTTP requires you to send a request first. The scanner handles each case separately.

Results show port number, guessed service name, state, and banner text.

---

## Usage

```bash
# Scan default range (ports 20–1024)
python main.py -t 127.0.0.1

# Custom range
python main.py -t 192.168.1.1 -p 1-500

# Save output as JSON
python main.py -t 127.0.0.1 -p 20-1024 -o results.json --format json

# Reduce threads (useful on slower networks)
python main.py -t 192.168.1.1 -p 1-1024 --threads 50
```

| Flag | What it does | Default |
|------|-------------|---------|
| `-t` | Target IP or hostname | required |
| `-p` | Port range | `20-1024` |
| `--threads` | Concurrent threads | `100` |
| `-o` | Save results to file | — |
| `--format` | `csv` or `json` | `csv` |

No dependencies to install — Python 3.7+ only.

---

## Project structure

```
main.py      →  CLI, argument parsing, entry point
scanner.py   →  socket logic, banner grabbing, thread pool
utils.py     →  terminal output, CSV and JSON writing
```

Each file has one job. If the output format changes, only `utils.py` needs to change.
If the scanning logic changes, only `scanner.py` needs to change.

---

## A few things I learned building this

**Threading model matters more than thread count**
The first version batched threads — start 100, wait for all 100 to finish, then
start the next 100. One slow port held up the whole batch. `ThreadPoolExecutor`
fixes this by keeping threads continuously fed with work.

**Protocols don't all talk the same way**
The original banner grabber always sent an HTTP probe, which meant it got nothing
back from SSH or FTP ports. Those protocols speak first — you just have to listen.
This was a simple fix once I understood why it was failing.

**Silent errors are worse than noisy ones**
The original code had `except: pass` everywhere. It made the scanner look clean
but hid real failures. A timeout on a filtered port is different from a DNS error —
they need different handling.

---

## Known limitations

- **TCP only** — UDP services like DNS and DHCP won't show up
- **No SYN scan** — would need raw sockets and root privileges
- **Encrypted ports** — HTTPS and IMAPS won't give useful banners without TLS
- **Single host only** — no CIDR range support yet

---

## What I'd add next

- `asyncio` version to compare performance with the threading approach
- CIDR input so you can scan a subnet like `192.168.1.0/24`
- Benchmark against Nmap on the same target to see where results differ

---

## Legal

Only scan systems you own or have explicit permission to test.
Unauthorized port scanning is illegal in Germany under §202a StGB.
