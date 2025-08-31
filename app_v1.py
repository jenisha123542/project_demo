import io
import time
import streamlit as st
from pypdf import PdfReader

# ---------- Page Config ----------
st.set_page_config(
    page_title="PDF Uploader & Viewer",
    page_icon="📄",
    layout="wide",
)

st.title("📄 PDF Uploader & Viewer (Streamlit + PyPDF)")
st.caption("Upload a PDF, preview pages, extract text, and download text as .txt")

# ---------- Sidebar Controls ----------
with st.sidebar:
    st.header("Controls")
    show_text = st.checkbox("Show extracted text for selected page", value=True)
    show_metadata = st.checkbox("Show PDF metadata", value=True)
    st.markdown("---")
    st.markdown("**Tip:** For scanned PDFs with no selectable text, you'll need OCR (pytesseract).")

# ---------- File Uploader ----------
uploaded = st.file_uploader("Upload a PDF file", type=["pdf"], accept_multiple_files=False)

if uploaded is None:
    st.info("👆 Upload a PDF to get started.")
    st.stop()

# ---------- Open PDF ----------
try:
    pdf_bytes = uploaded.read()
    reader = PdfReader(io.BytesIO(pdf_bytes))
except Exception as e:
    st.error(f"Failed to open PDF: {e}")
    st.stop()

# ---------- Basic Info ----------
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("Pages", len(reader.pages))
with col_b:
    st.metric("File Size", f"{len(pdf_bytes)/1024:.1f} KB")
with col_c:
    st.metric("Encrypted?", "Yes" if reader.is_encrypted else "No")

# ---------- Metadata ----------
if show_metadata:
    meta = reader.metadata or {}
    with st.expander("📇 Metadata", expanded=False):
        st.json(meta)

# ---------- Page Selector ----------
if len(reader.pages) > 1:
    page_index = st.slider("Select page", 1, len(reader.pages), 1) - 1
else:
    page_index = 0

# ---------- Extract Text for Selected Page ----------
if show_text:
    try:
        page = reader.pages[page_index]
        page_text = page.extract_text() or ""
        if page_text.strip():
            with st.expander(f"📝 Extracted Text (Page {page_index+1})", expanded=False):
                st.text(page_text)
        else:
            st.warning("No selectable text found on this page. This page might be scanned. Consider OCR.")
    except Exception as e:
        st.error(f"Text extraction error: {e}")

# ---------- Download All Text ----------
if st.button("🔽 Extract & Prepare All Text"):
    with st.spinner("Extracting text from all pages..."):
        all_text_parts = []
        for i, p in enumerate(reader.pages):
            t = p.extract_text() or ""
            all_text_parts.append(f"\n\n===== Page {i+1} =====\n\n" + t)
        all_text = "".join(all_text_parts)
        st.session_state["all_text"] = all_text
        time.sleep(0.2)
        st.success("Done! Use the download button below.")

if "all_text" in st.session_state and st.session_state["all_text"]:
    st.download_button(
        label="💾 Download Extracted Text (.txt)",
        data=st.session_state["all_text"].encode("utf-8"),
        file_name=(uploaded.name.rsplit(".", 1)[0] + "_extracted.txt"),
        mime="text/plain",
    )

# ---------- Footer ----------
st.markdown("---")
st.caption(
    "Built with Streamlit + PyPDF. For scanned PDFs, consider using pytesseract or ocrmypdf for OCR."
)
