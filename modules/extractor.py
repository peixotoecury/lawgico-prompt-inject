"""
Extração de texto de PDFs jurídicos.
Tenta pdfplumber primeiro; fallback para pymupdf (fitz).
"""
from __future__ import annotations
import io
import re

def extrair_texto(file_bytes: bytes, filename: str) -> dict:
    """
    Extrai texto de um PDF.
    Retorna dict: {texto, paginas, chars, metodo, aviso}
    """
    texto = ""
    paginas = 0
    metodo = ""
    aviso = ""

    # --- tentativa 1: pdfplumber ---
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            paginas = len(pdf.pages)
            partes = []
            for p in pdf.pages:
                t = p.extract_text() or ""
                partes.append(t)
            texto = "\n".join(partes)
        metodo = "pdfplumber"
    except Exception as e1:
        aviso = f"pdfplumber falhou ({e1}); "

    # --- fallback: pymupdf ---
    if not texto.strip():
        try:
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            paginas = len(doc)
            partes = [doc[i].get_text() for i in range(paginas)]
            texto = "\n".join(partes)
            metodo = "pymupdf"
        except Exception as e2:
            aviso += f"pymupdf falhou ({e2})"

    if not texto.strip():
        aviso = aviso or "Nenhum texto extraído (PDF pode ser imagem/escaneado)"

    return {
        "filename": filename,
        "texto": texto,
        "paginas": paginas,
        "chars": len(texto),
        "metodo": metodo,
        "aviso": aviso,
        "ilegivel": len(texto.strip()) < 100,
    }
