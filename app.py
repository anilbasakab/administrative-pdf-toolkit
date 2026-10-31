
import streamlit as st
from pdf2docx import Converter
from pypdf import PdfReader, PdfWriter
from PIL import Image
import tempfile
import os
import io
import zipfile
import re

# ==========================================
# APPLICATION CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Administrative PDF Toolkit 2.0",
    page_icon="📁",
    layout="wide",
)

# Custom styling
# ==========================================
# PROFESSIONAL APPLICATION STYLING
# ==========================================

st.markdown(
    """
    <style>
    :root {
        --primary-color: #1D4ED8;
    }

    .stApp {
        background-color: #F8FAFC;
    }

    [data-testid="stHeader"] {
        background: rgba(248, 250, 252, 0.9);
    }

    .main .block-container {
        max-width: 1320px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #0F172A;
        letter-spacing: -0.02em;
    }

    [data-testid="stSidebar"] {
        background-color: #F1F5F9;
        border-right: 1px solid #E2E8F0;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #0F172A;
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .st-key-global_home_button button {
    background-color: #16A34A;
    border: 1px solid #16A34A;
    color: white;
}

.st-key-global_home_button button:hover {
    background-color: #15803D;
    border-color: #15803D;
    color: white;
}

    .stButton > button[kind="primary"]:hover {
        background-color: #1E40AF;
        border-color: #1E40AF;
    }

    .stDownloadButton > button {
        width: 100%;
    }

    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #E2E8F0;
        padding: 16px;
        border-radius: 12px;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px;
        border-color: #E2E8F0;
        background-color: white;
    }

    [data-testid="stFileUploader"] {
        border-radius: 12px;
    }

    hr {
        border-color: #E2E8F0;
    }

    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# ==========================================

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================

tools = [
    "PDF to Word",
    "Merge PDF",
    "Split PDF",
    "Compress PDF",
    "Images to PDF",
    "Rotate PDF",
    "Batch PDF to Word",
    "PDF Information",
    "Reverse PDF"
]

TOOLS = [
    "PDF to Word",
    "Merge PDF",
    "Split PDF",
    "Compress PDF",
    "Images to PDF",
    "Rotate PDF",
    "Batch PDF to Word",
    "PDF Information",
    "Reverse PDF"
]

NAVIGATION = ["Home"] + TOOLS

if "pending_tool" in st.session_state:
    st.session_state["nav_choice"] = (
        st.session_state.pop("pending_tool")
    )

if "nav_choice" not in st.session_state:
    st.session_state["nav_choice"] = "Home"

if st.session_state["nav_choice"] not in NAVIGATION:
    st.session_state["nav_choice"] = "Home"

selected_tool = st.sidebar.selectbox(
    "SELECT A TOOL",
    NAVIGATION,
    key="nav_choice",
)
# Main header with Home button
title_column, home_column = st.columns([8, 1])

with title_column:
    st.markdown(
        """
        <div style="
            font-size: 46px;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -1px;
            padding: 0 0 14px 0;
            border-bottom: 1px solid #E2E8F0;
            margin-bottom: 24px;
            width: 100%;
        ">
            📁 Administrative PDF Toolkit
        </div>
        """,
        unsafe_allow_html=True,
    )


with home_column:
    if selected_tool != "Home":
        st.button(
            "🏠 Home",
            key="global_home_button",
            type="primary",
            use_container_width=True,
            on_click=lambda: st.session_state.update({"nav_choice": "Home"}),
        )

st.sidebar.divider()

st.sidebar.markdown("### 📁 PDF Toolkit")
st.sidebar.caption("Administrative Document Utilities")

st.sidebar.markdown(
    """
    <div style="
        margin-top: 20px;
        padding: 12px;
        border-radius: 10px;
        background: #E2E8F0;
        color: #334155;
        font-size: 12px;
    ">
        <strong>Version 2.0</strong><br>
        Built with Python and Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_pdf_reader(data):
    reader = PdfReader(io.BytesIO(data))

    if reader.is_encrypted:
        raise ValueError(
            "Password-protected PDFs are not supported."
        )

    if len(reader.pages) == 0:
        raise ValueError("The PDF contains no pages.")

    return reader


def parse_page_ranges(text, total_pages):
    """Accept ranges such as 1-3,5,7-9."""
    pages = set()

    for part in text.split(","):
        part = part.strip()

        if not part:
            continue

        if "-" in part:
            start, end = part.split("-", 1)

            if not start.strip().isdigit() or not end.strip().isdigit():
                raise ValueError("Invalid page range.")

            first = int(start)
            last = int(end)

            if first > last:
                raise ValueError("Range start must not exceed end.")

            selected = range(first, last + 1)

        else:
            if not part.isdigit():
                raise ValueError("Invalid page number.")

            selected = [int(part)]

        for page in selected:
            if page < 1 or page > total_pages:
                raise ValueError(
                    f"Page {page} is outside the PDF."
                )

            pages.add(page - 1)

    if not pages:
        raise ValueError("Please enter valid page numbers.")

    return sorted(pages)


def pdf_download(data, filename):
    st.download_button(
        "⬇️ Download PDF",
        data=data,
        file_name=filename,
        mime="application/pdf",
        use_container_width=True
    )
def render_tool_header(title, description):
    st.markdown(
        f"""
        <div style="
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid #E2E8F0;
        ">
            <h1 style="
                font-size: 28px;
                font-weight: 750;
                color: #0F172A;
                margin-bottom: 6px;
            ">{title}</h1>
            <p style="
                font-size: 15px;
                color: #64748B;
                margin: 0;
            ">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
def render_home():
    # Welcome banner
    with st.container(border=True):
        st.markdown(
            """
            <div style="color:#0F172A;">
                <h2 style="color:#1D4ED8; font-size:24px; margin-bottom:12px;">
    Your documents. Simplified.
</h2>
                <p style="color:#475569; font-size:16px; margin:0;">
                    Convert, organize, compress and manage PDF files
                    using one convenient toolkit.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.write("")

    # Tool descriptions
    descriptions = {
        "PDF to Word": "Convert PDF documents into editable Word files.",
        "Merge PDF": "Combine multiple PDFs into one document.",
        "Split PDF": "Extract selected pages from PDF documents.",
        "Compress PDF": "Attempt to reduce PDF file size.",
        "Images to PDF": "Convert JPG and PNG images into one PDF.",
        "Rotate PDF": "Rotate all pages or selected PDF pages.",
        "Batch PDF to Word": "Convert multiple PDFs into Word files.",
        "PDF Information": "View page count, file size and metadata.",
        "Reverse PDF": "Reverse the order of pages in a PDF.",
    }

    icons = {
        "PDF to Word": "📄",
        "Merge PDF": "📚",
        "Split PDF": "✂️",
        "Compress PDF": "📦",
        "Images to PDF": "🖼️",
        "Rotate PDF": "🔄",
        "Batch PDF to Word": "📑",
        "PDF Information": "🔍",
        "Reverse PDF": "🔃",
    }

    st.subheader("All document utilities")

    search_query = st.text_input(
        "Search tools",
        placeholder="Try: merge, rotate, Word, images...",
        key="home_tool_search",
    ).strip().lower()

    filtered_tools = [
        tool
        for tool in TOOLS
        if search_query in tool.lower()
        or search_query in descriptions[tool].lower()
    ]

    if not filtered_tools:
        st.info("No tools match your search. Try another keyword.")

    # Display three tool cards per row
    for row_start in range(0, len(filtered_tools), 3):
        columns = st.columns(3)

        for column, tool in zip(
            columns,
            filtered_tools[row_start:row_start + 3],
        ):
            with column:
                with st.container(border=True):
                    st.markdown(
                        f"""
                        <div style="
    color:#0F172A;
    min-height:115px;
    display:flex;
    flex-direction:column;
">
                            <h3 style="
                                color:#0F172A;
                                font-size:20px;
                                margin:0 0 12px 0;
                            ">{icons[tool]} {tool}</h3>
                            <p style="
    color:#475569;
    font-size:14px;
    line-height:1.5;
    margin:0;
    min-height:42px;
">{descriptions[tool]}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        f"Open {tool} →",
                        key=f"open_{tool}",
                        use_container_width=True,
                    ):
                        st.session_state["pending_tool"] = tool
                        st.rerun()

    st.divider()
    st.subheader("How it works")

    step1, step2, step3, step4 = st.columns(4)

    step1.markdown("**1. Upload**")
    step1.caption("Choose your PDF or image files.")

    step2.markdown("**2. Configure**")
    step2.caption("Set page ranges or other options.")

    step3.markdown("**3. Process**")
    step3.caption("Run the selected document utility.")

    step4.markdown("**4. Download**")
    step4.caption("Save the generated file.")
# ==========================================
# 1. PDF TO WORD
# ==========================================


if selected_tool == "Home":
    render_home()


elif selected_tool == "PDF to Word":
    render_tool_header(
        "📄 PDF to Word",
        "Convert PDF documents into editable Word files."
    )

    uploaded = st.file_uploader(
        "Upload your PDF",
        type=["pdf"],
        key="single_word"
    )

    if uploaded:
        st.info(f"Selected: {uploaded.name}")

        if st.button("Convert to Word", type="primary"):
            if uploaded is None:
                st.warning("Please upload a PDF file first.")
            else:
                with st.status("Converting PDF to Word...", expanded=True) as status:
                    pdf_path = None
                    docx_path = None
                    converter = None

                    try:
                        # Save uploaded PDF to a temporary file
                        with tempfile.NamedTemporaryFile(
                                delete=False, suffix=".pdf"
                        ) as pdf_file:
                            pdf_file.write(uploaded.getvalue())
                            pdf_path = pdf_file.name

                        # Create temporary DOCX output path
                        with tempfile.NamedTemporaryFile(
                                delete=False, suffix=".docx"
                        ) as docx_file:
                            docx_path = docx_file.name

                        # Convert PDF to Word
                        converter = Converter(pdf_path)
                        converter.convert(docx_path, start=0, end=None)
                        converter.close()
                        converter = None

                        # Read converted DOCX into memory
                        with open(docx_path, "rb") as docx_file:
                            docx_data = docx_file.read()

                        status.update(
                            label="Conversion completed successfully!",
                            state="complete"
                        )

                    except Exception as e:
                        status.update(
                            label="Conversion failed.",
                            state="error"
                        )
                        st.error(f"Conversion failed: {e}")
                        docx_data = None

                    finally:
                        if converter is not None:
                            try:
                                converter.close()
                            except Exception:
                                pass

                        for temp_path in (pdf_path, docx_path):
                            if temp_path and os.path.exists(temp_path):
                                try:
                                    os.remove(temp_path)
                                except Exception:
                                    pass

                # Display download button only after successful conversion
                if docx_data:
                    st.download_button(
                        label="⬇️ Download Word Document",
                        data=docx_data,
                        file_name=uploaded.name.rsplit(".", 1)[0] + ".docx",
                        mime=(
                            "application/vnd.openxmlformats-officedocument."
                            "wordprocessingml.document"
                        ),
                        type="primary"
                    )

                if converter is not None:
                    converter.close()

                for path in (pdf_path, docx_path):
                    if path and os.path.exists(path):
                        os.remove(path)


# ==========================================
# 2. MERGE PDF
# ==========================================

# ==========================================
# 2. MERGE PDF
# ==========================================

elif selected_tool == "Merge PDF":

    render_tool_header(
        "📚 Merge PDF",
        "Combine multiple PDF files into one document and arrange their order."
    )

    files = st.file_uploader(
        "Select two or more PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key="merge",
    )

    if files:

        if len(files) < 2:
            st.warning("Please upload at least two PDF files.")

        else:
            st.subheader("Arrange files")

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
                use_container_width=True,
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

                st.subheader("Merge preview")

                for position, (file, row) in enumerate(sorted_rows, start=1):
                    st.write(f"{position}. {file.name}")

                if st.button(
                    "Merge PDF Files",
                    type="primary",
                    disabled=not valid_order,
                ):

                    writer = PdfWriter()

                    try:
                        with st.spinner("Merging PDF files..."):

                            for file, row in sorted_rows:
                                writer.append(
                                    io.BytesIO(file.getvalue())
                                )

                            output = io.BytesIO()
                            writer.write(output)
                            writer.close()

                        st.success("PDFs merged successfully!")

                        pdf_download(
                            output.getvalue(),
                            "Merged_Document.pdf",
                        )

                    except Exception as e:
                        writer.close()
                        st.error(f"Merge failed: {e}")


# ==========================================
# 3. SPLIT PDF
# ==========================================

# ==========================================
# 3. SPLIT PDF
# ==========================================

elif selected_tool == "Split PDF":

    render_tool_header(
        "✂️ Split PDF",
        "Extract selected pages from a PDF document."
    )

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="split",
    )

    if file:
        try:
            reader = get_pdf_reader(file.getvalue())
            total_pages = len(reader.pages)

            st.metric("Total pages", total_pages)

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

            if page_range:
                try:
                    selected_pages = parse_page_ranges(
                        page_range,
                        total_pages,
                    )

                    st.info(
                        f"{len(selected_pages)} page(s) selected "
                        f"out of {total_pages}."
                    )

                    if st.button(
                        "Extract Pages",
                        type="primary",
                        key="extract_pages",
                    ):
                        writer = PdfWriter()

                        for page_index in selected_pages:
                            writer.add_page(reader.pages[page_index])

                        output = io.BytesIO()
                        writer.write(output)
                        writer.close()

                        st.success(
                            f"{len(selected_pages)} pages extracted successfully!"
                        )

                        pdf_download(
                            output.getvalue(),
                            "Extracted_Pages.pdf",
                        )

                except ValueError as e:
                    st.warning(f"Check your page selection: {e}")

        except Exception as e:
            st.error(f"Unable to read PDF: {e}")

# ==========================================
# 4. COMPRESS PDF
# ==========================================
elif selected_tool == "Compress PDF":
    render_tool_header(
        "📦 Compress PDF",
        "Reduce PDF file size and compare compression settings."
    )

    uploaded_file = st.file_uploader(
        "Upload a PDF file",
        type=["pdf"],
        key="compress_pdf_upload"
    )

    if uploaded_file:
        original_data = uploaded_file.getvalue()
        original_size = len(original_data)

        st.subheader("Compression settings")

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

        st.info(
            f"Current settings: **{dpi} DPI** | **JPEG quality {quality}**"
        )

        try:
            import fitz
            from PIL import Image
            import io

            with st.spinner("Generating size preview..."):
                source_pdf = fitz.open(
                    stream=original_data,
                    filetype="pdf"
                )

                compressed_pdf = fitz.open()

                for page in source_pdf:
                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(dpi / 72, dpi / 72),
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

                compressed_data = compressed_pdf.tobytes(
                    garbage=4,
                    deflate=True
                )

                source_pdf.close()
                compressed_pdf.close()

            compressed_size = len(compressed_data)
            reduction = (
                (original_size - compressed_size) / original_size
            ) * 100

            st.subheader("Compression preview")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Original PDF",
                f"{original_size / 1024 / 1024:.2f} MB"
            )

            col2.metric(
                "Estimated compressed PDF",
                f"{compressed_size / 1024 / 1024:.2f} MB"
            )

            col3.metric(
                "Size reduction",
                f"{reduction:.1f}%"
            )

            st.caption(
                "The displayed size is calculated by compressing the PDF "
                "with the selected settings. Adjust the sliders to compare."
            )

            if compressed_size < original_size:
                st.success("These settings reduce the file size.")
            elif compressed_size == original_size:
                st.warning("These settings produce a file the same size as the original.")
            else:
                st.warning(
                    "These settings increase the file size. "
                    "Try lowering DPI or JPEG quality."
                )

            st.download_button(
                label="Download Compressed PDF",
                data=compressed_data,
                file_name="compressed.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"Compression preview failed: {e}")
# ==========================================
# 5. IMAGES TO PDF
# ==========================================
elif selected_tool == "Images to PDF":
    render_tool_header(
        "🖼️ Images to PDF",
        "Arrange images, apply filters, and create a PDF."
    )

    uploaded_images = st.file_uploader(
        "Upload images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="images_to_pdf_upload"
    )

    if uploaded_images:
        import io
        import pandas as pd
        from PIL import Image, ImageOps, ImageEnhance, ImageFilter

        def enhance_image(image, mode):
            image = ImageOps.exif_transpose(image).convert("RGB")

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

        st.subheader("1. Arrange pages")

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
            use_container_width=True,
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

        st.subheader("2. Choose an enhancement filter")

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

        for _, row in ordered_df.iterrows():
            original_index = int(row["Original order"]) - 1
            image_file = uploaded_images[original_index]

            image_file.seek(0)
            with Image.open(image_file) as source_image:
                processed_image = enhance_image(source_image, filter_mode)

            ordered_images.append(
                (image_file.name, processed_image.copy())
            )

        st.subheader("3. Preview processed pages")

        preview_columns = st.columns(min(3, len(ordered_images)))

        for index, (filename, processed_image) in enumerate(ordered_images):
            with preview_columns[index % len(preview_columns)]:
                st.image(
                    processed_image,
                    caption=f"Page {index + 1}: {filename}",
                    use_container_width=True
                )

        st.subheader("4. Create PDF")

        if st.button("Create PDF", type="primary"):
            try:
                if not ordered_images:
                    st.error("Please upload at least one image.")
                else:
                    pdf_buffer = io.BytesIO()

                    first_image = ordered_images[0][1]
                    remaining_images = [
                        item[1] for item in ordered_images[1:]
                    ]

                    first_image.save(
                        pdf_buffer,
                        format="PDF",
                        save_all=True,
                        append_images=remaining_images,
                        resolution=150
                    )

                    pdf_data = pdf_buffer.getvalue()

                    st.success(
                        f"PDF created successfully with "
                        f"{len(ordered_images)} pages."
                    )

                    st.download_button(
                        label="Download PDF",
                        data=pdf_data,
                        file_name="scanned_document.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"PDF creation failed: {e}")
# ==========================================
# 6. ROTATE PDF
# ==========================================

elif selected_tool == "Rotate PDF":

    render_tool_header(
        "🔄 Rotate PDF",
        "Rotate all pages or selected pages in a PDF document."
    )

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="rotate"
    )

    if file:

        try:
            reader = get_pdf_reader(file.getvalue())

            total = len(reader.pages)

            st.info(f"Total pages: {total}")

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

            if st.button("Rotate PDF", type="primary"):

                if not selected:
                    st.warning("Select at least one page.")
                else:
                    writer = PdfWriter()

                    for i, page in enumerate(reader.pages):

                        if i in selected:
                            page.rotate(rotation)

                        writer.add_page(page)

                    output = io.BytesIO()
                    writer.write(output)
                    writer.close()

                    st.success("PDF rotated successfully!")

                    pdf_download(
                        output.getvalue(),
                        "Rotated_Document.pdf"
                    )

        except Exception as e:
            st.error(f"Rotation failed: {e}")


# ==========================================
# 7. BATCH PDF TO WORD
# ==========================================

elif selected_tool == "Batch PDF to Word":

    render_tool_header(
        "📚 Batch PDF to Word",
        "Convert multiple PDF documents into editable Word files."
    )

    files = st.file_uploader(
        "Select multiple PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key="batch"
    )

    if files:

        st.info(f"{len(files)} documents selected.")

        if st.button("Convert All Documents", type="primary"):

            temp_dir = tempfile.mkdtemp()
            zip_buffer = io.BytesIO()

            try:
                with zipfile.ZipFile(
                    zip_buffer,
                    "w",
                    zipfile.ZIP_DEFLATED
                ) as zip_file:

                    progress = st.progress(0)

                    for index, file in enumerate(files):

                        pdf_path = os.path.join(
                            temp_dir,
                            f"input_{index}.pdf"
                        )

                        docx_path = os.path.join(
                            temp_dir,
                            f"output_{index}.docx"
                        )

                        with open(pdf_path, "wb") as f:
                            f.write(file.getvalue())

                        converter = None

                        try:
                            converter = Converter(pdf_path)
                            converter.convert(docx_path)

                            output_name = (
                                os.path.splitext(file.name)[0] + ".docx"
                            )

                            zip_file.write(
                                docx_path,
                                output_name
                            )

                        finally:
                            if converter is not None:
                                converter.close()

                        progress.progress(
                            (index + 1) / len(files)
                        )

                st.success("Batch conversion completed!")

                st.download_button(
                    "⬇️ Download All Word Files (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="Batch_Word_Conversion.zip",
                    mime="application/zip",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"Batch conversion failed: {e}")

            finally:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)


# ==========================================
# 8. PDF INFORMATION
# ==========================================

elif selected_tool == "PDF Information":

    render_tool_header(
        "🔍 PDF Information",
        "Inspect page count, file size, encryption status, and metadata."
    )

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="info"
    )

    if file:

        try:
            reader = get_pdf_reader(file.getvalue())

            col1, col2, col3 = st.columns(3)

            col1.metric("Total Pages", len(reader.pages))

            col2.metric(
                "File Size",
                f"{len(file.getvalue()) / 1024:.1f} KB"
            )

            col3.metric(
                "Encrypted",
                "Yes" if reader.is_encrypted else "No"
            )

            st.subheader("Document Metadata")

            metadata = reader.metadata

            if metadata:
                details = {
                    "Title": metadata.title,
                    "Author": metadata.author,
                    "Subject": metadata.subject,
                    "Creator": metadata.creator,
                    "Producer": metadata.producer,
                    "Creation Date": str(metadata.creation_date),
                }

                st.json(details)

            else:
                st.info("No metadata available.")

        except Exception as e:
            st.error(f"Unable to read PDF: {e}")



# ==========================================
# 9. REVERSE PDF
# ==========================================

elif selected_tool == "Reverse PDF":
    render_tool_header(
        "🔃 Reverse PDF",
        "Reverse the page order so the last page becomes the first."
    )
    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="reverse_pdf_upload"
    )

    if uploaded_file:
        try:
            reader = get_pdf_reader(uploaded_file.getvalue())
            total_pages = len(reader.pages)

            st.info(f"PDF uploaded successfully: {total_pages} pages.")

            if st.button("Reverse PDF", type="primary"):
                writer = PdfWriter()

                for page in reversed(reader.pages):
                    writer.add_page(page)

                output_buffer = io.BytesIO()
                writer.write(output_buffer)
                reversed_pdf = output_buffer.getvalue()

                st.success("PDF page order reversed successfully.")

                st.download_button(
                    label="Download Reversed PDF",
                    data=reversed_pdf,
                    file_name="reversed.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Unable to reverse PDF: {e}")
# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "Administrative PDF Toolkit 2.0 | "
    "Python + Streamlit | Cloud Edition"
)

st.caption(
    "Avoid uploading confidential or sensitive documents "
    "to this public cloud application."
)
