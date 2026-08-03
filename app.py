"""
TASK 1: Language Translation Tool (v2 - Redesigned)
----------------------------------------------------
Modernized web app that:
1. Lets the user type (or speak) text and pick source & target language(s).
2. Translates live as you type, or into multiple target languages at once.
3. Shows translated text with copy / listen / history / favorites.
4. Supports uploading a .txt/.docx/.pdf file to translate its contents.

HOW TO RUN:
    1. pip install -r requirements.txt
    2. python app.py
    3. Open the link it prints (usually http://127.0.0.1:5000) in your browser.
"""

from flask import Flask, render_template, request, jsonify, send_file
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
import os

app = Flask(__name__)

FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# Languages that are written right-to-left and need bidi/reshaping before
# being drawn onto a PDF canvas.
RTL_LANGUAGES = {"ar", "ur", "fa", "he"}

# Which bundled Unicode font to use for a given target language, so
# translated PDFs don't render as "tofu" boxes for non-Latin scripts.
FONT_FOR_LANGUAGE = {
    "ar": "NotoNaskhArabic",
    "ur": "NotoNaskhArabic",
    "fa": "NotoNaskhArabic",
    "he": "NotoNaskhArabic",
    "hi": "NotoSansDevanagari",
}
DEFAULT_UNICODE_FONT = "NotoSans"

_FONTS_REGISTERED = False


def register_pdf_fonts():
    """Register bundled Noto fonts with reportlab once per process."""
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_files = {
        "NotoSans": "NotoSans-Regular.ttf",
        "NotoNaskhArabic": "NotoNaskhArabic-Regular.ttf",
        "NotoSansDevanagari": "NotoSansDevanagari-Regular.ttf",
    }
    for font_name, filename in font_files.items():
        path = os.path.join(FONTS_DIR, filename)
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(font_name, path))
    _FONTS_REGISTERED = True


def font_for_target(target):
    return FONT_FOR_LANGUAGE.get(target, DEFAULT_UNICODE_FONT)


def prepare_line_for_drawing(line, target):
    """For RTL languages, reshape Arabic-script letters into their correct
    joined forms and reorder for visual (left-to-right drawing) display."""
    if target not in RTL_LANGUAGES:
        return line
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(line)
        return get_display(reshaped)
    except Exception:
        return line

# Google Translate (via deep-translator) rejects requests over ~5000 chars,
# so long text gets split into safe-sized chunks and stitched back together.
CHUNK_LIMIT = 4500


def translate_long_text(text, source, target):
    """Translate arbitrarily long text by chunking on paragraph boundaries
    so we never exceed the API's per-request character limit."""
    if not text.strip():
        return ""
    if len(text) <= CHUNK_LIMIT:
        return GoogleTranslator(source=source, target=target).translate(text)

    pieces = re.split(r"(\n+)", text)
    chunks = []
    current = ""
    for piece in pieces:
        if len(current) + len(piece) <= CHUNK_LIMIT:
            current += piece
        else:
            if current:
                chunks.append(current)
            current = piece
    if current:
        chunks.append(current)

    translated_chunks = []
    for chunk in chunks:
        if chunk.strip():
            translated_chunks.append(GoogleTranslator(source=source, target=target).translate(chunk))
        else:
            translated_chunks.append(chunk)
    return "".join(translated_chunks)

# A short list of common languages: (code, display name)
LANGUAGES = {
    "auto": "Detect Language",
    "en": "English",
    "ur": "Urdu",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ar": "Arabic",
    "hi": "Hindi",
    "zh-CN": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian",
    "tr": "Turkish",
    "it": "Italian",
    "pt": "Portuguese",
    "bn": "Bengali",
    "pa": "Punjabi",
    "fa": "Persian",
    "id": "Indonesian",
    "nl": "Dutch",
}


@app.route("/")
def home():
    return render_template("index.html", languages=LANGUAGES)


@app.route("/translate", methods=["POST"])
def translate():
    """
    Receives JSON like: {"text": "hello", "source": "en", "target": "ur"}
    Returns JSON like: {"translated": "...", "detected_source": "en"}
    """
    data = request.get_json()
    text = data.get("text", "").strip()
    source = data.get("source", "auto")
    target = data.get("target", "en")

    if not text:
        return jsonify({"error": "Please enter some text to translate."}), 400

    try:
        translator = GoogleTranslator(source=source, target=target)
        translated_text = translator.translate(text)
        detected = None
        # deep-translator doesn't always expose detected language directly,
        # so we just echo back what was used.
        return jsonify({"translated": translated_text, "detected_source": detected})
    except Exception as e:
        return jsonify({"error": f"Translation failed: {str(e)}"}), 500


@app.route("/translate-multi", methods=["POST"])
def translate_multi():
    """
    Translate one piece of text into several target languages at once.
    Receives JSON like: {"text": "hello", "source": "en", "targets": ["ur","fr","ar"]}
    Returns JSON like: {"results": {"ur": "...", "fr": "...", "ar": "..."}, "errors": {...}}
    """
    data = request.get_json()
    text = data.get("text", "").strip()
    source = data.get("source", "auto")
    targets = data.get("targets", [])

    if not text:
        return jsonify({"error": "Please enter some text to translate."}), 400
    if not targets:
        return jsonify({"error": "Please select at least one target language."}), 400

    results = {}
    errors = {}
    for target in targets:
        try:
            results[target] = GoogleTranslator(source=source, target=target).translate(text)
        except Exception as e:
            errors[target] = str(e)

    return jsonify({"results": results, "errors": errors})


@app.route("/speak", methods=["POST"])
def speak():
    """
    Text-to-speech feature.
    Receives JSON like: {"text": "...", "lang": "ur"}
    Returns an MP3 audio file the browser can play.
    """
    data = request.get_json()
    text = data.get("text", "").strip()
    lang = data.get("lang", "en")

    if not text:
        return jsonify({"error": "No text to speak."}), 400

    try:
        tts_lang = lang if len(lang) == 2 else "en"
        tts = gTTS(text=text, lang=tts_lang)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return send_file(buf, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"error": f"Text-to-speech failed: {str(e)}"}), 500


@app.route("/extract", methods=["POST"])
def extract():
    """
    Accepts an uploaded file (.txt, .docx, .pdf) and returns its extracted text
    so the frontend can drop it into the input box for translation preview.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    f = request.files["file"]
    filename = (f.filename or "").lower()

    try:
        if filename.endswith(".txt"):
            text = f.read().decode("utf-8", errors="ignore")

        elif filename.endswith(".docx"):
            from docx import Document
            doc = Document(f)
            text = "\n".join(p.text for p in doc.paragraphs)

        elif filename.endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(f)
            text = "\n".join((page.extract_text() or "") for page in reader.pages)

        else:
            return jsonify({"error": "Unsupported file type. Use .txt, .docx, or .pdf."}), 400

        text = text.strip()
        if not text:
            return jsonify({"error": "Could not find any text in that file."}), 400

        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"error": f"Could not read file: {str(e)}"}), 500


@app.route("/translate-file", methods=["POST"])
def translate_file():
    """
    Accepts an uploaded file (.txt, .docx, .pdf) plus source/target language,
    translates its full contents, and returns a NEW file of the SAME type with
    the translation dropped back into place:
      - .txt  -> plain translated text file
      - .docx -> same document, paragraph/table text replaced in-place,
                 original styling (bold/italic/fonts/headings/tables) kept
      - .pdf  -> new PDF rebuilt page-by-page with the translated text
                 (exact original PDF layout can't be perfectly preserved,
                 since PDFs don't store re-flowable text, but page breaks
                 and reading order are kept)
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    f = request.files["file"]
    filename = f.filename or "upload"
    lower = filename.lower()
    source = request.form.get("source", "auto")
    target = request.form.get("target", "en")

    try:
        if lower.endswith(".txt"):
            original = f.read().decode("utf-8", errors="ignore")
            translated = translate_long_text(original, source, target)
            buf = io.BytesIO(translated.encode("utf-8"))
            buf.seek(0)
            out_name = filename.rsplit(".", 1)[0] + f"_{target}.txt"
            return send_file(buf, mimetype="text/plain", as_attachment=True, download_name=out_name)

        elif lower.endswith(".docx"):
            from docx import Document
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.oxml.ns import qn

            doc = Document(f)
            is_rtl = target in RTL_LANGUAGES

            def set_complex_script_font(run, name="Noto Naskh Arabic"):
                # Word renders Arabic-script text using the "complex script"
                # font slot (rPr/rFonts@cs), separate from the Latin font.
                rPr = run._element.get_or_add_rPr()
                rFonts = rPr.find(qn("w:rFonts"))
                if rFonts is None:
                    rFonts = rPr.makeelement(qn("w:rFonts"), {})
                    rPr.append(rFonts)
                rFonts.set(qn("w:cs"), name)
                rPr.set(qn("w:rtl"), "1") if False else None  # run-level rtl set below via bidi

            def translate_paragraph(p):
                if not p.text.strip():
                    return
                translated = translate_long_text(p.text, source, target)
                if p.runs:
                    p.runs[0].text = translated
                    for run in p.runs[1:]:
                        run.text = ""
                    if is_rtl:
                        set_complex_script_font(p.runs[0])
                else:
                    p.text = translated
                if is_rtl:
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    pPr = p._p.get_or_add_pPr()
                    bidi = pPr.makeelement(qn("w:bidi"), {})
                    pPr.append(bidi)

            for p in doc.paragraphs:
                translate_paragraph(p)

            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            translate_paragraph(p)

            buf = io.BytesIO()
            doc.save(buf)
            buf.seek(0)
            out_name = filename.rsplit(".", 1)[0] + f"_{target}.docx"
            return send_file(
                buf,
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                as_attachment=True,
                download_name=out_name,
            )

        elif lower.endswith(".pdf"):
            from pypdf import PdfReader
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch

            register_pdf_fonts()
            font_name = font_for_target(target)
            is_rtl = target in RTL_LANGUAGES

            reader = PdfReader(f)
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=letter)
            page_w, page_h = letter
            margin = 0.75 * inch
            usable_width = page_w - 2 * margin
            font_size = 12
            line_height = 18

            for page in reader.pages:
                raw_text = page.extract_text() or ""
                translated = translate_long_text(raw_text, source, target) if raw_text.strip() else ""

                c.setFont(font_name, font_size)
                y = page_h - margin

                def draw_line(text_line):
                    nonlocal y
                    if y < margin:
                        c.showPage()
                        c.setFont(font_name, font_size)
                        y = page_h - margin
                    display_line = prepare_line_for_drawing(text_line, target)
                    if is_rtl:
                        c.drawRightString(page_w - margin, y, display_line)
                    else:
                        c.drawString(margin, y, display_line)
                    y -= line_height

                for paragraph in translated.split("\n"):
                    if not paragraph.strip():
                        y -= line_height
                        continue
                    words = paragraph.split(" ")
                    line = ""
                    for word in words:
                        test_line = (line + " " + word).strip()
                        if c.stringWidth(prepare_line_for_drawing(test_line, target), font_name, font_size) <= usable_width:
                            line = test_line
                        else:
                            if line:
                                draw_line(line)
                            line = word
                    if line:
                        draw_line(line)

                c.showPage()

            c.save()
            buf.seek(0)
            out_name = filename.rsplit(".", 1)[0] + f"_{target}.pdf"
            return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=out_name)

        else:
            return jsonify({"error": "Unsupported file type. Use .txt, .docx, or .pdf."}), 400

    except Exception as e:
        return jsonify({"error": f"Could not translate file: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
