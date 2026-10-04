import sys
from pipeline import analyze_report


def main():
    file_path = sys.argv[1] if len(sys.argv) > 1 else "sample_report.png"
    print(f"Analyzing {file_path}...")
    result = analyze_report(file_path)

    for section in result["sections"]:
        print(f"\n=== SECTION: {section['report_type']} ===")

        print("\n--- RESULTS ---")
        for f in section["findings"]:
            if f["kind"] == "numeric":
                unit = f.get("unit", "")
                normal = f["normal_range"] if f["normal_range"] is not None else "N/A"
                source = f.get("range_source", "data")
                printed = f.get("printed_range")
                printed_note = f" [report printed: {printed}]" if printed else ""
                flag = "  ⚠ CRITICAL" if f.get("severity") == "critical" else ""
                print(
                    f"{f['name']}: {f['value']} {unit} → {f['status']} "
                    f"({f['severity']}, normal: {normal}, via: {source}){printed_note}{flag}"
                )
            elif f["kind"] == "narrative":
                print(f"[{f['section']}] {f['finding_text']}")

        advice = section["advice"]
        print("\n--- ADVICE ---")
        if isinstance(advice, dict):
            print(advice.get("summary", ""))
            for item in advice.get("findings", []):
                print(f"\n• {item.get('name', '')}:")
                print(f"  {item.get('advice', '')}")
        else:
            print(advice)

        print("\n--- DISCLAIMER ---")
        print(section.get("disclaimer", ""))

    skipped = result.get("skipped_pages", [])
    if skipped:
        pages = ", ".join(str(p) for p in skipped)
        print(f"\n--- NOTE ---\nSome pages could not be read and were skipped: page {pages}.")


if __name__ == "__main__":
    main()