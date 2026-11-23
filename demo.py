
from pathlib import Path

from core.pipeline import verify_offer


def main():
    sample_path = Path("data/samples/sample_offer.txt")

    if not sample_path.exists():
        print("Sample offer file not found.")
        return

    text = sample_path.read_text(encoding="utf-8")

    # example.com is only a synthetic test domain.
    # This is NOT a live company verification.
    report = verify_offer(
        text,
        official_domain="example.com",
    )

    print("\n=== OFFER EVIDENCE REPORT ===")
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
