# File Engine — ULTRON AI Platform

## Architecture

```
Upload ──► File Store ──► Parser ──► Content ──► AI Context
             │                           │
             ▼                           ▼
        S3 / Local                 Full-text Search
```

## Supported Formats

| Format | MIME Type | Parsing Strategy | Phase |
|--------|-----------|-----------------|-------|
| PDF | `application/pdf` | PyMuPDF / pdfplumber | M5 |
| DOCX | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | python-docx | M5 |
| TXT | `text/plain` | Direct read | M5 |
| CSV | `text/csv` | csv module → structured | M5 |
| ZIP | `application/zip` | zipfile → extract + parse each | M5 |
| JSON | `application/json` | json module | M5 |
| MD | `text/markdown` | Direct read | M5 |
| PNG/JPG | `image/*` | OCR (future: vision) | M6 |

## Storage Backend

```python
class FileStorage(ABC):
    """Abstract file storage interface."""

    @abstractmethod
    async def store(self, file: UploadFile, path: str) -> str: ...

    @abstractmethod
    async def retrieve(self, path: str) -> bytes: ...

    @abstractmethod
    async def delete(self, path: str) -> None: ...


class LocalStorage(FileStorage):
    """Local filesystem storage (dev)."""

class S3Storage(FileStorage):
    """S3-compatible storage (prod)."""
```

## Parsing Pipeline

```python
class ParsingPipeline:
    parsers: dict[str, FileParser] = {
        "application/pdf": PDFParser(),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DOCXParser(),
        "text/plain": TextParser(),
        "text/csv": CSVParser(),
        "application/json": JSONParser(),
        "text/markdown": TextParser(),
        # Image formats
        "image/png": OCRParser(),
        "image/jpeg": OCRParser(),
    }

    async def parse(self, file: File) -> ParseResult:
        parser = self.parsers.get(file.mime_type)
        if not parser:
            raise UnsupportedFormatError(file.mime_type)
        return await parser.parse(file)
```

## AI Context Integration

When a file is referenced in chat:

```json
{
  "content": "Analyze this document",
  "file_ids": ["uuid1", "uuid2"]
}
```

The backend:
1. Retrieves parsed content for each file
2. Truncates to budget (max 2000 tokens per file)
3. Injects into AI context as:

```
<file name="report.pdf">
[Full parsed content or summary for large files]
</file>
```

## Future: OCR + Vision

- Tesseract OCR for scanned documents
- Gemini Vision API for image understanding
- Invoice/receipt parsing

## Future: File Search

- Full-text search across parsed content
- Vector search for semantic file discovery
- Filter by type, date, size

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/files/upload` | Upload file(s) |
| GET | `/files` | List files (paginated, filterable) |
| GET | `/files/{id}` | File metadata |
| GET | `/files/{id}/download` | Download original |
| GET | `/files/{id}/content` | Get parsed text |
| DELETE | `/files/{id}` | Soft delete |
| POST | `/files/{id}/parse` | Trigger parse |
| POST | `/files/{id}/ocr` | Trigger OCR |
