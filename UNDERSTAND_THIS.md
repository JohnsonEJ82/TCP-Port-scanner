# Understanding the Port Scanner — Read This Before Any Professor Conversation

This document is for you, not for GitHub visitors. It explains what the project
does, how every part works, and how to talk about it confidently. It also
connects the project to your actual background so the conversation feels natural
rather than rehearsed.

---

## What the project actually does

A port scanner checks which services are running on a networked computer by
attempting to connect to each port in a given range. Every computer has 65,535
TCP ports — think of them like numbered doors. Services sit behind specific doors
and wait for incoming connections:

    Port 22   is where SSH listens
    Port 80   is where HTTP listens
    Port 443  is where HTTPS listens

This scanner knocks on each door in a range, notes which ones open, tries to
read any greeting message the service sends, and reports everything in a table.
The complexity is in how it does this efficiently, correctly, and without
silently hiding errors.

---

## How this connects to your SAP background

This is worth having ready because a professor will likely ask about your work
experience. The connection is genuine, not forced.

In SAP GRC you managed access control — who is allowed to do what in which
system. That is exactly what port scanning informs on the network level: which
services are exposed and reachable. A port that should be closed but is open
is the network equivalent of a user having a role they shouldn't have.

Transport management across DEV, QAS, and PROD environments taught you why
environment separation matters — the same principle applies to network
segmentation, where services in production should not be reachable from
development networks.

Incident handling taught you that diagnosing a problem requires distinguishing
between different failure modes. A user who can't log in because their account
is locked is a different problem from one who can't log in because their role
is missing. The scanner applies the same thinking — a timeout is a different
problem from a refused connection, which is different again from a DNS failure.

You don't need to force these connections into conversation, but if a professor
asks how your work experience relates to what you're studying, this is the
honest answer.

---

## The three files and what each one does

main.py is the entry point. It reads what the user typed on the command line,
validates it, and coordinates the other two files. One job: handle input and
wire things together.

scanner.py is the core logic. It opens TCP connections, decides whether each
port is open, closed, or filtered, and reads banners from open ports. All
network operations happen here.

utils.py handles output only. It prints the results table to the terminal and
writes CSV or JSON files. It knows nothing about networking.

This pattern is called separation of concerns. Each file has a single
responsibility. If output formatting needs to change, only utils.py changes.
If scanning logic changes, only scanner.py changes. Coming from Java, this
is essentially the same principle as single-responsibility classes.

---

## What a socket is

A socket is a software object representing one end of a network connection.
When a browser loads a webpage, it creates a socket to talk to the server.
This scanner creates sockets the same way, programmatically.

```python
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```

AF_INET means IPv4, the standard internet address format.
SOCK_STREAM means TCP, a reliable connection-based protocol.
The alternative is UDP (SOCK_DGRAM), which is faster but doesn't guarantee
delivery and isn't covered by this scanner.

---

## How TCP connect scanning works

When you call:

```python
return_code = sock.connect_ex((target, port))
```

Python attempts a full TCP connection. TCP connections use the three-way
handshake you know from your networking background:

    1. Your machine sends SYN
    2. If something is listening, it replies SYN-ACK
    3. Your machine sends ACK to complete the connection

connect_ex handles all three steps automatically. If it returns 0, the
handshake completed and the port is open. Any other return code means it
failed — the port is closed or blocked.

This is called a TCP connect scan. It completes the full handshake which makes
it reliable but also detectable. Tools like Nmap can do a SYN scan, which
sends the SYN but never completes the handshake, making it stealthier. That
requires raw socket access and root privileges, so this project uses the
simpler connect approach.

---

## Port states and what they mean

open means a service is actively listening and completed the handshake.

closed means nothing is listening, but the host responded with a rejection
packet (RST). The machine is reachable but that port is not in use.

filtered means there was no response at all within the timeout window. This
is usually a firewall silently dropping packets. The scanner infers this from
a socket.timeout exception.

error means something went wrong on the scanner's side — typically a DNS
failure (hostname couldn't be resolved) or an OS-level socket problem.

---

## Why threading is necessary

Without threading, the scanner handles one port at a time. Each connection
waits up to 1 second for a response. Scanning ports 80 to 500 would take
around 420 seconds — about 7 minutes. Threading lets hundreds of ports be
tested simultaneously.

The first version used manual thread batching:

```python
if len(threads) >= max_threads:
    for t in threads:
        t.join()
    threads = []
```

join() waits for every thread in the batch to finish before starting new ones.
If one port takes 900ms and all others finish in 50ms, every fast thread sits
idle waiting for that one slow port.

The current version uses ThreadPoolExecutor:

```python
with ThreadPoolExecutor(max_workers=max_threads) as executor:
    all_results = executor.map(lambda port: scan_port(target, port), port_range)
```

A fixed pool of worker threads is created once. As soon as any thread finishes,
it picks up the next port from the queue immediately. No batching delay.

The lambda is wrapping scan_port so that executor.map can call it with just
the port number — target stays the same for every call. In Java terms this is
similar to a method reference passed to a thread pool with a pre-bound argument.

---

## Banner grabbing and why protocols are handled separately

When a port is open, many services send a greeting message on connect — called
a banner. Examples:

    SSH:   SSH-2.0-OpenSSH_8.4p1 Ubuntu-6ubuntu2.1
    FTP:   220 ProFTPD 1.3.5 Server ready
    HTTP:  HTTP/1.1 200 OK

Banners are useful because they reveal the software and sometimes the version
running on that port. In security research this matters because specific
versions may have known vulnerabilities — the kind of thing your GRC access
risk reports flagged at the compliance level, but at the service level instead.

The key problem is that protocols behave differently on connect. SSH, FTP, and
SMTP send their banner immediately without waiting for you to speak first. HTTP
requires you to send a request before it responds. The first version of this
scanner always sent an HTTP probe, so SSH and FTP ports always returned empty
banners — the service had already spoken and was waiting for a response that
never came.

The current version handles this with two port groups:

    PASSIVE_BANNER_PORTS contains ports where you just listen
    HTTP_PORTS contains ports where you send a HEAD request first

For ports outside both groups, the scanner listens first and falls back to an
HTTP probe if nothing comes back. There is a TODO in the code noting that other
protocol patterns aren't covered — SMTP extensions, database handshakes, and
others all have their own conventions.

---

## Error handling and why bare except is a problem

The original code had this everywhere:

```python
except:
    pass
```

This makes a timeout look identical to a DNS failure which looks identical to
running out of file descriptors. Results can be wrong and you have no way of
knowing why.

The current version separates them:

```python
except socket.timeout:
    result["state"] = "filtered"

except socket.gaierror as e:
    logging.error(f"Could not resolve hostname '{target}': {e}")
    result["state"] = "error"

except OSError as e:
    logging.warning(f"Port {port}: {e}")
    result["state"] = "error"
```

socket.timeout specifically means the connection attempt timed out with no
response — the signature of a firewall dropping packets.

socket.gaierror is a DNS resolution failure. gaierror stands for getaddrinfo
error, which is the underlying system call that resolves hostnames.

OSError is a broader catch for operating system level socket problems such as
running out of available file descriptors.

logging is used instead of print() so errors go to stderr at the appropriate
severity level rather than mixing with normal output. The logging module works
similarly to Java's Logger — basicConfig sets the global format and level.

---

## The known bug and how to talk about it

In main.py, when the start port is greater than the end port, the code prints
an error but does not stop:

```python
if start > end:
    print("Error: start port must be less than or equal to end port")
return start, end  # still runs
```

The scan continues with a backwards range and returns no results. The correct
fix is sys.exit(1) or raising an exception, the same way the port range
validation above it is handled. There is a TODO comment noting this.

If a professor asks about it: "I noticed this when testing invalid inputs —
it prints the message but doesn't actually stop. I should have raised an
exception there the same way the other validation errors are handled above it."
That answer demonstrates you can read your own code critically.

---

## JSON and CSV output

CSV is one row per open port, comma-separated. Opens directly in Excel or
LibreOffice.

JSON is a structured array where each result is an object with named fields:

```json
[
  {
    "port": 80,
    "state": "open",
    "service": "HTTP",
    "banner": "HTTP/1.1 200 OK"
  }
]
```

JSON is more useful for feeding results into other scripts, comparing two
scans programmatically, or extending the data model without breaking the
format. The dict-based result structure in scanner.py makes this natural
because each result already has named fields.

---

## Questions you should be ready to answer

What is a TCP connect scan and how does it differ from a SYN scan?
TCP connect completes the full three-way handshake. SYN scan only sends the
first packet and never completes it — faster and stealthier but requires raw
sockets and root privileges. This scanner uses TCP connect because it works
without elevated permissions.

Why ThreadPoolExecutor instead of manual threading?
The manual version batched threads and waited for the entire batch before
starting new ones. One slow port blocked the whole batch. ThreadPoolExecutor
keeps workers running continuously — as soon as one finishes a port it picks
up the next one.

Why does SSH get handled differently from HTTP in banner grabbing?
SSH sends its banner the moment you connect. HTTP requires you to send a
request first. Sending an HTTP probe to an SSH port produces nothing because
SSH already spoke and is waiting for your response.

Why is the timeout 1 second?
Without a timeout the scanner blocks indefinitely on filtered ports where
the firewall drops packets silently. One second was enough for testing on
localhost. On a real network with latency it might need to be higher.

How does this connect to your work experience?
Port scanning is reconnaissance — finding out what is exposed and reachable.
That is the technical layer underneath what I was doing operationally in GRC:
figuring out who or what has access to what, and whether that access is
appropriate. The diagnostic thinking is the same, the layer is different.

What would you add next?
An asyncio version to compare performance with threading. CIDR range input
to scan subnets. A structured comparison against Nmap output on the same
target to understand where they differ and why.

---

## Your pitch — keep it under 45 seconds

"I have a bachelor's in Networking and Security and spent three years in
enterprise security at Cognizant before starting the master's. Most of that
work was at the process level — GRC, access management, incident handling —
and I wanted to get back to the technical foundations underneath it. This
scanner was the first thing I built in the program. It touches the socket
layer directly, which is where most early-stage network attacks happen. The
interesting problem was threading — the first version batched threads and one
slow port could hold up an entire batch. Switching to a thread pool fixed that.
I also had to split the banner grabbing by protocol because SSH and HTTP behave
completely differently on connect."
