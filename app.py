
import streamlit as st
from PIL import Image, ImageOps, ImageEnhance
from pathlib import Path
from contextlib import contextmanager
import base64
import hashlib
import html
import importlib
import logging
import numpy as np
import shutil
import subprocess
import tempfile
import threading
import os
import io
import zipfile
import re

logger = logging.getLogger(__name__)

# ==========================================
# APPLICATION CONFIGURATION
# ==========================================

APP_NAME = "AB PDF Toolkit"
APP_VERSION = "2.6"
APP_URL = "https://ab-pdf-toolkit.streamlit.app/"
# Your repository, such as "yourname/yourrepo". The feedback link appears once this is set.
GITHUB_REPO = "anilbasakab/administrative-pdf-toolkit"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

st.set_page_config(
    page_title=f"{APP_NAME} | Free online PDF tools",
    page_icon=str(ASSETS_DIR / "favicon.png"),
    layout="wide",
    initial_sidebar_state="auto",
)

# All custom styling lives in assets/style.css
st.markdown(
    f"<style>{(ASSETS_DIR / 'style.css').read_text(encoding='utf-8')}</style>",
    unsafe_allow_html=True,
)

# ==========================================
# BRAND AND TOOL DETAILS
# ==========================================

LOGO_SVG = (
    '<svg viewBox="0 0 40 40" role="img" aria-label="AB PDF Toolkit logo">'
    '<rect width="40" height="40" rx="10" fill="#1D4ED8"/>'
    '<path d="M12 6h12l7 7v19a2 2 0 0 1-2 2H12a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z" fill="#FFFFFF"/>'
    '<path d="M24 6v7h7z" fill="#BFD0FF"/>'
    '<text x="20.5" y="28" text-anchor="middle" font-family="Arial, sans-serif" '
    'font-size="11" font-weight="700" fill="#1D4ED8">AB</text>'
    "</svg>"
)

TOOL_GROUPS = {
    "Convert": [
        "PDF to Word",
        "Word to PDF",
        "Batch PDF to Word",
        "Images to PDF",
        "PDF to Images",
        "Extract Text",
        "OCR Scanned PDF",
    ],
    "Organize": [
        "Merge PDF",
        "Split PDF",
        "Delete Pages",
        "Reorder Pages",
        "Rotate PDF",
        "Reverse PDF",
    ],
    "Enhance": [
        "Compress PDF",
        "Add Page Numbers",
        "Add Watermark",
        "Protect PDF",
        "Unlock PDF",
        "PDF Information",
    ],
}

TOOLS = [tool for group in TOOL_GROUPS.values() for tool in group]
INFO_PAGES = ["About", "Privacy", "FAQ"]

TOOL_GROUP_OF = {
    tool: group
    for group, group_tools in TOOL_GROUPS.items()
    for tool in group_tools
}

TOOL_DESCRIPTIONS = {
    "PDF to Word": "Turn a PDF into an editable Word file.",
    "Batch PDF to Word": "Convert many PDFs to Word in one go.",
    "Images to PDF": "Turn JPG, PNG and WebP images into one PDF.",
    "Merge PDF": "Combine several PDFs into one document.",
    "Split PDF": "Pull out just the pages you need.",
    "Rotate PDF": "Fix sideways pages, all or just a few.",
    "Reverse PDF": "Flip the page order, last page first.",
    "Compress PDF": "Shrink large PDFs and see the size saved.",
    "PDF Information": "Check page count, file size and metadata.",
    "Word to PDF": "Turn a Word document into a PDF.",
    "PDF to Images": "Save PDF pages as PNG or JPG pictures.",
    "Extract Text": "Pull the text out of a PDF into a text file.",
    "OCR Scanned PDF": "Make scanned pages searchable and selectable.",
    "Delete Pages": "Remove the pages you don't want.",
    "Reorder Pages": "Drag pages into the order you want.",
    "Add Page Numbers": "Number every page, where and how you like.",
    "Add Watermark": "Stamp text such as DRAFT across every page.",
    "Protect PDF": "Lock a PDF with a password.",
    "Unlock PDF": "Remove a password you already know.",
}

TOOL_KEYWORDS = {
    "PDF to Word": "docx doc convert editable",
    "Batch PDF to Word": "docx doc convert multiple bulk zip",
    "Images to PDF": "jpg jpeg png webp photo picture scan convert",
    "Merge PDF": "combine join",
    "Split PDF": "extract pages separate cut",
    "Rotate PDF": "turn orientation",
    "Reverse PDF": "order flip backwards",
    "Compress PDF": "reduce shrink smaller size optimize",
    "PDF Information": "details metadata properties pages",
    "Word to PDF": "docx doc convert document",
    "PDF to Images": "png jpg jpeg picture photo export convert",
    "Extract Text": "txt copy words convert",
    "OCR Scanned PDF": "scan recognize searchable hindi english text",
    "Delete Pages": "remove erase",
    "Reorder Pages": "arrange sort move drag order rearrange",
    "Add Page Numbers": "numbering footer header",
    "Add Watermark": "stamp draft confidential",
    "Protect PDF": "password encrypt secure lock",
    "Unlock PDF": "password decrypt remove open",
}

TOOL_ICONS = {
    "PDF to Word": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8"/><path d="M8 17h8"/>',
    "Batch PDF to Word": '<path d="M15 2H8a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V6z"/><path d="M15 2v4h4"/><path d="M3 7v13a2 2 0 0 0 2 2h10"/>',
    "Images to PDF": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.1-3.1a2 2 0 0 0-2.8 0L6 21"/>',
    "Merge PDF": '<path d="m12 2 9 5-9 5-9-5z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/>',
    "Split PDF": '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4 8.12 15.88"/><path d="M14.47 14.48 20 20"/><path d="M8.12 8.12 12 12"/>',
    "Rotate PDF": '<path d="M21 12a9 9 0 1 1-2.64-6.36L21 8"/><path d="M21 3v5h-5"/>',
    "Reverse PDF": '<path d="m21 16-4 4-4-4"/><path d="M17 20V4"/><path d="m3 8 4-4 4 4"/><path d="M7 4v16"/>',
    "Compress PDF": '<path d="M4 14h6v6"/><path d="M20 10h-6V4"/><path d="m14 10 7-7"/><path d="m3 21 7-7"/>',
    "PDF Information": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "Word to PDF": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M12 18v-6"/><path d="m9 15 3 3 3-3"/>',
    "PDF to Images": '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.5"/><path d="m21 15-4-4L7 19"/>',
    "Extract Text": '<path d="M4 7V5h16v2"/><path d="M12 5v14"/><path d="M9 19h6"/>',
    "OCR Scanned PDF": '<path d="M3 7V4h3"/><path d="M18 4h3v3"/><path d="M21 17v3h-3"/><path d="M6 20H3v-3"/><path d="M7 9h10"/><path d="M7 12h10"/><path d="M7 15h6"/>',
    "Delete Pages": '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v5"/><path d="M14 11v5"/>',
    "Reorder Pages": '<rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/><path d="M17 10V7h-3"/><path d="M7 14v3h3"/>',
    "Add Page Numbers": '<path d="M4 5h3v14"/><path d="M4 19h6"/><path d="M13 7a3 3 0 0 1 6 0c0 3-6 6-6 12h7"/>',
    "Add Watermark": '<path d="M12 3s7 7.5 7 12a7 7 0 0 1-14 0c0-4.5 7-12 7-12z"/>',
    "Protect PDF": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "Unlock PDF": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 7.5-2"/>',
}

# ==========================================
# NAVIGATION
# ==========================================

if st.session_state.get("nav_choice") not in ["Home"] + TOOLS + INFO_PAGES:
    st.session_state["nav_choice"] = "Home"


def open_page(page):
    st.session_state["nav_choice"] = page


def tool_slug(tool):
    return tool.lower().replace(" ", "_")


def tool_tile(tool):
    group = TOOL_GROUP_OF[tool].lower()
    return (
        f'<span class="tool-tile group-{group}">'
        f'<svg viewBox="0 0 24 24" aria-hidden="true">{TOOL_ICONS[tool]}</svg>'
        "</span>"
    )


selected_tool = st.session_state["nav_choice"]


@st.cache_resource
def preload_pdf_libraries():
    def load():
        for library in ("pymupdf", "pypdf", "pdf2docx"):
            importlib.import_module(library)

    threading.Thread(target=load, daemon=True).start()


# These libraries take seconds to load. The home page doesn't wait for them,
# but starts loading them so the first tool a visitor opens is ready sooner.
if selected_tool in TOOLS:
    import pymupdf
    from pdf2docx import Converter
    from pypdf import PdfReader, PdfWriter
else:
    preload_pdf_libraries()

with st.sidebar:
    st.markdown(
        f'<div class="brand">{LOGO_SVG}<span>{APP_NAME}</span></div>',
        unsafe_allow_html=True,
    )
    st.write("")

    st.button(
        "All tools",
        key="nav_home",
        type="primary" if selected_tool == "Home" else "tertiary",
        width="stretch",
        on_click=open_page,
        args=("Home",),
    )

    for group, group_tools in TOOL_GROUPS.items():
        st.markdown(
            f'<div class="nav-label">{group}</div>',
            unsafe_allow_html=True,
        )

        for tool in group_tools:
            st.button(
                tool,
                key=f"nav_{tool_slug(tool)}",
                type="primary" if selected_tool == tool else "tertiary",
                width="stretch",
                on_click=open_page,
                args=(tool,),
            )

    st.markdown('<div class="nav-label">Help</div>', unsafe_allow_html=True)

    for page in INFO_PAGES:
        st.button(
            page,
            key=f"nav_{page.lower()}",
            type="primary" if selected_tool == page else "tertiary",
            width="stretch",
            on_click=open_page,
            args=(page,),
        )

# The sidebar is hidden on phones, so the brand is repeated here for them
st.markdown(
    f'<div class="brand brand-mobile">{LOGO_SVG}<span>{APP_NAME}</span></div>',
    unsafe_allow_html=True,
)

if selected_tool != "Home":
    st.button(
        "All tools",
        key="global_home_button",
        type="tertiary",
        icon=":material/arrow_back:",
        on_click=open_page,
        args=("Home",),
    )

# ==========================================
# HELPER FUNCTIONS
# ==========================================

PDF_MIME = "application/pdf"
WORD_MIME = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document"
)
PASSWORD_MESSAGE = (
    "This PDF is password-protected. "
    "Please remove the password and upload it again."
)
UNREADABLE_MESSAGE = (
    "This file can't be read as a PDF. "
    "It may be damaged, or it may not be a real PDF."
)
NO_PAGES_MESSAGE = "This PDF has no pages."
MAX_THUMBNAILS = 12
THUMBNAIL_PIXELS = 260
MAX_DRAG_PAGES = 40
MAX_IMAGE_PAGES = 100
MAX_IMAGE_PIXELS = 50_000_000
MAX_OCR_PAGES = 50
OCR_DPI = 200
PAGE_MARGIN = 28
MAX_WORD_MEGABYTES = 50
WORD_TIMEOUT_SECONDS = 180
WORD_UNREADABLE_MESSAGE = (
    "This file can't be read as a Word document. "
    "It may be damaged, or it may not be a real Word file."
)
WORD_PASSWORD_MESSAGE = (
    "This Word document is password-protected. "
    "Please remove the password in Word and upload it again."
)
TESSDATA_DIR = ASSETS_DIR / "tessdata"
OCR_LANGUAGES = {
    "English": "eng",
    "Hindi": "hin",
    "English and Hindi": "eng+hin",
}
NUMBER_POSITIONS = [
    "Bottom center",
    "Bottom right",
    "Bottom left",
    "Top center",
    "Top right",
    "Top left",
]
NUMBER_STYLES = ["1", "Page 1", "Page 1 of 10"]
WATERMARK_COLORS = {
    "Gray": (0.45, 0.45, 0.45),
    "Red": (0.8, 0.1, 0.1),
    "Blue": (0.1, 0.25, 0.75),
}
WATERMARK_SIZES = {"Small": 0.45, "Medium": 0.65, "Large": 0.85}


class PdfFileError(Exception):
    """A problem with the uploaded file. The message is written for users."""


class PasswordProtectedError(PdfFileError):
    pass


def show_failure(action):
    """Call from an except block. Technical details go to the server log only."""
    logger.exception("%s failed", action)
    st.error(
        f"{action} failed. The file may be damaged or unusual. "
        "Please try another copy of it."
    )


def get_pdf_reader(data):
    try:
        reader = PdfReader(io.BytesIO(data))

        # A blank password opens files that only restrict printing or editing
        if reader.is_encrypted and not reader.decrypt(""):
            raise PasswordProtectedError(PASSWORD_MESSAGE)

        page_count = len(reader.pages)

    except PdfFileError:
        raise

    except Exception as error:
        raise PdfFileError(UNREADABLE_MESSAGE) from error

    if page_count == 0:
        raise PdfFileError(NO_PAGES_MESSAGE)

    return reader


def open_pdf_document(data):
    """Open a PDF with PyMuPDF. The caller closes it."""
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
    except Exception as error:
        raise PdfFileError(UNREADABLE_MESSAGE) from error

    if document.needs_pass:
        document.close()
        raise PasswordProtectedError(PASSWORD_MESSAGE)

    if document.page_count == 0:
        document.close()
        raise PdfFileError(NO_PAGES_MESSAGE)

    return document


def straighten_text_pages(document):
    """pdf2docx drops text running downward or right to left, so turn those
    pages until their main text reads normally. Returns True if any changed."""
    # Line directions from PyMuPDF ignore the page's rotation setting
    angles = {(1, 0): 0, (0, 1): 90, (-1, 0): 180, (0, -1): 270}
    changed = False

    for page in document:
        characters = {}

        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                direction = tuple(round(value) for value in line["dir"])
                characters[direction] = characters.get(direction, 0) + sum(
                    len(span["text"]) for span in line["spans"]
                )

        if not characters:
            continue

        angle = angles.get(max(characters, key=characters.get))

        if angle is not None and (angle + page.rotation) % 360 in (90, 180):
            page.set_rotation((360 - angle) % 360)
            changed = True

    return changed


def count_letters(text):
    return sum(character.isalnum() for character in text)


def word_file_text(docx_data):
    with zipfile.ZipFile(io.BytesIO(docx_data)) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")

    return "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", xml))


def convert_pdf_to_word(data):
    """Return the Word file, whether the PDF's text all reached it, and the page count."""
    document = open_pdf_document(data)

    try:
        page_count = document.page_count

        source_letters = count_letters(
            "".join(page.get_text() for page in document)
        )

        if straighten_text_pages(document):
            data = document.tobytes()

    finally:
        document.close()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        pdf_path = os.path.join(temp_dir, "input.pdf")
        docx_path = os.path.join(temp_dir, "output.docx")

        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(data)

        converter = Converter(pdf_path)

        try:
            converter.convert(docx_path)
        finally:
            converter.close()

        with open(docx_path, "rb") as docx_file:
            docx_data = docx_file.read()

    text_complete = (
        count_letters(word_file_text(docx_data)) >= source_letters * 0.9
    )

    return docx_data, text_complete, page_count


def find_libreoffice():
    """LibreOffice does the Word conversion. Cloud installs it from packages.txt."""
    return (
        shutil.which("soffice")
        or shutil.which("libreoffice")
        or next(
            (
                path
                for path in (
                    r"C:\Program Files\LibreOffice\program\soffice.exe",
                    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                )
                if os.path.exists(path)
            ),
            None,
        )
    )


def word_file_type(data):
    """Return ".docx" or ".doc", or raise a plain error for anything else."""
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if "word/document.xml" in archive.namelist():
                return ".docx"

        raise PdfFileError(WORD_UNREADABLE_MESSAGE)

    # Older .doc files, and password-protected .docx files, share this format
    if data.startswith(b"\xd0\xcf\x11\xe0"):
        if "EncryptedPackage".encode("utf-16-le") in data:
            raise PdfFileError(WORD_PASSWORD_MESSAGE)

        return ".doc"

    raise PdfFileError(WORD_UNREADABLE_MESSAGE)


def convert_word_to_pdf(data):
    suffix = word_file_type(data)

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        word_path = Path(temp_dir) / f"input{suffix}"
        word_path.write_bytes(data)

        # A separate profile lets two visitors convert at the same time
        profile = (Path(temp_dir) / "profile").as_uri()

        try:
            subprocess.run(
                [
                    find_libreoffice(),
                    "--headless",
                    "--norestore",
                    f"-env:UserInstallation={profile}",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    temp_dir,
                    str(word_path),
                ],
                capture_output=True,
                timeout=WORD_TIMEOUT_SECONDS,
            )

        except subprocess.TimeoutExpired as error:
            raise PdfFileError(
                "This document took too long to convert. It may be very large, "
                "or it may need a password."
            ) from error

        pdf_path = Path(temp_dir) / "input.pdf"

        # LibreOffice doesn't report a bad file: it just makes no PDF
        if not pdf_path.exists():
            raise PdfFileError(WORD_UNREADABLE_MESSAGE)

        return pdf_path.read_bytes()


def word_file_name(pdf_name):
    return pdf_name.rsplit(".", 1)[0] + ".docx"


def unique_name(name, used_names):
    """Add (2), (3)... so no two files in a ZIP share a name."""
    stem, extension = os.path.splitext(name)
    candidate = name
    number = 2

    while candidate.lower() in used_names:
        candidate = f"{stem} ({number}){extension}"
        number += 1

    used_names.add(candidate.lower())
    return candidate


def compress_pdf(data, dpi, quality):
    source_pdf = open_pdf_document(data)

    try:
        # Rebuilding pages as pictures loses text and sharp drawings, so it is
        # kept for scans, where every page is an image with no text
        is_scan = all(
            page.get_images() and not page.get_text().strip()
            for page in source_pdf
        )

        if not is_scan:
            source_pdf.rewrite_images(
                dpi_threshold=dpi + 10,
                dpi_target=dpi,
                quality=quality
            )
            return source_pdf.tobytes(garbage=4, deflate=True)

        compressed_pdf = pymupdf.open()

        try:
            for page in source_pdf:
                pix = page.get_pixmap(
                    matrix=pymupdf.Matrix(dpi / 72, dpi / 72),
                    alpha=False
                )

                image = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples
                )

                image_buffer = io.BytesIO()
                image.save(
                    image_buffer,
                    format="JPEG",
                    quality=quality,
                    optimize=True
                )

                new_page = compressed_pdf.new_page(
                    width=page.rect.width,
                    height=page.rect.height
                )

                new_page.insert_image(
                    new_page.rect,
                    stream=image_buffer.getvalue()
                )

            return compressed_pdf.tobytes(garbage=4, deflate=True)

        finally:
            compressed_pdf.close()

    finally:
        source_pdf.close()


def creation_date_text(metadata):
    # pypdf raises an error when a file holds an invalid date
    try:
        created = metadata.creation_date
    except Exception:
        return str(metadata.get("/CreationDate") or "") or None

    return created.strftime("%d %b %Y, %H:%M") if created else None


@st.cache_data(ttl=900, max_entries=64, show_spinner=False)
def render_thumbnails(data, pages):
    """JPEG thumbnails for (page index, extra rotation) pairs.

    A preview is only a convenience, so a file that can't be drawn gives an
    empty list here and the tool itself reports any real problem.
    """
    try:
        document = open_pdf_document(data)
    except PdfFileError:
        return []

    try:
        thumbnails = []

        for page_index, extra_rotation in pages:
            page = document[page_index]
            page.set_rotation((page.rotation + extra_rotation) % 360)
            zoom = THUMBNAIL_PIXELS / max(page.rect.width, page.rect.height)
            pix = page.get_pixmap(
                matrix=pymupdf.Matrix(zoom, zoom),
                alpha=False
            )
            thumbnails.append(pix.tobytes("jpeg", jpg_quality=70))

        return thumbnails

    except Exception:
        logger.exception("Preview failed")
        return []

    finally:
        document.close()


def pdf_page_count(data):
    document = open_pdf_document(data)
    page_count = document.page_count
    document.close()
    return page_count


def file_stem(name):
    return name.rsplit(".", 1)[0]


def select_pages(data, pages):
    """Keep the given pages, in the given order. Bookmarks are kept too."""
    document = open_pdf_document(data)

    try:
        document.select(pages)
        return document.tobytes(garbage=3, deflate=True)

    finally:
        document.close()


def stamp_pages(data, stamp, preview=False):
    """Run stamp(page, index, total) on every page, or only the first for a preview."""
    document = open_pdf_document(data)

    try:
        total = document.page_count

        for index, page in enumerate(document):
            if preview and index > 0:
                break

            # Protects the stamp from settings left behind by the page's content
            if not page.is_wrapped:
                page.wrap_contents()

            stamp(page, index, total)

        if preview:
            document.select([0])

        return document.tobytes(garbage=3, deflate=True)

    finally:
        document.close()


def add_page_numbers(data, position, style, first_number, preview=False):
    def stamp(page, index, total):
        number = first_number + index

        if style == "1":
            text = str(number)
        elif style == "Page 1":
            text = f"Page {number}"
        else:
            text = f"Page {number} of {first_number + total - 1}"

        size = 11
        width = pymupdf.get_text_length(text, "helv", size)
        rect = page.rect

        if "left" in position:
            x = PAGE_MARGIN
        elif "right" in position:
            x = rect.width - PAGE_MARGIN - width
        else:
            x = (rect.width - width) / 2

        y = PAGE_MARGIN + size if "Top" in position else rect.height - PAGE_MARGIN

        page.insert_text(
            pymupdf.Point(x, y) * page.derotation_matrix,
            text,
            fontname="helv",
            fontsize=size,
            color=(0.2, 0.2, 0.2),
            rotate=page.rotation,
        )

    return stamp_pages(data, stamp, preview)


def add_watermark(data, text, color, size, opacity, diagonal, preview=False):
    def stamp(page, index, total):
        rect = page.rect
        span = (rect.width ** 2 + rect.height ** 2) ** 0.5 if diagonal else rect.width
        font_size = 100 * span * size / pymupdf.get_text_length(text, "helv", 100)
        width = pymupdf.get_text_length(text, "helv", font_size)
        centre = pymupdf.Point(rect.width / 2, rect.height / 2)

        page.insert_text(
            pymupdf.Point(centre.x - width / 2, centre.y + font_size / 3)
            * page.derotation_matrix,
            text,
            fontname="helv",
            fontsize=font_size,
            color=color,
            fill_opacity=opacity,
            rotate=page.rotation,
            morph=(
                centre * page.derotation_matrix,
                pymupdf.Matrix(45 if diagonal else 0),
            ),
        )

    return stamp_pages(data, stamp, preview)


def pdf_to_images(data, pages, dpi, image_format, stem):
    """Return (file name, picture bytes) for each chosen page."""
    document = open_pdf_document(data)

    try:
        images = []

        for page_index in pages:
            page = document[page_index]
            area = page.rect.width * page.rect.height
            # Very large pages are scaled so one page can't use up the server's memory
            zoom = min(dpi / 72, (MAX_IMAGE_PIXELS / area) ** 0.5)
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
            name = f"{stem}_page_{page_index + 1:03d}"

            if image_format == "PNG":
                images.append((f"{name}.png", pix.tobytes("png")))
            else:
                images.append((f"{name}.jpg", pix.tobytes("jpeg", jpg_quality=85)))

        return images

    finally:
        document.close()


def extract_pdf_text(data, pages):
    document = open_pdf_document(data)

    try:
        return "\n\n".join(
            f"--- Page {page_index + 1} ---\n\n{document[page_index].get_text().strip()}"
            for page_index in pages
        )

    finally:
        document.close()


def password_fingerprint(password):
    # Lets a result be matched to its password without keeping the password
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def protect_pdf(data, password):
    document = open_pdf_document(data)

    try:
        return document.tobytes(
            garbage=3,
            deflate=True,
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            user_pw=password,
            owner_pw=password,
        )

    finally:
        document.close()


def pdf_lock_state(data):
    """Return "password", "restricted" or "none"."""
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
    except Exception as error:
        raise PdfFileError(UNREADABLE_MESSAGE) from error

    try:
        if document.needs_pass:
            return "password"

        return "restricted" if document.metadata.get("encryption") else "none"

    finally:
        document.close()


def unlock_pdf(data, password):
    state = pdf_lock_state(data)
    document = pymupdf.open(stream=data, filetype="pdf")

    try:
        access = document.authenticate(password)

        # A restricted file opens for anyone, so only its owner password counts
        allowed = access > 0 if state == "password" else access & 4

        if not allowed:
            raise PdfFileError(
                "That password isn't correct. Please check it and try again."
            )

        return document.tobytes(garbage=3, deflate=True)

    finally:
        document.close()


def ocr_is_available(language):
    return all(
        (TESSDATA_DIR / f"{code}.traineddata").exists()
        for code in language.split("+")
    )


def ocr_pdf(data, language, on_page=None):
    """Return a searchable PDF and how many pages were read.

    Pages that already have text are copied as they are. Scanned pages become
    a picture with an invisible text layer on top.
    """
    source = open_pdf_document(data)
    output = pymupdf.open()

    try:
        pages_read = 0

        for index, page in enumerate(source):
            if on_page:
                on_page(index, source.page_count)

            if page.get_text().strip():
                output.insert_pdf(source, from_page=index, to_page=index)
                continue

            pix = page.get_pixmap(dpi=OCR_DPI, alpha=False)
            page_pdf = pix.pdfocr_tobytes(
                language=language,
                tessdata=str(TESSDATA_DIR)
            )

            with pymupdf.open(stream=page_pdf, filetype="pdf") as scanned:
                output.insert_pdf(scanned)

            pages_read += 1

        # The OCR pictures are stored without loss, so shrink them to photo size
        output.rewrite_images(dpi_threshold=OCR_DPI + 10, dpi_target=OCR_DPI, quality=70)

        return output.tobytes(garbage=3, deflate=True), pages_read

    finally:
        source.close()
        output.close()


def image_thumbnail(image):
    thumbnail = image.copy()
    thumbnail.thumbnail((THUMBNAIL_PIXELS, THUMBNAIL_PIXELS))
    buffer = io.BytesIO()
    thumbnail.save(buffer, format="JPEG", quality=70)
    return buffer.getvalue()


def to_rgb(image):
    # 16-bit grayscale must be scaled down, or mid-gray turns white
    if image.mode.startswith("I"):
        pixels = np.asarray(image, dtype="float32") / 256
        image = Image.fromarray(pixels.clip(0, 255).astype("uint8"))

    # Transparent areas become white paper, not black
    if image.mode in ("RGBA", "LA", "PA") or "transparency" in image.info:
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, "white")
        background.paste(image, mask=image.getchannel("A"))
        return background

    return image.convert("RGB")


def enhance_image(image, mode):
    image = to_rgb(ImageOps.exif_transpose(image))

    if mode == "Original":
        return image

    if mode == "Magic Color":
        image = ImageOps.autocontrast(image, cutoff=1)
        image = ImageEnhance.Color(image).enhance(1.25)
        image = ImageEnhance.Contrast(image).enhance(1.15)
        image = ImageEnhance.Sharpness(image).enhance(1.2)
        return image

    if mode == "Document":
        image = ImageOps.autocontrast(image, cutoff=2)
        image = ImageEnhance.Contrast(image).enhance(1.5)
        image = ImageEnhance.Sharpness(image).enhance(1.4)
        return image

    if mode == "Grayscale":
        return ImageOps.grayscale(image).convert("RGB")

    if mode == "Black & White":
        grayscale = ImageOps.grayscale(image)
        grayscale = ImageOps.autocontrast(grayscale)
        return grayscale.point(
            lambda pixel: 255 if pixel > 165 else 0
        ).convert("RGB")

    return image


@st.cache_data(ttl=900, max_entries=64, show_spinner=False)
def image_preview(data, mode):
    """A small filtered preview, or None if the file can't be read as an image.

    Saved so the page doesn't redo this work on every click. Full-size images
    are only processed when the PDF is created.
    """
    try:
        with Image.open(io.BytesIO(data)) as source:
            # Lets large JPEGs load at a reduced size, which is far quicker
            source.draft(None, (THUMBNAIL_PIXELS * 2, THUMBNAIL_PIXELS * 2))
            return image_thumbnail(enhance_image(source, mode))

    except Exception:
        return None


def parse_page_ranges(text, total_pages):
    """Accept ranges such as 1-3,5,7-9."""
    return sorted(set(expand_page_text(text, total_pages)))


def parse_page_order(text, total_pages):
    """Read a new page order. Pages not mentioned follow in their old order."""
    pages = expand_page_text(text, total_pages)

    if len(set(pages)) != len(pages):
        raise ValueError("Each page can only be listed once.")

    return pages + [page for page in range(total_pages) if page not in set(pages)]


def expand_page_text(text, total_pages):
    pages = []

    for part in text.split(","):
        part = part.strip()

        if not part:
            continue

        if "-" in part:
            start, end = part.split("-", 1)

            if not start.strip().isdecimal() or not end.strip().isdecimal():
                raise ValueError("Invalid page range.")

            first = int(start)
            last = int(end)

            if first > last:
                raise ValueError("Range start must not exceed end.")

            selected = range(first, last + 1)

        else:
            if not part.isdecimal():
                raise ValueError("Invalid page number.")

            selected = [int(part)]

        for page in selected:
            if page < 1 or page > total_pages:
                raise ValueError(
                    f"Page {page} is outside the PDF."
                )

            pages.append(page - 1)

    if not pages:
        raise ValueError("Please enter valid page numbers.")

    return pages


@contextmanager
def tool_errors(action):
    """Turn any problem inside a tool into a plain message."""
    try:
        yield

    except PdfFileError as e:
        st.error(str(e))

    except ValueError as e:
        st.warning(f"Check your page selection: {e}")

    except Exception:
        show_failure(action)


def choose_pages(total_pages, key):
    """Return the chosen pages, or nothing until a selection has been typed."""
    mode = st.radio(
        "Pages",
        ["All pages", "Selected pages"],
        horizontal=True,
        key=f"{key}_mode",
    )

    if mode == "All pages":
        return list(range(total_pages))

    text = st.text_input(
        "Page numbers",
        placeholder="Example: 1-5, 8, 10-12",
        key=f"{key}_text",
    )

    return parse_page_ranges(text, total_pages) if text else []


@st.cache_resource
def reorder_component():
    return st.components.v2.component(
        "reorder_pages",
        js=(ASSETS_DIR / "reorder_pages.js").read_text(encoding="utf-8"),
        isolate_styles=False,
    )


def drag_page_order(file, data, total_pages):
    """Show the draggable pages and return the order the user has arranged."""
    saved_key = f"reorder_saved_{file.file_id}"
    saved = st.session_state.get(saved_key, list(range(total_pages)))
    thumbnails = render_thumbnails(
        data,
        tuple((page_index, 0) for page_index in range(total_pages))
    )

    if not thumbnails:
        return saved

    result = reorder_component()(
        data={
            "signature": file.file_id,
            "order": saved,
            "thumbnails": [
                base64.b64encode(thumbnail).decode("ascii")
                for thumbnail in thumbnails
            ],
        },
        default={"order": None},
        key=f"reorder_{file.file_id}",
        on_order_change=lambda: None,
    )

    if result.order and sorted(result.order) == list(range(total_pages)):
        saved = list(result.order)
        st.session_state[saved_key] = saved

    return saved


def pages_text(count):
    return f"{count} page" if count == 1 else f"{count} pages"


def size_text(size):
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"

    return f"{size / 1024 / 1024:.2f} MB"


step_count = 0


def tool_step(title):
    """Numbered heading, so every tool reads upload, options, process, download."""
    global step_count
    step_count += 1

    st.markdown(
        f'<div class="tool-step"><span class="tool-step-number">{step_count}</span>'
        f"{title}</div>",
        unsafe_allow_html=True,
    )


def show_thumbnails(items, total=None):
    """Show (JPEG bytes or None, caption) pairs as a grid of small previews."""
    figures = []

    for image_data, caption in items:
        if image_data:
            encoded = base64.b64encode(image_data).decode("ascii")
            picture = f'<img src="data:image/jpeg;base64,{encoded}" alt="">'
        else:
            picture = '<div class="thumb-empty">No preview</div>'

        figures.append(
            f'<figure class="thumb">{picture}'
            f"<figcaption>{html.escape(caption)}</figcaption></figure>"
        )

    st.html(f'<div class="thumb-grid">{"".join(figures)}</div>')

    if total and total > len(items):
        st.caption(f"Showing {len(items)} of {total}.")


def show_page_previews(data, pages, total=None):
    """Preview a PDF's pages, given as (page index, extra rotation) pairs."""
    pages = pages[:MAX_THUMBNAILS]
    thumbnails = render_thumbnails(data, tuple(pages))

    if thumbnails:
        show_thumbnails(
            [
                (thumbnail, f"Page {page_index + 1}")
                for thumbnail, (page_index, _) in zip(thumbnails, pages)
            ],
            total
        )


def show_first_pages(files):
    """Preview the first page of each file, numbered in the order given."""
    items = []

    for position, file in enumerate(files[:MAX_THUMBNAILS], start=1):
        thumbnails = render_thumbnails(file.getvalue(), ((0, 0),))
        items.append((
            thumbnails[0] if thumbnails else None,
            f"{position}. {file.name}"
        ))

    show_thumbnails(items, len(files))


def result_source(files, *settings):
    """Identify what a result was made from, so a stale one is never offered."""
    return (selected_tool, [file.file_id for file in files], settings)


def save_result(
    source, message, label=None, data=None, file_name=None,
    mime=PDF_MIME, warnings=(), facts=(), text_preview=None
):
    # Only the latest result is kept, to limit memory use on the server
    st.session_state["tool_result"] = {
        "source": source,
        "message": message,
        "label": label,
        "data": data,
        "file_name": file_name,
        "mime": mime,
        "warnings": warnings,
        "facts": facts,
        "text_preview": text_preview,
    }


def show_result(source):
    """Show the saved result, which stays until the file or settings change."""
    result = st.session_state.get("tool_result")

    if not result or result["source"] != source:
        return

    # No file to offer: the message explains why
    if result["data"] is None:
        st.info(result["message"])
        return

    tool_step("Download")

    with st.container(key="result_card"):
        st.success(result["message"])

        for warning in result["warnings"]:
            st.warning(warning)

        if result["facts"]:
            columns = st.columns(len(result["facts"]))

            for column, (name, value) in zip(columns, result["facts"]):
                column.metric(name, value)

        if result["text_preview"]:
            st.text_area(
                "Text preview",
                result["text_preview"],
                height=220,
                disabled=True,
            )

        st.download_button(
            label=result["label"],
            data=result["data"],
            file_name=result["file_name"],
            mime=result["mime"],
            icon=":material/download:",
            type="primary",
            width="stretch",
            on_click="ignore"
        )


def render_tool_header(title, description):
    st.markdown(
        f'<div class="tool-header">{tool_tile(title)}<div>'
        f'<h1 class="tool-title">{title}</h1>'
        f'<p class="tool-text">{description}</p>'
        "</div></div>",
        unsafe_allow_html=True,
    )


def render_about():
    st.markdown(
        '<h1 class="tool-title">About</h1>'
        f'<p class="tool-text">{APP_NAME} is a free set of everyday PDF tools.</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
**What it is.** {len(TOOLS)} tools for converting, organizing and improving
PDFs, in one place. There is no account to create and nothing to install.

**Who it's for.** Anyone who needs a quick PDF job done: students, office
staff, small businesses and anyone handling paperwork.

**How it's built.** It's an independent project written in Python and hosted
on Streamlit Community Cloud. It relies on open-source libraries including
PyMuPDF, pypdf, pdf2docx, Pillow, LibreOffice and the Tesseract OCR engine.
"""
    )


def render_privacy():
    st.markdown(
        '<h1 class="tool-title">Privacy</h1>'
        '<p class="tool-text">What happens to your files, in plain language.</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
#### Your files
- Your files are sent to the server that runs this app, so the tools can work on them.
- The app doesn't save your files permanently. It holds them in the server's
  memory while your browser tab is open.
- PDF to Word and Word to PDF write temporary files while they convert, and delete them straight after.
- Your latest result stays in memory so you can download it again, until you
  make another result or your session ends.
- Small page previews stay in memory for about 15 minutes.

#### Your passwords
Passwords for Protect PDF and Unlock PDF are used only for that action. The app
doesn't save them to any file or database. They stay in memory only while your
session is open.

#### Accounts, ads and tracking
The app has no accounts and no ads, and it adds no tracking of its own.

#### The hosting service
The app runs on Streamlit Community Cloud, a shared public service with its own
technical logs and policies. The app's own error logs may include a file's name,
but not its contents.

#### Sensitive documents
Because this is a public cloud service, please avoid uploading highly
confidential documents, such as identity papers, bank statements or medical records.
"""
    )


FAQ_ITEMS = [
    (
        "Is it really free?",
        "Yes. All the tools are free to use, with no sign-up."
    ),
    (
        "How large can my files be?",
        "Up to 200 MB per file. Large files take longer, and OCR handles "
        f"up to {MAX_OCR_PAGES} pages at a time."
    ),
    (
        "Why was the site slow to open?",
        "The free hosting puts the app to sleep when nobody has used it for a "
        "while. The first visitor after that may wait while it wakes up."
    ),
    (
        "Why does my Word document look a little different as a PDF?",
        "If it uses a font this service doesn't have, a similar font is used "
        "instead, which can shift the layout slightly."
    ),
    (
        "Why can't I select the text in my scanned PDF?",
        "A scan is a picture of a page, so it has no real text. Run OCR Scanned "
        "PDF first, and the words can then be searched and copied."
    ),
    (
        "Is OCR always accurate?",
        "No. It can misread words, especially in faint scans or Hindi text. "
        "Please check anything important."
    ),
    (
        "Which languages does OCR support?",
        "English and Hindi, separately or together."
    ),
    (
        "I forgot the password I set. Can you recover it?",
        "No. The password isn't kept, so nobody can recover it. Please keep "
        "your original file until you're sure you have the password safe."
    ),
    (
        "Can I remove a password I don't know?",
        "No. Unlock PDF only works when you enter the correct password."
    ),
    (
        "Does it work on a phone?",
        "Yes. To reorder pages on a touch screen, use the arrow buttons."
    ),
]


def render_faq():
    st.markdown(
        '<h1 class="tool-title">FAQ</h1>'
        '<p class="tool-text">Quick answers to common questions.</p>',
        unsafe_allow_html=True,
    )

    st.write("")

    for question, answer in FAQ_ITEMS:
        with st.expander(question):
            st.write(answer)


def render_home():
    with st.container(key="hero"):
        st.markdown(
            '<h1 class="hero-title">Every PDF tool you need, in one place.</h1>'
            '<p class="hero-text">Convert, merge, split, rotate and compress '
            "your documents in a few clicks.</p>"
            f'<div class="hero-facts"><span>{len(TOOLS)} tools</span>'
            "<span>Free to use</span><span>No sign-up</span></div>",
            unsafe_allow_html=True,
        )

        search_query = st.text_input(
            "Search tools",
            placeholder="Search tools: merge, rotate, Word, images...",
            key="home_tool_search",
            label_visibility="collapsed",
        ).strip().lower()

    matching_tools = [
        tool
        for tool in TOOLS
        if search_query in tool.lower()
        or search_query in TOOL_DESCRIPTIONS[tool].lower()
        or search_query in TOOL_KEYWORDS[tool]
    ]

    if not matching_tools:
        st.info("No tools match your search. Try another keyword.")

    columns = st.columns(len(TOOL_GROUPS))

    for column, (group, group_tools) in zip(columns, TOOL_GROUPS.items()):
        visible_tools = [
            tool for tool in group_tools if tool in matching_tools
        ]

        if not visible_tools:
            continue

        with column:
            st.markdown(
                f'<div class="group-label group-{group.lower()}">{group}</div>',
                unsafe_allow_html=True,
            )

            for tool in visible_tools:
                with st.container(key=f"card_{tool_slug(tool)}"):
                    st.markdown(
                        f'<div class="tool-card">{tool_tile(tool)}<div>'
                        f'<div class="tool-card-title">{tool}</div>'
                        f'<div class="tool-card-text">{TOOL_DESCRIPTIONS[tool]}</div>'
                        "</div></div>",
                        unsafe_allow_html=True,
                    )

                    st.button(
                        f"Open {tool}",
                        key=f"open_{tool_slug(tool)}",
                        on_click=open_page,
                        args=(tool,),
                    )

    steps = [
        ("Upload", "Choose your PDF or image files."),
        ("Adjust", "Set page ranges or other options."),
        ("Process", "Let the tool do the work."),
        ("Download", "Save your finished file."),
    ]

    steps_html = "".join(
        f'<div class="step"><div class="step-number">{number}</div>'
        f'<div class="step-title">{title}</div>'
        f'<div class="step-text">{text}</div></div>'
        for number, (title, text) in enumerate(steps, start=1)
    )

    st.markdown(
        '<h2 class="section-title">How it works</h2>'
        f'<div class="steps">{steps_html}</div>',
        unsafe_allow_html=True,
    )


# ==========================================
# 1. PDF TO WORD
# ==========================================


if selected_tool == "Home":
    render_home()


elif selected_tool == "About":
    render_about()


elif selected_tool == "Privacy":
    render_privacy()


elif selected_tool == "FAQ":
    render_faq()


elif selected_tool == "PDF to Word":
    render_tool_header(
        "PDF to Word",
        "Convert PDF documents into editable Word files."
    )

    tool_step("Upload your PDF")

    uploaded = st.file_uploader(
        "Upload your PDF",
        type=["pdf"],
        key="single_word",
        label_visibility="collapsed"
    )

    if uploaded:
        pdf_data = uploaded.getvalue()

        show_page_previews(pdf_data, [(0, 0)])

        source = result_source([uploaded])

        tool_step("Convert")

        if st.button("Convert to Word", type="primary", width="stretch"):
            try:
                with st.spinner("Converting PDF to Word..."):
                    docx_data, text_complete, page_count = convert_pdf_to_word(
                        pdf_data
                    )

                save_result(
                    source,
                    "Your Word document is ready.",
                    "Download Word Document",
                    docx_data,
                    word_file_name(uploaded.name),
                    WORD_MIME,
                    warnings=() if text_complete else (
                        "Some text may be missing from the Word file. "
                        "Please compare it with your PDF.",
                    ),
                    facts=(
                        ("Pages", page_count),
                        ("PDF size", size_text(len(pdf_data))),
                        ("Word size", size_text(len(docx_data))),
                    )
                )

            except PdfFileError as e:
                st.error(str(e))

            except Exception:
                show_failure("Conversion")

        show_result(source)


# ==========================================
# 2. MERGE PDF
# ==========================================

# ==========================================
# 2. MERGE PDF
# ==========================================

elif selected_tool == "Merge PDF":

    render_tool_header(
        "Merge PDF",
        "Combine multiple PDF files into one document and arrange their order."
    )

    tool_step("Upload two or more PDF files")

    files = st.file_uploader(
        "Select two or more PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key="merge",
        label_visibility="collapsed",
    )

    if files:

        if len(files) < 2:
            st.warning("Please upload at least two PDF files.")

        else:
            tool_step("Arrange the files")

            st.caption(
                "Assign each file a unique order number. "
                "The PDF with order 1 will appear first."
            )

            order_data = [
                {
                    "File name": file.name,
                    "Order": index,
                }
                for index, file in enumerate(files, start=1)
            ]

            edited_order = st.data_editor(
                order_data,
                hide_index=True,
                width="stretch",
                disabled=["File name"],
                column_config={
                    "File name": st.column_config.TextColumn(
                        "File name",
                        width="large",
                    ),
                    "Order": st.column_config.NumberColumn(
                        "Order",
                        min_value=1,
                        max_value=len(files),
                        step=1,
                        required=True,
                    ),
                },
                key="merge_order_editor",
            )

            order_values = [
                row["Order"] for row in edited_order
            ]

            valid_order = (
                all(value is not None for value in order_values)
                and sorted(order_values) == list(range(1, len(files) + 1))
            )

            if not valid_order:
                st.warning(
                    "Please assign each file a unique order number "
                    "from 1 to the number of uploaded files."
                )

            else:
                sorted_rows = sorted(
                    zip(files, edited_order),
                    key=lambda item: item[1]["Order"],
                )

                show_first_pages([file for file, row in sorted_rows])

                source = result_source(files, order_values)

                tool_step("Merge")

                if st.button(
                    "Merge PDF Files",
                    type="primary",
                    disabled=not valid_order,
                    width="stretch",
                ):

                    writer = PdfWriter()

                    try:
                        with st.spinner("Merging PDF files..."):

                            for file, row in sorted_rows:
                                try:
                                    reader = get_pdf_reader(file.getvalue())
                                except PdfFileError as e:
                                    raise PdfFileError(
                                        f"{file.name}: {e}"
                                    ) from e

                                writer.append(reader)

                            page_count = len(writer.pages)
                            output = io.BytesIO()
                            writer.write(output)

                        save_result(
                            source,
                            "PDFs merged successfully!",
                            "Download PDF",
                            output.getvalue(),
                            "Merged_Document.pdf",
                            facts=(
                                ("Files merged", len(files)),
                                ("Pages", page_count),
                                ("Size", size_text(output.getbuffer().nbytes)),
                            ),
                        )

                    except PdfFileError as e:
                        st.error(str(e))

                    except Exception:
                        show_failure("Merge")

                    finally:
                        writer.close()

                show_result(source)


# ==========================================
# 3. SPLIT PDF
# ==========================================

# ==========================================
# 3. SPLIT PDF
# ==========================================

elif selected_tool == "Split PDF":

    render_tool_header(
        "Split PDF",
        "Extract selected pages from a PDF document."
    )

    tool_step("Upload your PDF")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="split",
        label_visibility="collapsed",
    )

    if file:
        try:
            reader = get_pdf_reader(file.getvalue())
            total_pages = len(reader.pages)

            st.caption(
                f"{pages_text(total_pages)}, {size_text(file.size)}"
            )

            tool_step("Choose the pages")

            selection_mode = st.selectbox(
                "Choose pages to extract",
                [
                    "All pages",
                    "First page",
                    "Last page",
                    "Custom page range",
                ],
                key="split_selection_mode",
            )

            if selection_mode == "All pages":
                page_range = f"1-{total_pages}"

            elif selection_mode == "First page":
                page_range = "1"

            elif selection_mode == "Last page":
                page_range = str(total_pages)

            else:
                page_range = st.text_input(
                    "Enter page numbers or ranges",
                    placeholder="Example: 1-5, 8, 10-12",
                    key="split_custom_range",
                )

                st.caption(
                    "Pages stay in their original PDF order, "
                    "so 5,1 gives page 1 and then page 5."
                )

            if page_range:
                try:
                    selected_pages = parse_page_ranges(
                        page_range,
                        total_pages,
                    )

                    st.info(
                        f"{pages_text(len(selected_pages))} selected "
                        f"out of {total_pages}."
                    )

                    show_page_previews(
                        file.getvalue(),
                        [(page_index, 0) for page_index in selected_pages],
                        len(selected_pages),
                    )

                    source = result_source([file], selected_pages)

                    tool_step("Extract")

                    if st.button(
                        "Extract Pages",
                        type="primary",
                        key="extract_pages",
                        width="stretch",
                    ):
                        with st.spinner("Extracting pages..."):
                            writer = PdfWriter()

                            for page_index in selected_pages:
                                writer.add_page(reader.pages[page_index])

                            output = io.BytesIO()
                            writer.write(output)
                            writer.close()

                        save_result(
                            source,
                            f"{pages_text(len(selected_pages))} extracted successfully!",
                            "Download PDF",
                            output.getvalue(),
                            "Extracted_Pages.pdf",
                            facts=(
                                ("Pages", f"{len(selected_pages)} of {total_pages}"),
                                ("Original size", size_text(file.size)),
                                ("New size", size_text(output.getbuffer().nbytes)),
                            ),
                        )

                    show_result(source)

                except ValueError as e:
                    st.warning(f"Check your page selection: {e}")

        except PdfFileError as e:
            st.error(str(e))

        except Exception:
            show_failure("Page extraction")

# ==========================================
# 4. COMPRESS PDF
# ==========================================
elif selected_tool == "Compress PDF":
    render_tool_header(
        "Compress PDF",
        "Reduce PDF file size and compare compression settings."
    )

    tool_step("Upload your PDF")

    uploaded_file = st.file_uploader(
        "Upload a PDF file",
        type=["pdf"],
        key="compress_pdf_upload",
        label_visibility="collapsed"
    )

    if uploaded_file:
        original_data = uploaded_file.getvalue()
        original_size = len(original_data)

        try:
            document = open_pdf_document(original_data)
            total_pages = document.page_count
            document.close()

            st.caption(f"{pages_text(total_pages)}, {size_text(original_size)}")

            show_page_previews(original_data, [(0, 0)])

            tool_step("Choose the settings")

            dpi = st.slider(
                "Image resolution (DPI)",
                min_value=72,
                max_value=200,
                value=120,
                step=10,
                help="Lower DPI usually produces a smaller file."
            )

            quality = st.slider(
                "JPEG image quality",
                min_value=30,
                max_value=90,
                value=55,
                step=5,
                help="Lower quality usually produces a smaller file."
            )

            st.caption(
                "The sliders change how images are compressed. Text stays "
                "selectable, but scanned pages are saved again as pictures."
            )

            source = result_source([uploaded_file], dpi, quality)

            tool_step("Compress")

            if st.button("Compress PDF", type="primary", width="stretch"):
                with st.spinner("Compressing PDF..."):
                    compressed_data = compress_pdf(original_data, dpi, quality)

                compressed_size = len(compressed_data)

                if compressed_size < original_size:
                    reduction = (
                        (original_size - compressed_size) / original_size
                    ) * 100

                    save_result(
                        source,
                        "Your PDF is now smaller.",
                        "Download Compressed PDF",
                        compressed_data,
                        "compressed.pdf",
                        facts=(
                            ("Original size", size_text(original_size)),
                            ("New size", size_text(compressed_size)),
                            ("Size reduction", f"{reduction:.1f}%"),
                        )
                    )

                else:
                    save_result(
                        source,
                        "This PDF is already compact, and these settings can't "
                        "make it smaller. Your original file is fine to use."
                    )

            show_result(source)

        except PdfFileError as e:
            st.error(str(e))

        except Exception:
            show_failure("Compression")
# ==========================================
# 5. IMAGES TO PDF
# ==========================================
elif selected_tool == "Images to PDF":
    render_tool_header(
        "Images to PDF",
        "Arrange images, apply filters, and create a PDF."
    )

    tool_step("Upload your images")

    uploaded_images = st.file_uploader(
        "Upload images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="images_to_pdf_upload",
        label_visibility="collapsed"
    )

    if uploaded_images:
        import pandas as pd

        tool_step("Arrange the pages and choose a filter")

        order_data = [
            {
                "Original order": index + 1,
                "Image": image_file.name,
                "PDF page order": index + 1
            }
            for index, image_file in enumerate(uploaded_images)
        ]

        order_df = pd.DataFrame(order_data)

        edited_df = st.data_editor(
            order_df,
            hide_index=True,
            width="stretch",
            disabled=["Original order", "Image"],
            column_config={
                "PDF page order": st.column_config.NumberColumn(
                    min_value=1,
                    max_value=len(uploaded_images),
                    step=1,
                    required=True
                )
            },
            key="image_pdf_order_editor"
        )

        st.caption(
            "Change the page-order numbers. If two pages have the same number, "
            "their original upload order is preserved."
        )

        filter_mode = st.selectbox(
            "Filter",
            [
                "Original",
                "Magic Color",
                "Document",
                "Grayscale",
                "Black & White"
            ],
            help="The selected filter will be applied to every uploaded page."
        )

        ordered_df = edited_df.copy()
        ordered_df["PDF page order"] = pd.to_numeric(
            ordered_df["PDF page order"],
            errors="coerce"
        )

        if ordered_df["PDF page order"].isna().any():
            st.error("Please enter a valid page order for every image.")
            st.stop()

        ordered_df = ordered_df.sort_values(
            by=["PDF page order", "Original order"]
        )

        ordered_images = []
        unreadable_images = []

        for _, row in ordered_df.iterrows():
            original_index = int(row["Original order"]) - 1
            image_file = uploaded_images[original_index]
            preview = image_preview(image_file.getvalue(), filter_mode)

            if preview is None:
                unreadable_images.append(image_file.name)
            else:
                ordered_images.append((image_file, preview))

        if unreadable_images:
            st.warning(
                "These files can't be read as images and were left out: "
                + ", ".join(unreadable_images)
            )

        if not ordered_images:
            st.error("None of the uploaded files could be read as images.")
            st.stop()

        show_thumbnails(
            [
                (preview, f"{index}. {image_file.name}")
                for index, (image_file, preview)
                in enumerate(ordered_images[:MAX_THUMBNAILS], start=1)
            ],
            len(ordered_images)
        )

        tool_step("Create the PDF")

        source = result_source(
            uploaded_images,
            ordered_df["PDF page order"].tolist(),
            filter_mode
        )

        if st.button("Create PDF", type="primary", width="stretch"):
            try:
                with st.spinner("Creating your PDF..."):
                    pdf_buffer = io.BytesIO()
                    page_images = []

                    for image_file, _ in ordered_images:
                        with Image.open(io.BytesIO(image_file.getvalue())) as source_image:
                            page_images.append(enhance_image(source_image, filter_mode))

                    first_image = page_images[0]
                    remaining_images = page_images[1:]

                    first_image.save(
                        pdf_buffer,
                        format="PDF",
                        save_all=True,
                        append_images=remaining_images,
                        resolution=150
                    )

                save_result(
                    source,
                    "Your PDF is ready.",
                    "Download PDF",
                    pdf_buffer.getvalue(),
                    "scanned_document.pdf",
                    facts=(
                        ("Pages", len(ordered_images)),
                        ("Size", size_text(pdf_buffer.getbuffer().nbytes)),
                    )
                )

            except Exception:
                show_failure("PDF creation")

        show_result(source)
# ==========================================
# 6. ROTATE PDF
# ==========================================

elif selected_tool == "Rotate PDF":

    render_tool_header(
        "Rotate PDF",
        "Rotate all pages or selected pages in a PDF document."
    )

    tool_step("Upload your PDF")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="rotate",
        label_visibility="collapsed"
    )

    if file:

        try:
            reader = get_pdf_reader(file.getvalue())

            total = len(reader.pages)

            st.caption(f"{pages_text(total)}, {size_text(file.size)}")

            tool_step("Choose the angle and pages")

            rotation = st.selectbox(
                "Rotation angle",
                [90, 180, 270]
            )

            page_selection = st.radio(
                "Apply rotation to",
                ["All pages", "Selected pages"]
            )

            selected = list(range(total))

            if page_selection == "Selected pages":

                text = st.text_input(
                    "Page numbers",
                    placeholder="Example: 1-3, 5"
                )

                if text:
                    selected = parse_page_ranges(
                        text,
                        total
                    )
                else:
                    selected = []

            show_page_previews(
                file.getvalue(),
                [(page_index, rotation) for page_index in selected],
                len(selected)
            )

            source = result_source([file], rotation, selected)

            tool_step("Rotate")

            if st.button("Rotate PDF", type="primary", width="stretch"):

                if not selected:
                    st.warning("Select at least one page.")
                else:
                    with st.spinner("Rotating pages..."):
                        writer = PdfWriter()

                        for i, page in enumerate(reader.pages):

                            if i in selected:
                                page.rotate(rotation)

                            writer.add_page(page)

                        output = io.BytesIO()
                        writer.write(output)
                        writer.close()

                    save_result(
                        source,
                        "PDF rotated successfully!",
                        "Download PDF",
                        output.getvalue(),
                        "Rotated_Document.pdf",
                        facts=(
                            ("Pages rotated", f"{len(selected)} of {total}"),
                            ("Angle", f"{rotation}°"),
                            ("Size", size_text(output.getbuffer().nbytes)),
                        )
                    )

            show_result(source)

        except PdfFileError as e:
            st.error(str(e))

        except ValueError as e:
            st.warning(f"Check your page selection: {e}")

        except Exception:
            show_failure("Rotation")


# ==========================================
# 7. BATCH PDF TO WORD
# ==========================================

elif selected_tool == "Batch PDF to Word":

    render_tool_header(
        "Batch PDF to Word",
        "Convert multiple PDF documents into editable Word files."
    )

    tool_step("Upload your PDF files")

    files = st.file_uploader(
        "Select multiple PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key="batch",
        label_visibility="collapsed"
    )

    if files:

        show_first_pages(files)

        source = result_source(files)

        tool_step("Convert")

        if st.button("Convert All Documents", type="primary", width="stretch"):

            zip_buffer = io.BytesIO()
            used_names = set()
            converted = 0
            problems = []

            with zipfile.ZipFile(
                zip_buffer,
                "w",
                zipfile.ZIP_DEFLATED
            ) as zip_file:

                progress = st.progress(0)

                for index, file in enumerate(files):

                    progress.progress(
                        index / len(files),
                        text=f"Converting {index + 1} of {len(files)}: {file.name}"
                    )

                    # One bad file must not lose the others
                    try:
                        docx_data, text_complete, _ = convert_pdf_to_word(
                            file.getvalue()
                        )

                        zip_file.writestr(
                            unique_name(word_file_name(file.name), used_names),
                            docx_data
                        )

                        converted += 1

                        if not text_complete:
                            problems.append(
                                f"{file.name}: some text may be missing from "
                                "the Word file. Please compare it with your PDF."
                            )

                    except PdfFileError as e:
                        problems.append(f"{file.name} was skipped. {e}")

                    except Exception:
                        logger.exception("Batch conversion failed")
                        problems.append(
                            f"{file.name} was skipped. It could not be converted."
                        )

                progress.empty()

            if converted:
                save_result(
                    source,
                    f"Converted {converted} of {len(files)} documents.",
                    "Download All Word Files (ZIP)",
                    zip_buffer.getvalue(),
                    "Batch_Word_Conversion.zip",
                    "application/zip",
                    warnings=problems,
                    facts=(
                        ("Converted", f"{converted} of {len(files)}"),
                        ("ZIP size", size_text(zip_buffer.getbuffer().nbytes)),
                    )
                )

            else:
                st.error("None of the documents could be converted.")

                for problem in problems:
                    st.warning(problem)

        show_result(source)


# ==========================================
# 8. PDF INFORMATION
# ==========================================

elif selected_tool == "PDF Information":

    render_tool_header(
        "PDF Information",
        "Inspect page count, file size, encryption status, and metadata."
    )

    tool_step("Upload your PDF")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="info",
        label_visibility="collapsed"
    )

    if file:

        try:
            reader = get_pdf_reader(file.getvalue())

            tool_step("Read the details")

            col1, col2, col3 = st.columns(3)

            col1.metric("Total Pages", len(reader.pages))

            col2.metric("File Size", size_text(file.size))

            col3.metric(
                "Encrypted",
                "Yes" if reader.is_encrypted else "No"
            )

            show_page_previews(file.getvalue(), [(0, 0)])

            metadata = reader.metadata

            if metadata:
                details = {
                    "Title": metadata.title,
                    "Author": metadata.author,
                    "Subject": metadata.subject,
                    "Creator": metadata.creator,
                    "Producer": metadata.producer,
                    "Creation Date": creation_date_text(metadata),
                }

                st.dataframe(
                    [
                        {"Detail": name, "Value": value or "Not available"}
                        for name, value in details.items()
                    ],
                    hide_index=True,
                    width="stretch"
                )

            else:
                st.info("No metadata available.")

        except PasswordProtectedError:
            tool_step("Read the details")

            col1, col2, col3 = st.columns(3)

            col1.metric("Total Pages", "Locked")

            col2.metric("File Size", size_text(file.size))

            col3.metric("Encrypted", "Yes")

            st.info(
                "This PDF needs a password, so its pages and details "
                "can't be read."
            )

        except PdfFileError as e:
            st.error(str(e))

        except Exception:
            show_failure("Reading this PDF")



# ==========================================
# 9. REVERSE PDF
# ==========================================

elif selected_tool == "Reverse PDF":
    render_tool_header(
        "Reverse PDF",
        "Reverse the page order so the last page becomes the first."
    )
    tool_step("Upload your PDF")

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="reverse_pdf_upload",
        label_visibility="collapsed"
    )

    if uploaded_file:
        try:
            reader = get_pdf_reader(uploaded_file.getvalue())
            total_pages = len(reader.pages)

            st.caption(
                f"{pages_text(total_pages)}, {size_text(uploaded_file.size)}"
            )

            show_page_previews(
                uploaded_file.getvalue(),
                [(index, 0) for index in reversed(range(total_pages))],
                total_pages
            )

            source = result_source([uploaded_file])

            tool_step("Reverse")

            if st.button("Reverse PDF", type="primary", width="stretch"):
                with st.spinner("Reversing pages..."):
                    writer = PdfWriter()

                    for page in reversed(reader.pages):
                        writer.add_page(page)

                    output_buffer = io.BytesIO()
                    writer.write(output_buffer)
                    writer.close()

                save_result(
                    source,
                    "PDF page order reversed successfully.",
                    "Download Reversed PDF",
                    output_buffer.getvalue(),
                    "reversed.pdf",
                    facts=(
                        ("Pages", total_pages),
                        ("Size", size_text(output_buffer.getbuffer().nbytes)),
                    )
                )

            show_result(source)

        except PdfFileError as e:
            st.error(str(e))

        except Exception:
            show_failure("Reversing this PDF")
# ==========================================
# WORD TO PDF
# ==========================================

elif selected_tool == "Word to PDF":
    render_tool_header(
        "Word to PDF",
        "Turn a Word document into a PDF."
    )

    tool_step("Upload your Word document")

    file = st.file_uploader(
        "Upload Word document",
        type=["docx", "doc"],
        key="word_to_pdf_upload",
        label_visibility="collapsed"
    )

    if file:
        with tool_errors("Conversion"):
            st.caption(size_text(file.size))

            source = result_source([file])

            if file.size > MAX_WORD_MEGABYTES * 1024 * 1024:
                st.warning(
                    f"Please use a document of {MAX_WORD_MEGABYTES} MB or smaller."
                )

            elif not find_libreoffice():
                st.error("Word to PDF isn't available at the moment.")

            else:
                tool_step("Convert")

                st.caption(
                    "The layout can shift slightly if your document uses "
                    "fonts this service doesn't have."
                )

                if st.button("Convert to PDF", type="primary", width="stretch"):
                    data = file.getvalue()

                    with st.spinner("Converting to PDF. This can take a minute..."):
                        output = convert_word_to_pdf(data)

                    save_result(
                        source,
                        "Your PDF is ready.",
                        "Download PDF",
                        output,
                        f"{file_stem(file.name)}.pdf",
                        facts=(
                            ("Pages", pdf_page_count(output)),
                            ("Word size", size_text(file.size)),
                            ("PDF size", size_text(len(output))),
                        )
                    )

                show_result(source)

                result = st.session_state.get("tool_result")

                if result and result["source"] == source and result["data"]:
                    show_page_previews(result["data"], [(0, 0)])


# ==========================================
# 10. DELETE PAGES
# ==========================================

elif selected_tool == "Delete Pages":
    render_tool_header(
        "Delete Pages",
        "Remove the pages you don't want from a PDF."
    )

    tool_step("Upload your PDF")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="delete_pages_upload",
        label_visibility="collapsed"
    )

    if file:
        with tool_errors("Deleting pages"):
            data = file.getvalue()
            total_pages = pdf_page_count(data)

            st.caption(f"{pages_text(total_pages)}, {size_text(file.size)}")

            tool_step("Choose the pages to delete")

            page_text = st.text_input(
                "Pages to delete",
                placeholder="Example: 2, 5-7",
                key="delete_pages_text",
            )

            if page_text:
                removed = set(parse_page_ranges(page_text, total_pages))
                kept = [
                    page_index
                    for page_index in range(total_pages)
                    if page_index not in removed
                ]

                if not kept:
                    st.warning(
                        "That would delete every page. "
                        "A PDF needs at least one page."
                    )

                else:
                    st.caption("These pages will remain:")

                    show_page_previews(
                        data,
                        [(page_index, 0) for page_index in kept],
                        len(kept)
                    )

                    source = result_source([file], kept)

                    tool_step("Delete")

                    if st.button("Delete Pages", type="primary", width="stretch"):
                        with st.spinner("Deleting pages..."):
                            output = select_pages(data, kept)

                        save_result(
                            source,
                            f"{pages_text(len(removed))} deleted.",
                            "Download PDF",
                            output,
                            f"{file_stem(file.name)}_edited.pdf",
                            facts=(
                                ("Pages left", f"{len(kept)} of {total_pages}"),
                                ("Original size", size_text(file.size)),
                                ("New size", size_text(len(output))),
                            )
                        )

                    show_result(source)


# ==========================================
# 11. REORDER PAGES
# ==========================================

elif selected_tool == "Reorder Pages":
    render_tool_header(
        "Reorder Pages",
        "Drag the pages of a PDF into the order you want."
    )

    tool_step("Upload your PDF")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="reorder_pages_upload",
        label_visibility="collapsed"
    )

    if file:
        with tool_errors("Reordering pages"):
            data = file.getvalue()
            total_pages = pdf_page_count(data)
            original_order = list(range(total_pages))

            st.caption(f"{pages_text(total_pages)}, {size_text(file.size)}")

            tool_step("Arrange the pages")

            page_order = original_order

            if total_pages <= MAX_DRAG_PAGES:
                st.caption("Drag a page to move it, or use its arrow buttons.")
                page_order = drag_page_order(file, data, total_pages)
                order_label = "Or type the new order"

            else:
                st.caption(
                    f"This PDF has more than {MAX_DRAG_PAGES} pages, "
                    "so please type the new order."
                )
                order_label = "New page order"

            typed_order = st.text_input(
                order_label,
                placeholder="Example: 3, 1, 2",
                help="Pages you leave out follow in their old order.",
                key="reorder_pages_text",
            )

            if typed_order:
                page_order = parse_page_order(typed_order, total_pages)

                show_page_previews(
                    data,
                    [(page_index, 0) for page_index in page_order],
                    total_pages
                )

            if page_order != original_order and total_pages <= MAX_DRAG_PAGES:
                st.caption(
                    "New order: "
                    + ", ".join(str(page_index + 1) for page_index in page_order)
                )

            source = result_source([file], page_order)

            tool_step("Reorder")

            if st.button(
                "Reorder Pages",
                type="primary",
                width="stretch",
                disabled=page_order == original_order,
            ):
                with st.spinner("Reordering pages..."):
                    output = select_pages(data, page_order)

                save_result(
                    source,
                    "Your pages are in their new order.",
                    "Download PDF",
                    output,
                    f"{file_stem(file.name)}_reordered.pdf",
                    facts=(
                        ("Pages", total_pages),
                        ("Size", size_text(len(output))),
                    )
                )

            show_result(source)


# ==========================================
# 12. ADD PAGE NUMBERS
# ==========================================

elif selected_tool == "Add Page Numbers":
    render_tool_header(
        "Add Page Numbers",
        "Number every page of a PDF."
    )

    tool_step("Upload your PDF")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="page_numbers_upload",
        label_visibility="collapsed"
    )

    if file:
        with tool_errors("Adding page numbers"):
            data = file.getvalue()
            total_pages = pdf_page_count(data)

            st.caption(f"{pages_text(total_pages)}, {size_text(file.size)}")

            tool_step("Choose the style")

            position = st.selectbox("Position", NUMBER_POSITIONS)
            number_style = st.selectbox("Style", NUMBER_STYLES)
            first_number = st.number_input(
                "First number",
                min_value=1,
                max_value=100000,
                value=1,
                step=1,
            )

            show_page_previews(
                add_page_numbers(data, position, number_style, first_number, preview=True),
                [(0, 0)]
            )

            source = result_source([file], position, number_style, first_number)

            tool_step("Add the numbers")

            if st.button("Add Page Numbers", type="primary", width="stretch"):
                with st.spinner("Adding page numbers..."):
                    output = add_page_numbers(data, position, number_style, first_number)

                save_result(
                    source,
                    "Page numbers added.",
                    "Download PDF",
                    output,
                    f"{file_stem(file.name)}_numbered.pdf",
                    facts=(
                        ("Pages numbered", total_pages),
                        ("Size", size_text(len(output))),
                    )
                )

            show_result(source)


# ==========================================
# 13. ADD WATERMARK
# ==========================================

elif selected_tool == "Add Watermark":
    render_tool_header(
        "Add Watermark",
        "Stamp text such as DRAFT across every page."
    )

    tool_step("Upload your PDF")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="watermark_upload",
        label_visibility="collapsed"
    )

    if file:
        with tool_errors("Adding the watermark"):
            data = file.getvalue()
            total_pages = pdf_page_count(data)

            st.caption(f"{pages_text(total_pages)}, {size_text(file.size)}")

            tool_step("Choose the watermark")

            watermark_text = st.text_input(
                "Watermark text",
                value="CONFIDENTIAL",
                max_chars=60,
            ).strip()

            color_name = st.selectbox("Color", list(WATERMARK_COLORS))
            size_name = st.selectbox("Size", list(WATERMARK_SIZES), index=1)
            layout = st.radio("Direction", ["Diagonal", "Horizontal"], horizontal=True)
            opacity = st.slider("Strength", 10, 80, 25, 5, format="%d%%")

            # The built-in font only covers Western letters
            text_is_usable = watermark_text and all(
                ord(character) < 256 for character in watermark_text
            )

            if not watermark_text:
                st.warning("Please enter the watermark text.")

            elif not text_is_usable:
                st.warning(
                    "Watermarks can only use English and Western European "
                    "letters for now. Please change the text."
                )

            else:
                settings = (
                    watermark_text,
                    WATERMARK_COLORS[color_name],
                    WATERMARK_SIZES[size_name],
                    opacity / 100,
                    layout == "Diagonal",
                )

                show_page_previews(
                    add_watermark(data, *settings, preview=True),
                    [(0, 0)]
                )

                source = result_source([file], settings)

                tool_step("Add the watermark")

                if st.button("Add Watermark", type="primary", width="stretch"):
                    with st.spinner("Adding the watermark..."):
                        output = add_watermark(data, *settings)

                    save_result(
                        source,
                        "Watermark added.",
                        "Download PDF",
                        output,
                        f"{file_stem(file.name)}_watermarked.pdf",
                        facts=(
                            ("Pages stamped", total_pages),
                            ("Size", size_text(len(output))),
                        )
                    )

                show_result(source)


# ==========================================
# 14. PDF TO IMAGES
# ==========================================

elif selected_tool == "PDF to Images":
    render_tool_header(
        "PDF to Images",
        "Save the pages of a PDF as PNG or JPG pictures."
    )

    tool_step("Upload your PDF")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="pdf_to_images_upload",
        label_visibility="collapsed"
    )

    if file:
        with tool_errors("Creating the images"):
            data = file.getvalue()
            total_pages = pdf_page_count(data)

            st.caption(f"{pages_text(total_pages)}, {size_text(file.size)}")

            tool_step("Choose the pages and quality")

            selected_pages = choose_pages(total_pages, "pdf_to_images")
            image_format = st.radio("Format", ["PNG", "JPG"], horizontal=True)
            quality_name = st.selectbox(
                "Quality",
                ["Standard (150 DPI)", "High (300 DPI)", "Screen (72 DPI)"],
            )
            dpi = int(re.search(r"\d+", quality_name).group())

            if len(selected_pages) > MAX_IMAGE_PAGES:
                st.warning(
                    f"Please choose {MAX_IMAGE_PAGES} pages or fewer at a time."
                )

            elif selected_pages:
                show_page_previews(
                    data,
                    [(page_index, 0) for page_index in selected_pages],
                    len(selected_pages)
                )

                source = result_source([file], selected_pages, image_format, dpi)

                tool_step("Create the images")

                if st.button("Create Images", type="primary", width="stretch"):
                    with st.spinner("Creating the images..."):
                        images = pdf_to_images(
                            data,
                            selected_pages,
                            dpi,
                            image_format,
                            file_stem(file.name)
                        )

                        # One picture downloads directly, several go in a ZIP
                        if len(images) == 1:
                            output_name, output = images[0]
                            mime = "image/png" if image_format == "PNG" else "image/jpeg"
                            label = "Download Image"

                        else:
                            buffer = io.BytesIO()

                            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as archive:
                                for image_name, image_data in images:
                                    archive.writestr(image_name, image_data)

                            output = buffer.getvalue()
                            output_name = f"{file_stem(file.name)}_images.zip"
                            mime = "application/zip"
                            label = "Download All Images (ZIP)"

                    save_result(
                        source,
                        f"{len(images)} image{'' if len(images) == 1 else 's'} ready.",
                        label,
                        output,
                        output_name,
                        mime,
                        facts=(
                            ("Images", len(images)),
                            ("Format", image_format),
                            ("Size", size_text(len(output))),
                        )
                    )

                show_result(source)


# ==========================================
# 15. EXTRACT TEXT
# ==========================================

elif selected_tool == "Extract Text":
    render_tool_header(
        "Extract Text",
        "Pull the text out of a PDF into a text file."
    )

    tool_step("Upload your PDF")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="extract_text_upload",
        label_visibility="collapsed"
    )

    if file:
        with tool_errors("Extracting the text"):
            data = file.getvalue()
            total_pages = pdf_page_count(data)

            st.caption(f"{pages_text(total_pages)}, {size_text(file.size)}")

            tool_step("Choose the pages")

            selected_pages = choose_pages(total_pages, "extract_text")

            if selected_pages:
                source = result_source([file], selected_pages)

                tool_step("Extract")

                if st.button("Extract Text", type="primary", width="stretch"):
                    with st.spinner("Extracting the text..."):
                        text = extract_pdf_text(data, selected_pages)

                    # Every page has a "Page n" heading, so count only what's under them
                    page_text = re.sub(r"--- Page \d+ ---", "", text)
                    letters = count_letters(page_text)

                    if letters == 0:
                        save_result(
                            source,
                            "No text was found on these pages, so this is probably "
                            "a scan. Try the OCR Scanned PDF tool first."
                        )

                    else:
                        output = text.encode("utf-8")

                        save_result(
                            source,
                            "Your text is ready.",
                            "Download Text File",
                            output,
                            f"{file_stem(file.name)}.txt",
                            "text/plain",
                            facts=(
                                ("Pages", len(selected_pages)),
                                ("Letters and digits", f"{letters:,}"),
                                ("Size", size_text(len(output))),
                            ),
                            text_preview=text[:3000]
                        )

                show_result(source)


# ==========================================
# 16. PROTECT PDF
# ==========================================

elif selected_tool == "Protect PDF":
    render_tool_header(
        "Protect PDF",
        "Lock a PDF so it needs a password to open."
    )

    tool_step("Upload your PDF")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="protect_upload",
        label_visibility="collapsed"
    )

    if file:
        with tool_errors("Protecting the PDF"):
            data = file.getvalue()
            total_pages = pdf_page_count(data)

            st.caption(f"{pages_text(total_pages)}, {size_text(file.size)}")

            tool_step("Choose a password")

            password = st.text_input(
                "Password",
                type="password",
                autocomplete="new-password",
                key="protect_password",
            )

            confirm_password = st.text_input(
                "Type the password again",
                type="password",
                autocomplete="new-password",
                key="protect_confirm",
            )

            st.caption(
                "Keep your password safe. If you forget it, nobody can "
                "open the file, and this site can't recover it."
            )

            if password and confirm_password:
                if password != confirm_password:
                    st.warning("The two passwords don't match.")

                elif len(password) < 4:
                    st.warning("Please use a password of at least 4 characters.")

                else:
                    source = result_source([file], password_fingerprint(password))

                    tool_step("Protect")

                    if st.button("Protect PDF", type="primary", width="stretch"):
                        with st.spinner("Protecting your PDF..."):
                            output = protect_pdf(data, password)

                        save_result(
                            source,
                            "Your PDF is now password-protected.",
                            "Download Protected PDF",
                            output,
                            f"{file_stem(file.name)}_protected.pdf",
                            facts=(
                                ("Pages", total_pages),
                                ("Encryption", "AES-256"),
                                ("Size", size_text(len(output))),
                            )
                        )

                    show_result(source)


# ==========================================
# 17. UNLOCK PDF
# ==========================================

elif selected_tool == "Unlock PDF":
    render_tool_header(
        "Unlock PDF",
        "Remove the password from a PDF, if you know the password."
    )

    tool_step("Upload your PDF")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="unlock_upload",
        label_visibility="collapsed"
    )

    if file:
        with tool_errors("Unlocking the PDF"):
            data = file.getvalue()
            lock_state = pdf_lock_state(data)

            if lock_state == "none":
                st.info("This PDF isn't protected, so there is nothing to unlock.")

            else:
                tool_step("Enter the password")

                if lock_state == "restricted":
                    st.caption(
                        "This PDF opens freely but limits printing or editing. "
                        "Enter its owner password to remove those limits."
                    )

                password = st.text_input(
                    "Password",
                    type="password",
                    autocomplete="off",
                    key="unlock_password",
                )

                if password:
                    source = result_source([file], password_fingerprint(password))

                    tool_step("Unlock")

                    if st.button("Unlock PDF", type="primary", width="stretch"):
                        with st.spinner("Unlocking your PDF..."):
                            output = unlock_pdf(data, password)

                        save_result(
                            source,
                            "Your PDF is unlocked.",
                            "Download Unlocked PDF",
                            output,
                            f"{file_stem(file.name)}_unlocked.pdf",
                            facts=(
                                ("Pages", pdf_page_count(output)),
                                ("Size", size_text(len(output))),
                            )
                        )

                    show_result(source)


# ==========================================
# 18. OCR SCANNED PDF
# ==========================================

elif selected_tool == "OCR Scanned PDF":
    render_tool_header(
        "OCR Scanned PDF",
        "Read the words in scanned pages, so they can be searched and copied."
    )

    tool_step("Upload your PDF")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="ocr_upload",
        label_visibility="collapsed"
    )

    if file:
        with tool_errors("OCR"):
            data = file.getvalue()
            total_pages = pdf_page_count(data)

            st.caption(f"{pages_text(total_pages)}, {size_text(file.size)}")

            show_page_previews(data, [(0, 0)])

            tool_step("Choose the language")

            language_name = st.selectbox("Document language", list(OCR_LANGUAGES))
            language = OCR_LANGUAGES[language_name]

            st.caption(
                "OCR reads each page as a picture, so it can take a while "
                "and may misread some words. Please check anything important."
            )

            if total_pages > MAX_OCR_PAGES:
                st.warning(
                    f"Please use a PDF of {MAX_OCR_PAGES} pages or fewer. "
                    "The Split PDF tool can divide a longer one."
                )

            elif not ocr_is_available(language):
                st.error("OCR isn't available for this language at the moment.")

            else:
                source = result_source([file], language)

                tool_step("Read the pages")

                if st.button("Run OCR", type="primary", width="stretch"):
                    progress = st.progress(0)

                    def show_ocr_progress(index, count):
                        progress.progress(
                            index / count,
                            text=f"Reading page {index + 1} of {count}"
                        )

                    output, pages_read = ocr_pdf(data, language, show_ocr_progress)
                    progress.empty()

                    if pages_read == 0:
                        save_result(
                            source,
                            "Every page already has selectable text, "
                            "so this PDF doesn't need OCR."
                        )

                    else:
                        text = extract_pdf_text(output, list(range(total_pages)))

                        save_result(
                            source,
                            "Your PDF can now be searched and copied.",
                            "Download Searchable PDF",
                            output,
                            f"{file_stem(file.name)}_searchable.pdf",
                            warnings=() if count_letters(
                                re.sub(r"--- Page \d+ ---", "", text)
                            ) else (
                                "No words could be read. The scan may be too "
                                "faint, or in a different language.",
                            ),
                            facts=(
                                ("Pages read", f"{pages_read} of {total_pages}"),
                                ("Size", size_text(len(output))),
                            ),
                            text_preview=text[:3000]
                        )

                show_result(source)


# ==========================================
# FOOTER
# ==========================================

st.markdown(
    '<div class="site-footer">'
    "<strong>Your files:</strong> they're used only to do what you ask, and this "
    "app doesn't save them permanently. They are processed on a public cloud "
    "service, so please avoid uploading highly confidential documents."
    f"<br>{APP_NAME} {APP_VERSION}"
    "</div>",
    unsafe_allow_html=True,
)

# Repeated here because the sidebar is hidden on phones
with st.container(horizontal=True, key="footer_links"):
    for page in INFO_PAGES:
        st.button(
            page,
            key=f"footer_{page.lower()}",
            type="tertiary",
            on_click=open_page,
            args=(page,),
        )

    if GITHUB_REPO:
        st.link_button(
            "Send feedback",
            f"https://github.com/{GITHUB_REPO}/issues/new",
            type="tertiary",
        )
