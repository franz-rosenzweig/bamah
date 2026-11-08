"""Text out of the files she brings in: plain text, Markdown, Word (.docx) and PDF."""

import io
import re
import zipfile
from xml.etree import ElementTree

LIMIT = 200_000      # characters kept from one file
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class Unreadable(Exception):
    pass


def extract(name: str, data: bytes) -> str:
    ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
    if ext in ("txt", "md", "markdown", "text", ""):
        text = data.decode("utf-8", errors="replace")
    elif ext == "docx":
        text = _docx(data)
    elif ext == "pdf":
        text = _pdf(data)
    else:
        raise Unreadable(ext)
    text = re.sub(r"\n{3,}", "\n\n", text.replace("\r\n", "\n")).strip()
    if not text:
        raise Unreadable("empty")
    return text[:LIMIT]


def _docx(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            root = ElementTree.fromstring(z.read("word/document.xml"))
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError) as e:
        raise Unreadable("docx") from e
    paras = []
    for p in root.iter(W + "p"):
        bits = []
        for el in p.iter():
            if el.tag == W + "t" and el.text:
                bits.append(el.text)
            elif el.tag == W + "tab":
                bits.append("\t")
            elif el.tag in (W + "br", W + "cr"):
                bits.append("\n")
        paras.append("".join(bits))
    return "\n\n".join(p for p in paras if p.strip())


def _pdf(data: bytes) -> str:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages)
    except (PdfReadError, ValueError) as e:
        raise Unreadable("pdf") from e


def words(text: str) -> int:
    return len(text.split())
