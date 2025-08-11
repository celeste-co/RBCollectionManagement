import json
from pathlib import Path

CARD_DATA_DIR = Path(__file__).resolve().parents[2] / "card_data"

FINISHES_BY_RARITY = {
    "common": ["non_foil", "foil"],
    "uncommon": ["non_foil", "foil"],
    # Higher rarities only foil
}


def finishes_for_rarity(rarity: str):
    r = (rarity or "").strip().lower()
    return FINISHES_BY_RARITY.get(r, ["foil"])  # default to foil only


def update_file(json_path: Path) -> int:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    changed = 0
    for card in data:
        desired = finishes_for_rarity(card.get("rarity", ""))
        if card.get("finishes") != desired:
            card["finishes"] = desired
            changed += 1

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return changed


def main():
    if not CARD_DATA_DIR.exists():
        print(f"card_data directory not found: {CARD_DATA_DIR}")
        return

    total_changed = 0
    for json_file in sorted(CARD_DATA_DIR.glob("*.json")):
        changed = update_file(json_file)
        print(f"Updated {json_file.name}: {changed} cards")
        total_changed += changed

    print(f"\nDone. Total cards updated: {total_changed}")


if __name__ == "__main__":
    main()
