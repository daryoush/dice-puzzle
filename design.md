# Dice Puzzle — Design Document

## 1. Overview

Dice Puzzle is a bilingual word game. Twelve six-sided letter dice are thrown
onto a grid; the player drags them into rows or columns to spell words, which are
validated against an embedded dictionary and scored. Two extra tools help the
player: a **dictionary lookup** (tag letters, see all formable words containing
them) and a **structure move** (long-press to drag a connected group as one
unit). The whole game ships as one self-contained HTML file with both English
and Farsi built in.

## 2. Goals

- Single self-contained file — no server, no network, no dependencies.
- Work equally well for English (LTR) and Farsi (RTL), switchable live.
- Mouse and touch parity via Pointer Events.
- A genuinely useful anagram / word-finder, not just a game.
- Comfortable on phone, tablet, and desktop (responsive, no fixed widths).

## 3. Architecture

The project is a small data → build → dist pipeline:

    data/  ──┐
              ├──  src/build.py  ──>  dist/index.html
    src/template.html  ──┘

- **data/** holds the dictionaries and dice configurations as plain text/JSON.
- **src/template.html** is the full HTML/CSS/JS with `__PLACEHOLDER__` tokens.
- **src/build.py** reads the data, JSON-encodes it, substitutes the tokens, and
  writes `dist/index.html`.

The built file embeds both dictionaries as JavaScript string literals and parses
them into a `Set` on load, so the game is fully offline.

## 4. Runtime data structures

- `CONFIGS.{en,fa}` — per-language config: dice faces, letter values, text
  direction, UI strings, the word string, digit mapping, minimum word length.
- `dict` — a `Set` of words for the current language (lowercased).
- `wordsArr` — the same words as an array, used by the Find Words scan.
- `diceState` — an array of die objects: `{ id, sides, topFace, col, row, x, y,
  element, tagged }`. `col`/`row` are grid coordinates; `x`/`y` are pixels.
- `lang` — `'en'` or `'fa'`; `cfg()` returns the active config.

Switching language reloads the dictionary, flips `document.documentElement.dir`,
rewrites all UI text, and resets the board.

## 5. Core mechanics

### Throw
Each die rolls a random face and is placed in a random empty cell. Dice drop in
with a staggered CSS keyframe animation. During the animation, input is disabled
on each die until its animation ends.

### Grid and snapping
The grid is drawn with CSS background-size lines; cell size is derived from that.
Dragging moves a die by the pointer delta (clamped to the table). On release the
die snaps to the nearest empty cell; if that cell is taken, the nearest free cell
within an expanding Chebyshev radius is used. A dashed preview shows the snap
target during the drag.

### Word detection (direction-aware)
For each die, the scanner looks for a run that *starts* at that die:

- **Horizontal, LTR (English):** the die with no neighbour to its left starts a
  run extending right.
- **Horizontal, RTL (Farsi):** the die with no neighbour to its right starts a
  run extending left.
- **Vertical (both):** the die with no neighbour above starts a run extending
  down.

Within each run, a dynamic-programming pass finds the highest-scoring set of
non-overlapping dictionary words (reward = length² + downstream score). Words are
lowercased before lookup because the dictionary is lowercase; Persian letters
have no case, so lowercasing is a harmless no-op for Farsi.

### Scoring
Each letter's value comes from the language's value table (Scrabble for English,
a Persian frequency-weighted table for Farsi). The lookup is case-insensitive so
the lowercase dictionary words still score correctly against uppercase tile
letters.

## 6. Tagging and dictionary lookup

**Tagging.** A quick click (pointer down then up, movement under 5px, and before
the long-press timer fires) toggles a gold ring on a tile. Any number of tiles
can be tagged.

**Find Words.** Given the 12 shown letters and the tagged subset, the scan finds
every dictionary word that:

1. can be spelled from the multiset of shown letters (each letter used at most as
   many times as it appears on the board), and
2. contains every tagged letter (with multiplicity).

With no tags, condition (2) is vacuous, so it returns all formable words — an
anagram solver. Results are sorted longest-first, then by score. The scan is a
single linear pass over the dictionary (~315k English words), building a small
frequency counter per word with early exit; it finishes well under a second. A
`setTimeout(30)` lets a "searching…" indicator render before the heavy loop.

## 7. Structure move (long-press)

Three gestures share one tile:

- **Quick click** → toggles the tag.
- **Quick drag** (move > 5px before the timer) → moves a single tile.
- **Long-press then drag** (hold ~380 ms without moving) → grabs the whole
  connected structure.

A **structure** is the 4-connected component of dice reachable from the held die
via orthogonal adjacency — a straight row, a straight column, or any attached
shape (L, T, cross). It is found with an iterative flood fill over the grid map.

Once engaged, every tile in the structure moves by the same pixel delta and snaps
as a unit: the anchor snaps to its nearest cell, that offset (Δcol, Δrow) is
applied to every tile, and the offset is walked back toward (0,0) until the whole
group fits without bounds violation or collision with outside tiles. This means a
blocked move lands as close as possible instead of snapping back, and a built
word stays intact when repositioned.

`setPointerCapture` is wrapped in `try/catch` so a pointer-capture failure (some
environments reject synthetic or unsupported pointers) cannot abort the gesture.

## 8. Bilingual design

Everything language-specific lives in `CONFIGS`:

- **Direction:** `ltr` / `rtl`, applied to `<html dir>`. Horizontal word scanning
  reverses accordingly; vertical is always top-to-bottom.
- **Fonts:** a stack that covers Latin and Persian (Vazirmatn, Tahoma, …).
- **Digits:** scores render in Western digits for English and Eastern-Arabic
  digits for Farsi.
- **Text:** every button, label, hint, and modal string is per-language.
- **Data:** each language has its own dice, letter values, and dictionary.

The toggle reloads the dictionary, rewrites the UI, and resets the board, so the
two modes never interfere.

## 9. Responsiveness

- `meta viewport` with `user-scalable=no` so the grid does not jump on tap-zoom.
- Cell and die sizes use `clamp()` with viewport units; no fixed pixel widths.
- The layout is a flex column that fills `100dvh`; the table flexes to fill.
- On resize, dice are clamped back into bounds and re-gridded.

## 10. Key decisions and trade-offs

- **One file, two dictionaries.** Both word lists are embedded (~3.6 MB total).
  This makes the game trivially deployable and fully offline, at the cost of a
  larger file. Acceptable for this use case.
- **Set + array for the dictionary.** The `Set` gives O(1) membership for board
  detection; the array gives a fast linear scan for Find Words. Memory is
  duplicated but both are needed and the cost is modest.
- **Lowercase dictionary, case-insensitive lookup.** Keeps one canonical form
  and works for both caseless (Persian) and cased (English) scripts.
- **Long-press vs. a modifier key.** Long-press works on touch and mouse without
  a keyboard, matching "hold on a character".
- **4-connected structures.** Handles straight lines and arbitrary attached
  shapes uniformly; a built word is always one connected component.

## 11. Possible future work

- Per-letter scoring tweaks and bonus cells.
- A timed mode and a daily challenge.
- Exporting / importing custom dice sets and word lists.
- A service worker so the file can be installed as an offline app.
