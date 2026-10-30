
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
    layout="wide"
)

# Custom styling
st.markdown("""
<style>
.main .block-container {
    max-width: 1150px;
    padding-top: 2rem;
}
.tool-card {
    padding: 18px;
    border: 1px solid rgba(128,128,128,0.25);
    border-radius: 12px;
    margin-bottom: 10px;
}
.small-note {
    color: gray;
    font-size: 13px;
}
.stDownloadButton button {
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# HEADER
# ==========================================

st.title("📁 Administrative PDF Toolkit")
st.caption("Version 2.0 | Your cloud-based document management suite")

st.divider()

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
    "PDF Information"
]

selected_tool = st.sidebar.selectbox(
    "SELECT A TOOL",
    tools
)

st.sidebar.divider()
st.sidebar.success("Version 2.0")
st.sidebar.caption("Administrative Document Utilities")
st.sidebar.caption("Developed using Python + Streamlit")

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


# ==========================================
# 1. PDF TO WORD
# ==========================================

if selected_tool == "PDF to Word":

    st.header("📄 PDF to Word Converter")
    st.write("Convert PDF documents into editable Word files.")

    uploaded = st.file_uploader(
        "Upload your PDF",
        type=["pdf"],
        key="single_word"
    )

    if uploaded:

        st.info(f"Selected: {uploaded.name}")

        if st.button("Convert to Word", type="primary"):

            pdf_path = None
            docx_path = None
            converter = None

            try:
                with st.spinner("Converting document..."):

                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".pdf"
                    ) as temp:
                        temp.write(uploaded.getvalue())
                        pdf_path = temp.name

                    docx_path = pdf_path[:-4] + ".docx"

                    converter = Converter(pdf_path)
                    converter.convert(docx_path)

                    with open(docx_path, "rb") as f:
                        result = f.read()

                st.success("Conversion completed!")

                st.download_button(
                    "⬇️ Download Word Document",
                    data=result,
                    file_name=os.path.splitext(uploaded.name)[0] + ".docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"Conversion failed: {e}")

            finally:
                if converter is not None:
                    converter.close()

                for path in [pdf_path, docx_path]:
                    if path and os.path.exists(path):
                        os.remove(path)


# ==========================================
# 2. MERGE PDF
# ==========================================

elif selected_tool == "Merge PDF":

    st.header("📚 Merge PDF Documents")
    st.write("Combine multiple PDF documents into one file.")

    files = st.file_uploader(
        "Select two or more PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key="merge"
    )

    if files:

        st.write("Selected documents:")

        for i, file in enumerate(files, 1):
            st.write(f"{i}. {file.name}")

        st.caption("Documents will be merged in the order listed above.")

        if st.button("Merge PDF Files", type="primary"):

            writer = PdfWriter()

            try:
                for file in files:
                    writer.append(io.BytesIO(file.getvalue()))

                output = io.BytesIO()
                writer.write(output)
                writer.close()

                st.success("PDFs merged successfully!")

                pdf_download(
                    output.getvalue(),
                    "Merged_Document.pdf"
                )

            except Exception as e:
                writer.close()
                st.error(f"Merge failed: {e}")


# ==========================================
# 3. SPLIT PDF
# ==========================================

elif selected_tool == "Split PDF":

    st.header("✂️ Split PDF")
    st.write("Extract selected pages from a PDF.")

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="split"
    )

    if file:

        try:
            reader = get_pdf_reader(file.getvalue())
            total = len(reader.pages)

            st.info(f"Total pages: {total}")

            page_range = st.text_input(
                "Enter pages or ranges",
                placeholder="Example: 1-5, 8, 10-12"
            )

            if st.button("Extract Pages", type="primary"):

                selected = parse_page_ranges(
                    page_range,
                    total
                )

                writer = PdfWriter()

                for page in selected:
                    writer.add_page(reader.pages[page])

                output = io.BytesIO()
                writer.write(output)
                writer.close()

                st.success(
                    f"{len(selected)} pages extracted successfully!"
                )

                pdf_download(
                    output.getvalue(),
                    "Extracted_Pages.pdf"
                )

        except Exception as e:
            st.error(f"Unable to split PDF: {e}")



# ==========================================
# 4. COMPRESS PDF
# ==========================================

elif selected_tool == "Compress PDF":

    st.header("📦 Compress PDF")
    st.write(
        "Attempt to reduce PDF size by compressing page content streams."
    )

    file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="compress"
    )

    if file:

        original = file.getvalue()

        st.info(
            f"Original size: {len(original) / 1024:.2f} KB"
        )

        if st.button("Compress PDF", type="primary"):

            try:
                reader = get_pdf_reader(original)
                writer = PdfWriter()

                with st.spinner("Compressing PDF..."):

                    # Step 1: Add all pages to the writer
                    for page in reader.pages:
                        writer.add_page(page)

                    # Step 2: Compress pages after adding them
                    for page in writer.pages:
                        page.compress_content_streams()

                    # Step 3: Generate the new PDF
                    output = io.BytesIO()
                    writer.write(output)
                    writer.close()

                compressed = output.getvalue()

                before = len(original)
                after = len(compressed)

                st.subheader("Compression Results")

                col1, col2 = st.columns(2)

                col1.metric(
                    "Original Size",
                    f"{before / 1024:.2f} KB"
                )

                col2.metric(
                    "Processed Size",
                    f"{after / 1024:.2f} KB"
                )

                if after < before:

                    reduction = (
                        (before - after) / before
                    ) * 100

                    st.success(
                        f"File size reduced by {reduction:.2f}%!"
                    )

                else:

                    st.warning(
                        "The processed PDF is not smaller. "
                        "Image-heavy PDFs may need image recompression."
                    )

                pdf_download(
                    compressed,
                    "Compressed_Document.pdf"
                )

            except Exception as e:

                st.error(
                    f"Compression failed: {e}"
                )

# ==========================================
# 5. IMAGES TO PDF
# ==========================================

elif selected_tool == "Images to PDF":

    st.header("🖼️ Images to PDF")
    st.write("Combine JPG, JPEG, and PNG images into one PDF.")

    images = st.file_uploader(
        "Upload images",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="images"
    )

    if images:

        st.write(f"{len(images)} images selected.")

        if st.button("Convert Images to PDF", type="primary"):

            try:
                converted = []

                for uploaded in images:
                    image = Image.open(
                        io.BytesIO(uploaded.getvalue())
                    )

                    if image.mode != "RGB":
                        image = image.convert("RGB")

                    converted.append(image.copy())
                    image.close()

                output = io.BytesIO()

                converted[0].save(
                    output,
                    format="PDF",
                    save_all=True,
                    append_images=converted[1:]
                )

                for image in converted:
                    image.close()

                st.success("Images converted successfully!")

                pdf_download(
                    output.getvalue(),
                    "Images_Combined.pdf"
                )

            except Exception as e:
                st.error(f"Image conversion failed: {e}")


# ==========================================
# 6. ROTATE PDF
# ==========================================

elif selected_tool == "Rotate PDF":

    st.header("🔄 Rotate PDF Pages")

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

    st.header("📚 Batch PDF to Word")
    st.write("Convert multiple PDF documents into Word files together.")

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

    st.header("🔍 PDF Information")
    st.write("Inspect the properties of a PDF document.")

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
