import io
import time
import fitz
import streamlit as st

# ---------- Page Config ----------
st.set_page_config(
    page_title="PDF Uploader & Viewer",
    page_icon="📄",
    layout="wide",
)

st.title("📄 PDF Uploader & Viewer (Streamlit)")
st.caption("Upload a PDF, preview pages, extract text, and download text as .txt")

# ---------- Sidebar Controls ----------
with st.sidebar:
    st.header("Controls")
    zoom = st.slider("Zoom (render scale)", 1.0, 3.0, 2.0, 0.1)
    show_text = st.checkbox("Show extracted text for selected page", value=True)
    show_metadata = st.checkbox("Show PDF metadata", value=True)
    st.markdown("---")
    st.markdown("**Tip:** For scanned PDFs with no selectable text, you'll need OCR.")

# ---------- File Uploader ----------
uploaded = st.file_uploader("Upload a PDF file", type=["pdf"], accept_multiple_files=False)

if uploaded is None:
    st.info("👆 Upload a PDF to get started.")
    st.stop()

# ---------- Open the PDF from bytes ----------
try:
    pdf_bytes = uploaded.getvalue()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
except Exception as e:
    st.error(f"Failed to open PDF: {e}")
    st.stop()

# ---------- Basic Info ----------
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("Pages", doc.page_count)
with col_b:
    st.metric("File Size", f"{len(pdf_bytes)/1024:.1f} KB")
with col_c:
    st.metric("Encrypted?", "Yes" if doc.is_encrypted else "No")

# ---------- Metadata ----------
if show_metadata:
    meta = doc.metadata or {}
    with st.expander("📇 Metadata", expanded=False):
        st.json(meta)

# ---------- Page Selector ----------
if doc.page_count > 1:
    page_index = st.slider("Select page", 1, doc.page_count, 1) - 1
else:
    page_index = 0

# ---------- Render Selected Page ----------
try:
    page = doc.load_page(page_index)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    st.image(pix.tobytes("png"), use_column_width=True)
except Exception as e:
    st.error(f"Failed to render page: {e}")

# ---------- Extract Text for Selected Page ----------
if show_text:
    try:
        page_text = page.get_text("text") or ""
        if page_text.strip():
            with st.expander("📝 Extracted Text (this page)", expanded=False):
                st.text(page_text)
        else:
            st.warning("No selectable text found on this page. This page might be an image (scanned). Consider OCR.")
    except Exception as e:
        st.error(f"Text extraction error: {e}")

# ---------- Download All Text ----------
if st.button("🔽 Extract & Prepare All Text"):
    with st.spinner("Extracting text from all pages..."):
        all_text_parts = []
        for i in range(doc.page_count):
            try:
                t = doc.load_page(i).get_text("text")
            except Exception:
                t = ""
            all_text_parts.append(f"\n\n===== Page {i+1} =====\n\n" + (t or ""))
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
    "Built with Streamlit + PyMuPDF. For OCR on scanned PDFs, consider ocrmypdf or pytesseract."
)
