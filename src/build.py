#!/usr/bin/env python3
"""Build the Dice Puzzle game (dist/index.html) from source + data + books.

For every book in books/*.txt the script:
  * extracts the distinct words   -> data/<slug>_words.txt
  * builds a frequency-weighted 12x6 dice config + letter values
                                    -> data/<slug>_dice.json
  * auto-detects RTL (Arabic/Persian script) vs LTR (Latin)
  * embeds every book config into dist via the __BOOKS__ placeholder
"""
import json
import re
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SRC = ROOT / "src"
DIST = ROOT / "dist"
BOOKS = ROOT / "books"

NUM_DICE = 12
FACES_PER_DIE = 6
TOTAL_FACES = NUM_DICE * FACES_PER_DIE   # 72
MIN_WORD = 3

# Arabic/Persian letter ranges (used for RTL detection + word/letter extraction).
_ARABIC = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
_LATIN = re.compile(r"[A-Za-z]")
_LATIN_WORD = re.compile(r"[A-Za-z]+")
# An Arabic-script word may contain a ZWNJ (\u200c) between letter runs.
_ARABIC_WORD = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]+"
    r"(?:\u200c[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]+)*"
)


def is_rtl_text(text):
    """RTL if Arabic-script letters outnumber Latin letters in the text."""
    return len(_ARABIC.findall(text)) > len(_LATIN.findall(text))


def slugify(name):
    s = name.lower()
    s = re.sub(r"[^a-z0-9\u0600-\u06ff]+", "-", s).strip("-")
    return s or "book"


def extract_words(text, rtl):
    if rtl:
        raw = _ARABIC_WORD.findall(text)
        words = [w for w in raw if len(w) >= MIN_WORD]
    else:
        words = [w.lower() for w in _LATIN_WORD.findall(text) if len(w) >= MIN_WORD]
    return sorted(set(words))


def letter_freq(text, rtl):
    if rtl:
        return Counter(_ARABIC.findall(text))
    return Counter(c.upper() for c in _LATIN.findall(text))


def make_dice(freq):
    """12 dice x 6 faces, weighted by frequency, 6 distinct letters per die."""
    alphabet = [ch for ch, _ in freq.most_common()]   # most frequent first
    if not alphabet:
        return [["E", "A", "I", "O", "U", "T"] for _ in range(NUM_DICE)]
    total = sum(freq.values())
    targets = {}
    for ch in alphabet:
        t = round(TOTAL_FACES * freq[ch] / total)
        targets[ch] = max(1, min(NUM_DICE, t))
    # Adjust so the targets sum to exactly TOTAL_FACES (72).
    diff = TOTAL_FACES - sum(targets.values())
    guard = 0
    while diff != 0 and guard < 10000:
        guard += 1
        if diff > 0:
            for ch in alphabet:                       # add to frequent letters
                if diff == 0:
                    break
                if targets[ch] < NUM_DICE:
                    targets[ch] += 1
                    diff -= 1
        else:
            for ch in reversed(alphabet):             # trim rare letters
                if diff == 0:
                    break
                if targets[ch] > 1:
                    targets[ch] -= 1
                    diff += 1
    # Distribute: place each letter on `targets[ch]` dice that have the most free
    # slots and do not already carry that letter (keeps each die's 6 letters distinct).
    dice = [[] for _ in range(NUM_DICE)]
    for ch in alphabet:
        n = targets[ch]
        order = sorted(range(NUM_DICE),
                       key=lambda i: (-(FACES_PER_DIE - len(dice[i])), ch in dice[i]))
        placed = 0
        for i in order:
            if placed >= n:
                break
            if ch in dice[i] or len(dice[i]) >= FACES_PER_DIE:
                continue
            dice[i].append(ch)
            placed += 1
    return dice


def make_values(freq):
    """Scrabble-like letter values: common letters score low, rare letters high."""
    alpha = freq.most_common()                        # most frequent first
    n = len(alpha)
    if n == 0:
        return {}
    values = {}
    for idx, (ch, _) in enumerate(alpha):
        frac = idx / n
        if frac < 0.45:
            v = 1
        elif frac < 0.62:
            v = 2
        elif frac < 0.74:
            v = 3
        elif frac < 0.83:
            v = 4
        elif frac < 0.90:
            v = 5
        elif frac < 0.95:
            v = 8
        else:
            v = 10
        values[ch] = v
    return values


def process_book(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    rtl = is_rtl_text(text)
    slug = slugify(path.stem)
    title = path.stem.strip()
    words = extract_words(text, rtl)
    freq = letter_freq(text, rtl)
    dice = make_dice(freq)
    values = make_values(freq)
    (DATA / f"{slug}_words.txt").write_text("\n".join(words), encoding="utf-8")
    (DATA / f"{slug}_dice.json").write_text(
        json.dumps({"dice": dice, "values": values}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return {
        "key": slug,
        "title": title,
        "dir": "rtl" if rtl else "ltr",
        "langAttr": "fa" if rtl else "en",
        "digits": "\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9" if rtl else "0123456789",
        "dice": dice,
        "values": values,
        "wordsStr": "\n".join(words),
        "wordCount": len(words),
        "top": [ch for ch, _ in freq.most_common(6)],
    }


def main():
    template = (SRC / "template.html").read_text(encoding="utf-8")
    en_words = (DATA / "english_words.txt").read_text(encoding="utf-8").strip()
    fa_raw = (DATA / "farsi_words.txt").read_text(encoding="utf-8").strip().split("\n")
    fa_words = [w.strip().replace("\u200c", "") for w in fa_raw if w.strip()]
    en_cfg = json.loads((DATA / "english_dice.json").read_text(encoding="utf-8"))
    fa_cfg = json.loads((DATA / "farsi_dice_config.json").read_text(encoding="utf-8"))

    # Process every book in books/*.txt into data/<slug>_words.txt + _dice.json.
    books = []
    if BOOKS.is_dir():
        for p in sorted(BOOKS.glob("*.txt")):
            b = process_book(p)
            books.append(b)
            print(f"Book '{b['title']}' -> {b['wordCount']:,} words, dir={b['dir']}, "
                  f"top letters={b['top']}")

    replacements = {
        "__EN_DICE__":   json.dumps(en_cfg["dice"],   ensure_ascii=False),
        "__EN_VALUES__": json.dumps(en_cfg["values"], ensure_ascii=False),
        "__EN_WORDS__":  json.dumps(en_words,         ensure_ascii=False),
        "__FA_DICE__":   json.dumps(fa_cfg["dice"],   ensure_ascii=False),
        "__FA_VALUES__": json.dumps(fa_cfg["values"], ensure_ascii=False),
        "__FA_WORDS__":  json.dumps("\n".join(fa_words), ensure_ascii=False),
        "__BOOKS__":     json.dumps(books, ensure_ascii=False),
    }
    out = template
    for ph, val in replacements.items():
        if ph not in out:
            raise SystemExit(f"Placeholder {ph} not found in template")
        out = out.replace(ph, val)
    DIST.mkdir(exist_ok=True)
    (DIST / "index.html").write_text(out, encoding="utf-8")

    # Copy PWA assets (manifest, service worker, icons) into dist/, and add
    # .nojekyll so GitHub Pages serves the directory as-is (no Jekyll processing).
    pwa_src = SRC / "pwa"
    if pwa_src.is_dir():
        for f in pwa_src.iterdir():
            if f.is_file():
                shutil.copy2(f, DIST / f.name)
    (DIST / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Wrote {DIST / 'index.html'} ({len(out):,} bytes)")
    print(f"English words: {en_words.count(chr(10)) + 1:,}")
    print(f"Farsi words: {len(fa_words):,}")
    print(f"Books: {len(books)}")


if __name__ == "__main__":
    main()
