import json
import csv


def print_results(results):
    if not results:
        print("No open ports found.")
        return

    # format string alignment — took a bit to figure out the < syntax (left-align)
    print(f"\n{'PORT':<8} {'SERVICE':<14} {'STATE':<10} BANNER")
    print("-" * 70)

    for r in results:
        banner_display = r["banner"] if r["banner"] else "N/A"
        # truncate long banners so the table doesn't break
        if len(banner_display) > 40:
            banner_display = banner_display[:37] + "..."
        print(f"{r['port']:<8} {r['service']:<14} {r['state']:<10} {banner_display}")

    print(f"\n{len(results)} open port(s) found.")


def save_results(results, filename, fmt="csv"):
    if fmt == "json":
        _save_json(results, filename)
    else:
        _save_csv(results, filename)


def _save_csv(results, filename):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["port", "service", "state", "banner"])
        writer.writeheader()
        writer.writerows(results)
    print(f"Results saved to {filename} (CSV)")


def _save_json(results, filename):
    # JSON is easier to parse programmatically than CSV, added this as an option
    # tested this by scanning 127.0.0.1 and checking the output manually
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {filename} (JSON)")
