# File Engine — ULTRON AI

## Architecture

```
FileService
    │
    ├── StorageProvider (interface)
    │       └── LocalStorage (filesystem)
    │
    ├── Processors
    │       ├── TextProcessor (.txt, .md, .json, .csv, .xml, .yaml, .yml)
    │       ├── ImageProcessor (.png, .jpg, .jpeg, .webp, .gif, .svg)
    │       ├── PDFProcessor (.pdf)
    │       ├── AudioProcessor (.mp3, .wav, .m4a, .flac, .ogg)
    │       └── OCRProcessor (wraps Plugin Engine OCR)
    │
    └── Utils
            ├── SHA-256 hashing
            ├── Safe filename sanitization
            ├── MIME type mapping
            ├── Storage path generation
            └── Temp file context manager
```

## Core Files

| File | Purpose |
|------|---------|
| `app/file_engine/interface.py` | `StorageProvider` ABC + `FileMetadata` dataclass |
| `app/file_engine/errors.py` | `FileError` hierarchy (7 types) |
| `app/file_engine/models.py` | `StoredFile` model with serialization |
| `app/file_engine/utils.py` | Hashing, safe naming, MIME maps, temp files |
| `app/file_engine/service.py` | `FileService` — single entry point |
| `app/file_engine/storage/local.py` | `LocalStorage` — filesystem backed, path traversal protection |
| `app/file_engine/processors/base.py` | `Processor` ABC + `ChainProcessor` |
| `app/file_engine/processors/text.py` | Text processor (UTF-8 decode, char/line/word counts) |
| `app/file_engine/processors/image.py` | Image processor (PNG/JPEG/GIF/WebP dimension extraction) |
| `app/file_engine/processors/pdf.py` | PDF processor (text extraction, page count, validation) |
| `app/file_engine/processors/audio.py` | Audio processor (WAV duration, MP3 estimate) |
| `app/file_engine/processors/ocr.py` | OCR wrapper (delegates to Plugin Engine) |

## StorageProvider Interface

| Method | Returns | Description |
|--------|---------|-------------|
| `save(path, data)` | `str` | Store bytes, returns storage path |
| `load(path)` | `bytes` | Read file content |
| `delete(path)` | `bool` | Remove file, returns success |
| `exists(path)` | `bool` | Check file existence |
| `move(source, dest)` | `bool` | Move file between paths |
| `copy(source, dest)` | `bool` | Copy file between paths |
| `list_files(prefix)` | `list[str]` | List all files matching prefix |
| `get_metadata(path)` | `dict` | OS-level metadata (size, timestamps) |

## FileService API

| Method | Description |
|--------|-------------|
| `save(data, filename, mime_type, run_ocr)` | Validate → hash → dedup check → store → process → return `StoredFile` |
| `load(path)` | Read bytes from storage |
| `delete(path)` | Remove file from storage |
| `copy(source, filename)` | Load + save to new filename |
| `move(source, filename)` | Copy + delete source |
| `exists(path)` | Check storage existence |
| `list_files(prefix)` | List stored files |
| `get_metadata(path)` | Storage metadata |
| `extract_text(data, filename)` | Extract text using processor |
| `health_check()` | Storage check + processor registry |

## Error Hierarchy

```
FileError
├── FileNotFoundError
├── InvalidFileTypeError
├── StorageError
├── DuplicateFileError
├── ProcessingError
└── PermissionError
```

## Supported File Types

| Category | Extensions | Processor |
|----------|-----------|-----------|
| Text | .txt, .md, .json, .csv, .xml, .yaml, .yml | TextProcessor |
| Images | .png, .jpg, .jpeg, .webp, .gif, .svg | ImageProcessor |
| PDF | .pdf | PDFProcessor |
| Audio | .mp3, .wav, .m4a, .flac, .ogg | AudioProcessor |
| Documents | .docx, .xlsx, .pptx | Unsupported (metadata only) |
| Archives | .zip, .tar, .gz | Unsupported (metadata only) |

## Processor Interface

| Method | Description |
|--------|-------------|
| `process(data, metadata)` | Full processing pipeline, returns enriched `FileMetadata` |
| `extract_text(data, metadata)` | Text extraction |
| `extract_metadata(data, metadata)` | Additional metadata |
| `validate(data, metadata)` | Format validation |
| `supported_extensions()` | Set of handled extensions |

## Hashing & Deduplication

- SHA-256 hash computed on every `save()`
- Storage path: `{hash[:4]}/{safe_filename}`
- `deduplicate=True` (default) rejects identical files
- Hash-based `_find_by_hash()` scans prefix directories

## OCR Integration

`OCRProcessor` delegates to the Plugin Engine's OCR plugin:
- Instantiates `OCRPlugin`, calls `initialize()`, then `execute(image_base64=...)`
- Supports all image + PDF extensions
- `name_ocr=True` on `FileService.save()` triggers OCR processing
- Failures are silently caught (OCR text set to empty)

## Temp Files

```python
from app.file_engine.utils import temp_file

async with temp_file(suffix=".txt") as tmp:
    tmp.write_text("data")
    # tmp is a Path, auto-deleted on exit
```

## Safety

- `LocalStorage._resolve()` rejects `../` path traversal
- `safe_filename()` strips special characters and leading `._`
- Filenames truncated to 255 chars
- Max file size configurable (default 50MB)
- MIME types normalized via extension mapping

## Future Extensibility

- Implement `StorageProvider` for S3, Google Drive, Azure Blob
- Swap `SearchCache` for distributed cache
- Add new processors by implementing `Processor` ABC
- Add `FileService` as a FastAPI dependency for REST endpoints

## Tests

`tests/test_file_engine.py` — 56 tests covering:
- StorageProvider (save, load, delete, move, copy, list, metadata, not found)
- LocalStorage (path traversal, exists, directories)
- Utils (SHA-256, safe naming, MIME, extensions, storage path, temp file)
- Processors (text, image PNG/JPEG/GIF/WebP, PDF validate/extract, audio WAV/MP3, OCR extensions, ChainProcessor)
- FileService (save, load, delete, copy, move, deduplication, size limits, unsupported types, custom MIME, health check, list, metadata, text extraction)
- FileMetadata (serialization, defaults, from dict)
- FileError hierarchy
