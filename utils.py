def print_results(results):
    if not results:
        print("No open ports found.")
        return
    print(f"{'PORT':<8}{'STATUS':<10}BANNER")
    print("-" * 60)
    for port, banner in results:
        print(f"{port:<8}{'OPEN':<10}{banner or 'N/A'}")
    print(f"\n{len(results)} open port(s) found.")

def save_results(results, filename):
    with open(filename, "w") as f:
        f.write("PORT,STATUS,BANNER\n")
        for port, banner in results:
            f.write(f"{port},OPEN,{banner or 'N/A'}\n")
    print(f"Results saved to {filename}")
