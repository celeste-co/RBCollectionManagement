import json
from pathlib import Path

CARD_DATA_DIR = Path(__file__).resolve().parents[2] / "card_data"

def update_file(json_path: Path) -> int:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    changed = 0
    for card in data:
        domains = card.get("domains")
        power_cost = card.get("power_cost")
        if isinstance(domains, list) and len(domains) == 2 and isinstance(power_cost, int) and power_cost > 0:
            current = card.get("power_cost_map") or {}
            desired = {"Any": power_cost}
            if current != desired:
                card["power_cost_map"] = desired
                changed += 1

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return changed


def main():
    total = 0
    for jf in sorted(CARD_DATA_DIR.glob("*.json")):
        c = update_file(jf)
        print(f"Updated {jf.name}: {c} cards set to Any power cost")
        total += c
    print(f"\nDone. Total updated: {total}")


if __name__ == "__main__":
    main()
