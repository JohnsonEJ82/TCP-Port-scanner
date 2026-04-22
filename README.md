# TCP Port Scanner

A Python port scanner I built to get back into hands-on network programming
after three years working in enterprise security operations. No external
libraries — just Python's standard socket and threading modules.

---

## Background

My bachelor's was in Computer Science with a specialization in Networking and
Security, and I spent three years after that working as a Security Consultant
at Cognizant — mostly SAP security, GRC, and access management. That work gave
me a solid understanding of how enterprise security works at the process level,
but most of the actual technical investigation during incidents was handled by
specialist teams. I wanted to get closer to the technical side, which is part
of why I came back to do a master's.

This project is one of the first things I built after starting the program. I
chose a port scanner specifically because it touches the socket layer directly —
the same layer where most network reconnaissance and early-stage attacks happen.
Coming from a networking specialization, I understood the concepts but hadn't
implemented anything at this level since university.

---

## What it does

The scanner connects to each port in a given range using TCP, classifies the
port as open, closed, or filtered, and tries to read whatever greeting message
the service sends back. Results include the port number, guessed service name,
connection state, and banner text.

One thing I had to figure out is that different protocols behave differently
when you connect. SSH and FTP send a greeting immediately — you just listen.
HTTP requires you to send a request first before it responds. The first version
of the scanner always sent an HTTP probe, which meant SSH and FTP ports always
returned empty banners. Once I understood why, splitting the port groups by
protocol behavior was straightforward.

---

## Usage

```bash
python main.py -t 127.0.0.1 -p 80-500

python main.py -t 127.0.0.1 -p 20-1024 -o results.json --format json

python main.py -t 192.168.1.1 -p 1-1024 --threads 50
```

Flags available:

    -t            Target IP or hostname (required)
    -p            Port range, default is 20-1024
    --threads     Number of concurrent threads, default is 100
    -o            Output file path
    --format      csv or json, default is csv

No dependencies to install. Python 3.7 or higher is all you need.

---

## Project structure

    main.py      reads command-line arguments, validates input, runs the scan
    scanner.py   handles TCP connections, port state detection, banner grabbing
    utils.py     formats and prints results, writes CSV and JSON output

Each file has one responsibility. Changing the output format means touching
only utils.py. Changing scanning behavior means touching only scanner.py.

---

## What I learned building this

The threading problem was the most interesting part. The first version batched
threads and waited for the entire batch to finish before starting new ones. If
one port in the batch was slow, every other finished thread sat idle waiting
for it. Switching to ThreadPoolExecutor means threads pick up the next port
immediately as they finish, with no batching delay. I came from Java so the
pattern was familiar — it's essentially the same as a fixed thread pool with
a work queue.

I also learned to stop using bare except clauses. The original code had
except: pass everywhere, which meant a DNS failure, a timeout, and an OS error
all looked identical. Distinguishing between them makes results more accurate
and errors actually visible.

---

## Known limitations

TCP only. UDP services like DNS and SNMP won't appear in results.

No SYN scanning. That requires raw sockets and root privileges and is out of
scope for this project.

Encrypted ports like HTTPS won't return useful banner content without TLS
negotiation.

Single host only — no CIDR range support yet.

There is a known bug in port range parsing: if you enter a reversed range like
500-80, an error message prints but the scan continues anyway and returns
nothing. It should exit cleanly instead.

---

## What I'd add next

An asyncio version would be worth comparing against the threading approach for
I/O-bound workloads. CIDR input support would make it more practically useful.
Running it against the same target as Nmap and comparing results would be a
good exercise — understanding where they diverge and why matters more than
just matching output.

---

## Legal

Only scan systems you own or have explicit permission to test. Unauthorized
port scanning is illegal in Germany under §202a StGB and in many other
jurisdictions.
