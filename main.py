import argparse
from scanner import scan_ports
from utils import print_results, save_results

def main():
    parser = argparse.ArgumentParser(description="Python Port Scanner")
    parser.add_argument("-t", "--target", required=True, help="Target IP or domain")
    parser.add_argument("-p", "--ports", default="20-1024", help="Port range e.g. 20-1024")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument("--threads", type=int, default=100, help="Max concurrent threads")

    args = parser.parse_args()

    start_port, end_port = map(int, args.ports.split("-"))

    print(f"\nScanning {args.target} ports {start_port}-{end_port}...\n")
    open_ports = scan_ports(args.target, start_port, end_port, args.threads)

    print_results(open_ports)

    if args.output:
        save_results(open_ports, args.output)

if __name__ == "__main__":
    main()
