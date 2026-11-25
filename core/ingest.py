"""Lecture des fichiers de cours et détection de la langue."""
import io
from langdetect import DetectorFactory, detect
from pypdf import PdfReader

DetectorFactory.seed = 0  # résultats reproductibles

def read_upload(uploaded) -> str:
    """Retourne le texte d'un fichier PDF / TXT / MD déposé dans Streamlit."""
    name = uploaded.name.lower()
    data = uploaded.getvalue()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((p.extract_text() or "") for p in reader.pages).strip()
    return data.decode("utf-8", errors="ignore").strip()

def detect_lang(text: str) -> str:
    try:
        return detect(text[:4000])
    except Exception:
        return "en"