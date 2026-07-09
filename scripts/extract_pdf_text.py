import sys
import io
from pdfminer.high_level import extract_text

pdf_bytes = sys.stdin.buffer.read()
text = extract_text(io.BytesIO(pdf_bytes))
sys.stdout.write(text)
