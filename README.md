# 🌐 LinguaLeap — Smart Translator

A Flask-based web app for translating text and documents, with a
"boarding pass / passport" visual identity, live translation, voice
input, multi-language mode, and full file-to-file translation —
including correct rendering of right-to-left scripts (Urdu, Arabic,
Persian) in translated PDFs and Word docs.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.1-black)
![License](https://img.shields.io/badge/license-MIT-green)

## 📸 Screenshots

| Translate | Result |
|---|---|
| ![Translate tab, empty state](screenshots/01-translate-empty.png) | ![Translate tab, result](screenshots/02-translate-result.png) |

| File translation | Multi-language mode |
|---|---|
| ![Translate & download a file in the same format](screenshots/03-file-translate.png) | ![Translate into several languages at once](screenshots/04-multi-language.png) |

**History**
![Recent & saved translations](screenshots/05-history.png)

## ✨ Features
- Full visual redesign: parchment palette, Fraunces serif + IBM Plex
  Sans/Mono, perforated divider between source/translation,
  postmark-style language chips, dark mode.
- **Translate & Download (Same Format)** — upload a `.txt`, `.docx`,
  or `.pdf` and get back a translated file in the *same* format, with
  layout/formatting preserved as closely as each format allows.
- Live translation as you type, voice input, multi-language grid
  translation, history log, favorites, copy/listen.
- Text-to-speech playback of translated text.
- Correct **RTL (right-to-left) rendering** for Urdu, Arabic, and
  Persian — reshaped and right-aligned using `arabic-reshaper` +
  `python-bidi`, instead of disconnected letterforms or "tofu" boxes.

## 🩹 Fixed in this version
- **PDF output showing "▪▪▪▪" boxes instead of Urdu/Arabic text** —
  caused by the PDF writer using a font (Helvetica) with no
  Arabic-script glyphs. Now bundles proper Unicode fonts (Noto Naskh
  Arabic, Noto Sans Devanagari, Noto Sans) and registers them with
  the PDF engine.
- **Right-to-left rendering** — Urdu/Arabic/Persian text is now
  reshaped (letters joined correctly) and right-aligned instead of
  drawn as isolated letterforms.
- **Word (.docx) output** for RTL languages now sets right alignment,
  RTL paragraph direction, and the correct "complex script" font so
  Urdu/Arabic displays properly in Word.

## 🚀 How to run

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/lingualeap-translator.git
cd lingualeap-translator

# 2. (Recommended) create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Then open the printed link (usually **http://127.0.0.1:5000**) in your browser.

## 🛠 Tech stack
- **Backend:** Flask
- **Translation:** [deep-translator](https://pypi.org/project/deep-translator/) (Google Translate backend — no paid API key needed)
- **Text-to-speech:** gTTS
- **Document handling:** python-docx, pypdf, reportlab
- **RTL text shaping:** arabic-reshaper, python-bidi

## 📝 Notes
- Requires internet access at runtime for translation, TTS, and
  file-translation calls.
- The `fonts/` folder must stay next to `app.py` — it contains the
  Unicode fonts used to render non-Latin scripts in generated PDFs.
- History/favorites are stored in the browser's `localStorage`
  (per-browser, not synced).
- Long documents are automatically chunked to stay under the
  translation API's per-request character limit.
- PDF layout is rebuilt page-by-page (not pixel-identical to the
  original, since PDFs don't store re-flowable text) — page order
  and count are kept.

## 📄 License
This project is licensed under the MIT License — feel free to use,
modify, and distribute it.
