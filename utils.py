import json
import csv


def print_results(results):
    """Print open port results to the terminal in a formatted table."""
    if not results:
        print("No open ports found.")
        return

    print(f"\n{'PORT':<8} {'SERVICE':<14} {'STATE':<10} BANNER")
    print("-" * 70)

    for r in results:
        banner_display = r["banner"] if r["banner"] else "N/A"
        # Truncate long banners so the table stays readable in the terminal
        if len(banner_display) > 40:
            banner_display = banner_display[:37] + "..."
        print(f"{r['port']:<8} {r['service']:<14} {r['state']:<10} {banner_display}")

    print(f"\n{len(results)} open port(s) found.")


def save_results(results, filename, fmt="csv"):
    """
    Save results to a file.

    fmt="csv"  → one row per port, comma-separated
    fmt="json" → structured JSON array, easy to parse programmatically
    """
    if fmt == "json":
        _save_json(results, filename)
    else:
        _save_csv(results, filename)


def _save_csv(results, filename):
    """Write results as CSV. Simple, opens in Excel/LibreOffice."""
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["port", "service", "state", "banner"])
        writer.writeheader()
        writer.writerows(results)
    print(f"Results saved to {filename} (CSV)")


def _save_json(results, filename):
    """
    Write results as JSON. More useful for:
    - Further processing with scripts
    - Feeding into other tools
    - Structured diffing between scans
    """
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {filename} (JSON)")
