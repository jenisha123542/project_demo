import io
import time
import re
import streamlit as st
from pypdf import PdfReader
import spacy
import pandas as pd
import os

# ---------- Load spaCy ----------
nlp = spacy.load("en_core_web_sm")

# ---------- Config ----------
st.set_page_config(
    page_title="PDF Resume Parser",
    page_icon="📄",
    layout="wide",
)

st.title("📄 PDF Resume Parser (Streamlit + PyPDF + spaCy)")
st.caption("Upload a PDF, extract text, view structured resume information, and merge into master CSV.")

MASTER_CSV = "all_parsed_resumes.csv"  # Master file

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Controls")
    show_text = st.checkbox("Show extracted text for selected page", value=True)
    show_metadata = st.checkbox("Show PDF metadata", value=True)
    st.markdown("---")
    st.markdown("**Tip:** For scanned PDFs with no selectable text, you'll need OCR (pytesseract).")

# ---------- PDF Uploader ----------
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

# ---------- Extract All Text ----------
all_text_parts = []
for p in reader.pages:
    t = p.extract_text() or ""
    all_text_parts.append(t)
all_text = "\n\n".join(all_text_parts)
doc = nlp(all_text)

# ---------- Page Selector ----------
if len(reader.pages) > 1 and show_text:
    page_index = st.slider("Select page", 1, len(reader.pages), 1) - 1
    page_text = reader.pages[page_index].extract_text() or ""
    with st.expander(f"📝 Extracted Text (Page {page_index+1})", expanded=False):
        st.text(page_text)

# ---------- Parse Resume ----------
names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
name = names[0] if names else "N/A"
emails = re.findall(r'\S+@\S+', all_text)
phones = re.findall(r'\+?\d{10,12}', all_text)
skills_list = ["Python", "Java", "PHP", "SQL", "Pandas", "NumPy", 
               "Matplotlib", "Seaborn", "Tableau", "Machine Learning",
               "Deep Learning", "HTML", "CSS", "JavaScript", "Statistics",
               "Logistic Regression", "Random Forest", "KNN", "SVR"]
found_skills = [skill for skill in skills_list if skill.lower() in all_text.lower()]
education_keywords = ["Bachelors", "Masters", "+2", "School", "College", "University"]
education_lines = [line.strip() for line in all_text.split('\n') if any(k in line for k in education_keywords)]
projects_keywords = ["Project", "PROJECT", "projects", "ACADEMIC PROJECTS", "Mini Projects"]
projects_lines = [line.strip() for line in all_text.split('\n') if any(k in line for k in projects_keywords)]
profile_sentences = [sent.text.strip() for sent in doc.sents if "passionate" in sent.text.lower() or "skilled" in sent.text.lower()]

# ---------- Display Parsed Data ----------
st.markdown("## 🗂 Parsed Resume Information")
st.subheader("👤 Name"); st.write(name)
st.subheader("📧 Emails"); st.write(", ".join(emails) if emails else "N/A")
st.subheader("📞 Phone Numbers"); st.write(", ".join(phones) if phones else "N/A")
st.subheader("💡 Skills"); st.write(", ".join(found_skills) if found_skills else "N/A")
st.subheader("🎓 Education"); st.write("\n".join(education_lines) if education_lines else "N/A")
st.subheader("🛠 Projects"); st.write("\n".join(projects_lines) if projects_lines else "N/A")
st.subheader("📝 Profile / Summary"); st.write("\n".join(profile_sentences) if profile_sentences else "N/A")

# ---------- Prepare Resume Dict ----------
resume_dict = {
    "Name": name,
    "Emails": ", ".join(emails) if emails else "",
    "Phones": ", ".join(phones) if phones else "",
    "Skills": ", ".join(found_skills) if found_skills else "",
    "Education": "\n".join(education_lines) if education_lines else "",
    "Projects": "\n".join(projects_lines) if projects_lines else "",
    "Profile": "\n".join(profile_sentences) if profile_sentences else ""
}

df_new = pd.DataFrame([resume_dict])

# ---------- Merge with Master CSV ----------
if os.path.exists(MASTER_CSV):
    df_master = pd.read_csv(MASTER_CSV)
    df_combined = pd.concat([df_master, df_new], ignore_index=True)
else:
    df_combined = df_new

# Save merged CSV
df_combined.to_csv(MASTER_CSV, index=False)

# ---------- Show Merged Table ----------
st.subheader("📄 Master Resume CSV")
st.dataframe(df_combined)

# ---------- Download Master CSV ----------
csv_bytes = df_combined.to_csv(index=False).encode("utf-8")
st.download_button(
    label="💾 Download Master CSV",
    data=csv_bytes,
    file_name="all_parsed_resumes.csv",
    mime="text/csv"
)

# ---------- Footer ----------
st.markdown("---")
st.caption(
    "Built with Streamlit + PyPDF + spaCy. Each uploaded PDF is merged into a master CSV."
)
