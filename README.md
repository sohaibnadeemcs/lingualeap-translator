# LinguaLeap — Smart Translator (v4)

A redesigned translation web app with a "boarding pass / passport" visual
identity, live translation, voice input, multi-language mode, and full
file-to-file translation — including correct rendering of right-to-left
scripts (Urdu, Arabic, Persian) in translated PDFs and Word docs.

## Fixed in this version
- **PDF output showing "■■■■" boxes instead of Urdu/Arabic text** — this was
  because the PDF writer used a font (Helvetica) with no Arabic-script glyphs.
  Now bundles proper Unicode fonts (Noto Naskh Arabic, Noto Sans Devanagari,
  Noto Sans) and registers them with the PDF engine.
- **Right-to-left rendering** — Urdu/Arabic/Persian text is now reshaped
  (letters joined correctly) and right-aligned using arabic-reshaper + python-bidi,
  instead of being drawn as isolated, disconnected letter forms.
- **Word (.docx) output** for RTL languages now sets right alignment, RTL
  paragraph direction, and the correct "complex script" font so Urdu/Arabic
  displays properly in Word.

## Features
- Full visual redesign: parchment palette, Fraunces serif + IBM Plex Sans/Mono,
  perforated divider between source/translation, postmark-style language chips,
  dark mode.
- **Translate & Download (Same Format)**: upload a .txt, .docx, or .pdf and get
  back a translated file in the SAME format, with layout/formatting preserved
  as closely as each format allows.
- Live translation as you type, voice input, multi-language grid translation,
  history log, favorites, copy/listen.

## How to run
1. `pip install -r requirements.txt`
2. `python app.py`
3. Open the printed link (usually http://127.0.0.1:5000)

## Notes
- Uses deep-translator (Google Translate backend) — no paid API key needed.
- Requires internet access at runtime for translation, TTS, and file-translation calls.
- The `fonts/` folder must stay next to `app.py` — it contains the Unicode
  fonts used to render non-Latin scripts in generated PDFs.
- History/favorites are stored in the browser's localStorage (per-browser, not synced).
- Long documents are automatically chunked to stay under the translation API's
  per-request character limit.
- PDF layout is rebuilt page-by-page (not pixel-identical to the original,
  since PDFs don't store re-flowable text) — page order and count are kept.
