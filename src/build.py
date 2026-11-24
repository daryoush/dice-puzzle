#!/usr/bin/env python3
"""Build the Dice Puzzle game (dist/index.html) from source + data."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SRC = ROOT / "src"
DIST = ROOT / "dist"

def main():
    template = (SRC / "template.html").read_text(encoding="utf-8")
    en_words = (DATA / "english_words.txt").read_text(encoding="utf-8").strip()
    fa_raw = (DATA / "farsi_words.txt").read_text(encoding="utf-8").strip().split("\n")
    fa_words = [w.strip().replace("\u200c", "") for w in fa_raw if w.strip()]
    en_cfg = json.loads((DATA / "english_dice.json").read_text(encoding="utf-8"))
    fa_cfg = json.loads((DATA / "farsi_dice_config.json").read_text(encoding="utf-8"))

    replacements = {
        "__EN_DICE__":   json.dumps(en_cfg["dice"],   ensure_ascii=False),
        "__EN_VALUES__": json.dumps(en_cfg["values"], ensure_ascii=False),
        "__EN_WORDS__":  json.dumps(en_words,         ensure_ascii=False),
        "__FA_DICE__":   json.dumps(fa_cfg["dice"],   ensure_ascii=False),
        "__FA_VALUES__": json.dumps(fa_cfg["values"], ensure_ascii=False),
        "__FA_WORDS__":  json.dumps("\n".join(fa_words), ensure_ascii=False),
    }
    out = template
    for ph, val in replacements.items():
        if ph not in out:
            raise SystemExit(f"Placeholder {ph} not found in template")
        out = out.replace(ph, val)
    DIST.mkdir(exist_ok=True)
    (DIST / "index.html").write_text(out, encoding="utf-8")
    print(f"Wrote {DIST / 'index.html'} ({len(out):,} bytes)")
    print(f"English words: {en_words.count(chr(10)) + 1:,}")
    print(f"Farsi words: {len(fa_words):,}")

if __name__ == "__main__":
    main()
