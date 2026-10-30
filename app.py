
import streamlit as st
from pdf2docx import Converter
from pypdf import PdfWriter
import tempfile
import os
import io

st.set_page_config(
    page_title="Administrative PDF Toolkit",
    page_icon="📁"
)

st.title("📁 Administrative PDF Toolkit")
st.write("Your personal document management application.")

tab1, tab2 = st.tabs([
    "PDF to Word",
    "Merge PDF"
])

# PDF TO WORD

with tab1:

    st.header("Convert PDF to Word")

    pdf = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="convert"
    )

    if pdf:

        if st.button("Convert to Word"):

            with st.spinner("Converting..."):

                pdf_path = None
                docx_path = None
                converter = None

                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".pdf"
                    ) as temp:
                        temp.write(pdf.getvalue())
                        pdf_path = temp.name

                    docx_path = pdf_path[:-4] + ".docx"

                    converter = Converter(pdf_path)
                    converter.convert(docx_path)

                    with open(docx_path, "rb") as f:
                        word_data = f.read()

                    st.success("Conversion successful!")

                    st.download_button(
                        "Download Word File",
                        word_data,
                        file_name=pdf.name.rsplit(".", 1)[0] + ".docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

                except Exception as e:
                    st.error(f"Error: {e}")

                finally:
                    if converter is not None:
                        converter.close()

                    for path in [pdf_path, docx_path]:
                        if path and os.path.exists(path):
                            os.remove(path)


# MERGE PDF

with tab2:

    st.header("Merge PDF Files")

    files = st.file_uploader(
        "Upload two or more PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key="merge"
    )

    if files:

        for file in files:
            st.write("📄", file.name)

        if len(files) >= 2:

            if st.button("Merge PDF Files"):

                writer = PdfWriter()

                try:
                    for file in files:
                        writer.append(io.BytesIO(file.getvalue()))

                    output = io.BytesIO()
                    writer.write(output)
                    writer.close()

                    st.success("PDFs merged successfully!")

                    st.download_button(
                        "Download Merged PDF",
                        output.getvalue(),
                        file_name="Merged_Document.pdf",
                        mime="application/pdf"
                    )

                except Exception as e:
                    writer.close()
                    st.error(f"Error: {e}")

        else:
            st.warning("Please upload at least two PDF files.")

st.divider()
st.caption("Administrative Toolkit | Python + Streamlit")
