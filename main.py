import argparse
import sys
from scanner import scan_ports
from utils import print_results, save_results

ETHICAL_WARNING = """
 --------------------------------------------------------------
|                    ⚠  LEGAL NOTICE  ⚠                        |
|                                                              |
|  Port scanning without explicit authorization is illegal     |
|  in many jurisdictions, including Germany (§202a StGB).      |
|                                                              |
|  Only scan systems you own or have written permission to     |
|  test. The author takes no responsibility for misuse.        |
 --------------------------------------------------------------
"""


def parse_ports(port_str):
    """
    Parse port argument. Supports:
      - Range:  "20-1024"
      - Single: "80"
      - List:   "22,80,443"  (future extension point)
    """
    if "-" in port_str:
        parts = port_str.split("-")
        if len(parts) != 2:
            raise argparse.ArgumentTypeError(f"Invalid port range: '{port_str}'. Use format: 20-1024")
        start, end = int(parts[0]), int(parts[1])
        if not (1 <= start <= 65535 and 1 <= end <= 65535):
            raise argparse.ArgumentTypeError("Ports must be between 1 and 65535")
        if start > end:
            print("Error: Start port must be <= end port")
        return start, end
    else:
        port = int(port_str)
        return port, port


def main():
    print(ETHICAL_WARNING)

    parser = argparse.ArgumentParser(
        description="TCP Port Scanner — educational use only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py -t 127.0.0.1 -p 20-1024
  python main.py -t example.com -p 80-443 -o results.json --format json
  python main.py -t 192.168.1.1 -p 22 --threads 50
        """
    )

    parser.add_argument("-t", "--target", required=True,
                        help="Target IP address or hostname (e.g. 127.0.0.1 or example.com)")
    parser.add_argument("-p", "--ports", default="20-1024",
                        help="Port range to scan (default: 20-1024)")
    parser.add_argument("-o", "--output",
                        help="Output file path (e.g. results.csv or results.json)")
    parser.add_argument("--threads", type=int, default=100,
                        help="Number of concurrent threads (default: 100)")
    parser.add_argument("--format", choices=["csv", "json"], default="csv",
                        help="Output file format: csv or json (default: csv)")

    args = parser.parse_args()

    # Parse and validate port range
    try:
        start_port, end_port = parse_ports(args.ports)
    except (ValueError, argparse.ArgumentTypeError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    total_ports = end_port - start_port + 1
    print(f"Target  : {args.target}")
    print(f"Ports   : {start_port}–{end_port} ({total_ports} total)")
    print(f"Threads : {args.threads}")
    print(f"Format  : {args.format.upper()}\n")
    print("Scanning...\n")

    open_ports = scan_ports(args.target, start_port, end_port, args.threads)

    print_results(open_ports)

    if args.output:
        save_results(open_ports, args.output, fmt=args.format)


if __name__ == "__main__":
    main()
