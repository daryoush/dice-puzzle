# Dice Puzzle

A bilingual (English + Farsi) dice word game packed into a single self-contained
HTML file. Roll 12 letter-dice onto a grid, drag them into rows or columns to
spell dictionary words, and score by Scrabble letter values. Switch languages
with one toggle.

## Features

- 12 dice, 6 faces each — letter frequencies modelled on English and Farsi.
- Throw and snap — dice drop onto a grid; drag to move, release to snap into the
  nearest empty cell. No two dice share a cell.
- Word detection — arrange dice in a horizontal row (left-to-right for English,
  right-to-left for Farsi) or a vertical column. The game finds the longest
  valid word in each line and scores it.
- Scrabble scoring — each tile shows its letter value; round and total scores
  accumulate across rounds.
- Click to tag + dictionary lookup — click a tile to tag it (gold ring), then
  press Find Words to list every dictionary word formable from the 12 shown
  letters that contains your tagged letters. With no tags, it lists all
  formable words — an anagram solver.
- Long-press to move a structure — hold a tile (~0.4s without moving) to grab
  its whole connected group. All attached tiles move and snap together as one
  unit, so a word you built stays intact when you reposition it.
- Language toggle — switch between English (LTR) and Farsi (RTL) at any time.
  Direction, fonts, dice faces, letter values, the dictionary, and all UI text
  switch together.

## Play

Open dist/index.html in any modern browser. No server, no build step, no
internet required — both dictionaries (315,100 English words and 19,625 Farsi
words) are embedded in the file. Or visit the live GitHub Pages deployment (see
below).

## Build from source

Run the build script from the project root:

    python3 src/build.py

or use the convenience wrapper:

    ./build.sh

This reads src/template.html and the files in data/, injects both dictionaries
and dice configs, and writes dist/index.html (about 3.6 MB, self-contained). It
also copies the PWA assets (manifest, service worker, icons) and a .nojekyll
file into dist/.

## Deploy to GitHub Pages

The repo includes a GitHub Actions workflow (.github/workflows/deploy.yml) that
builds dist/ and publishes it to GitHub Pages on every push to main. To use it:

1. Push this repo to GitHub.
2. In the repo: Settings → Pages → Build and deployment → Source: **GitHub Actions**.
3. Push to main (or run the workflow manually). The workflow builds dist/ and deploys it.
4. The game is live at: https://&lt;your-username&gt;.github.io/&lt;repo-name&gt;/

The app is a single self-contained HTML file with no external requests, so it
works at any subpath — no base-path configuration needed.

## Install as a PWA

The app is a Progressive Web App — installable and fully offline:

- **Install**: open the Pages URL in Chrome/Edge (desktop) or any Chromium
  browser on Android; use the install icon in the address bar (or menu →
  Install app). On iOS Safari, use Share → Add to Home Screen.
- **Offline**: a service worker (sw.js) caches the whole game (including both
  embedded dictionaries) on first visit, so it launches with no network.
- **Icons / manifest**: src/pwa/manifest.json plus the icons in src/pwa/ define
  the app name, theme color, and icons (including a maskable icon).

Reinstalling after an update: the service worker bumps its cache version on
deploy, so the new version activates on next launch.

## Project layout

    dice-puzzle/
    ├── readme.md            this file
    ├── design.md            design document
    ├── .gitignore
    ├── build.sh             convenience wrapper for src/build.py
    ├── .github/workflows/deploy.yml   builds + deploys dist/ to GitHub Pages
    ├── src/
    │   ├── build.py         assembles dist/index.html from template + data
    │   ├── template.html    HTML/CSS/JS template with __placeholders__
    │   └── pwa/             PWA source assets (copied into dist/ by build.py)
    │       ├── manifest.json        web app manifest
    │       ├── sw.js                service worker (offline cache)
    │       └── icon-{192,512,180}.png  app / maskable icons
    ├── data/
    │   ├── english_words.txt        315,100 English words (one per line)
    │   ├── english_dice.json        12 English dice + Scrabble letter values
    │   ├── farsi_words.txt          19,625 Farsi words (one per line)
    │   └── farsi_dice_config.json   12 Farsi dice + Persian letter values
    └── dist/
        ├── index.html       the built, self-contained game
        ├── manifest.json    PWA manifest
        ├── sw.js            service worker
        └── icon-*.png       PWA icons

## Data sources

- English words — a public-domain English word list (~315,000 entries).
- English dice — 12 dice x 6 faces, designed around English letter frequency
  and Scrabble point values.
- Farsi words — about 19,600 common Persian words.
- Farsi dice — 12 dice x 6 faces covering all 33 Persian letters (including آ),
  distributed by Persian letter frequency.

See design.md for the architecture, algorithms, and key design decisions.

## Tech

Vanilla HTML, CSS, and JavaScript. No frameworks, no runtime dependencies, no
build tooling beyond the small Python assembler. Pointer Events handle both mouse
and touch. Works offline via file://.
