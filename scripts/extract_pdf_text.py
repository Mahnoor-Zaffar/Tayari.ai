import sys
import io
from pypdf import PdfReader

pdf_bytes = sys.stdin.buffer.read()
reader = PdfReader(io.BytesIO(pdf_bytes))
for page in reader.pages:
    text = page.extract_text()
    if text:
        sys.stdout.write(text + "\n")
