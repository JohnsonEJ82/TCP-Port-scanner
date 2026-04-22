# TCP Port Scanner

A Python port scanner I built to get back into hands-on network programming after three years in enterprise security. No external libraries, just Python's standard socket and threading modules.

## Background

My bachelor's was in Computer Science with a networking and security specialization, and I spent three years after that as a Security Consultant at Cognizant, mostly SAP security, GRC, and access management. That work gave me a solid grasp of how enterprise security works at the process level, but the hands-on technical side during incidents was usually handled by specialist teams. I wanted to close that gap, which is part of why I came back for a master's.

This was one of the first things I built after starting the program. I picked a port scanner because it works directly at the socket layer, which is where most network reconnaissance happens. I understood the concepts from my degree but hadn't implemented anything at this level since university.

## What it does

The scanner opens TCP connections to each port in a given range, classifies each as open, closed, or filtered, and tries to read the service banner. Results include the port number, guessed service name, connection state, and banner text.

One thing I had to work out is that protocols behave differently when you first connect. SSH and FTP send a greeting immediately, so you just listen. HTTP requires you to send a request before it responds. The first version always sent an HTTP probe, which meant SSH and FTP ports always came back with empty banners. Once I understood why, splitting the port groups by protocol behavior was straightforward.

## Usage

```bash
python main.py -t 127.0.0.1 -p 80-500
python main.py -t 127.0.0.1 -p 20-1024 -o results.json --format json
python main.py -t 192.168.1.1 -p 1-1024 --threads 50
```

Flags:

    -t            Target IP or hostname (required)
    -p            Port range (default: 20-1024)
    --threads     Concurrent threads (default: 100)
    -o            Output file path
    --format      csv or json (default: csv)

No dependencies. Python 3.7 or higher is all you need.

## Project structure

    main.py      CLI argument parsing and entry point
    scanner.py   TCP connections, port state detection, banner grabbing
    utils.py     Result formatting, CSV and JSON output

Each file has one responsibility. Changing output format means touching only utils.py; changing scanning behavior means touching only scanner.py.

## What I learned

The threading part was the most interesting problem. The first version batched threads and waited for the whole batch to finish before starting new ones, so if one port in the batch was slow, every finished thread just sat idle. Switching to ThreadPoolExecutor means threads pick up the next port as soon as they finish, with no batching delay. Coming from Java, the pattern felt familiar: it's basically a fixed thread pool with a work queue.

I also stopped using bare except clauses. The original code had `except: pass` throughout, which made a DNS failure, a timeout, and an OS error all look identical. Distinguishing between them makes results more accurate and errors actually visible.

## Known limitations

TCP only. UDP services like DNS and SNMP won't show up.

No SYN scanning. That needs raw sockets and root privileges and is out of scope here.

Encrypted ports like HTTPS won't return useful banner content without TLS negotiation.

Single host only, no CIDR support yet.

There's a known bug in port range parsing: entering a reversed range like `500-80` prints an error but lets the scan continue, returning nothing. It should exit cleanly instead.

## What's next

An asyncio version would be worth comparing against the threading approach for I/O-bound workloads. CIDR input would make it more practically useful. Running it against the same target as Nmap and comparing results would also be a good exercise; understanding where they diverge and why matters more than just matching the output.

## Legal

Only scan systems you own or have explicit written permission to test. Unauthorized port scanning is illegal in Germany under §202a StGB and in many other jurisdictions.
