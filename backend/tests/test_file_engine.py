from __future__ import annotations

import tempfile

import pytest

from app.file_engine.errors import (
    DuplicateFileError,
    FileNotFoundError,  # noqa: A004
    FilePermissionError,
    InvalidFileTypeError,
    ProcessingError,
    StorageError,
)
from app.file_engine.interface import FileMetadata, StorageProvider
from app.file_engine.models import StoredFile
from app.file_engine.processors.audio import AudioProcessor
from app.file_engine.processors.base import ChainProcessor
from app.file_engine.processors.image import ImageProcessor
from app.file_engine.processors.ocr import OCRProcessor
from app.file_engine.processors.pdf import PDFProcessor
from app.file_engine.processors.text import TextProcessor
from app.file_engine.service import FileService
from app.file_engine.storage.local import LocalStorage
from app.file_engine.utils import (
    get_extension,
    get_storage_subpath,
    guess_mime_type,
    is_supported_filename,
    safe_filename,
    sha256_hash,
    temp_file,
)


class FakeStorage(StorageProvider):
    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}
        self._fail = False

    @property
    def name(self) -> str:
        return "fake"

    async def save(self, path: str, data: bytes) -> str:
        if self._fail:
            raise StorageError("storage failed")
        self._files[path] = data
        return path

    async def load(self, path: str) -> bytes:
        if self._fail:
            raise StorageError("storage failed")
        if path not in self._files:
            raise FileNotFoundError(f"not found: {path}")
        return self._files[path]

    async def delete(self, path: str) -> bool:
        if self._fail:
            raise StorageError("storage failed")
        return self._files.pop(path, None) is not None

    async def exists(self, path: str) -> bool:
        return path in self._files

    async def move(self, source: str, destination: str) -> bool:
        if source not in self._files:
            return False
        self._files[destination] = self._files.pop(source)
        return True

    async def copy(self, source: str, destination: str) -> bool:
        if source not in self._files:
            return False
        self._files[destination] = self._files[source]
        return True

    async def list_files(self, prefix: str = "") -> list[str]:
        return sorted(p for p in self._files if p.startswith(prefix))

    async def get_metadata(self, path: str) -> dict:
        if path not in self._files:
            raise FileNotFoundError(f"not found: {path}")
        return {"size": len(self._files[path]), "path": path}


class TestStorageProvider:
    @pytest.mark.asyncio
    async def test_save_and_load(self) -> None:
        s = FakeStorage()
        path = await s.save("test/a.txt", b"hello")
        assert path == "test/a.txt"
        data = await s.load("test/a.txt")
        assert data == b"hello"

    @pytest.mark.asyncio
    async def test_load_not_found(self) -> None:
        s = FakeStorage()
        with pytest.raises(FileNotFoundError):
            await s.load("nonexistent")

    @pytest.mark.asyncio
    async def test_delete_existing(self) -> None:
        s = FakeStorage()
        await s.save("f.txt", b"data")
        assert await s.delete("f.txt") is True
        assert await s.exists("f.txt") is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self) -> None:
        s = FakeStorage()
        assert await s.delete("nope") is False

    @pytest.mark.asyncio
    async def test_move(self) -> None:
        s = FakeStorage()
        await s.save("src.txt", b"data")
        assert await s.move("src.txt", "dst.txt") is True
        assert await s.exists("src.txt") is False
        assert await s.load("dst.txt") == b"data"

    @pytest.mark.asyncio
    async def test_copy(self) -> None:
        s = FakeStorage()
        await s.save("src.txt", b"data")
        assert await s.copy("src.txt", "dst.txt") is True
        assert await s.load("src.txt") == b"data"
        assert await s.load("dst.txt") == b"data"

    @pytest.mark.asyncio
    async def test_list_files(self) -> None:
        s = FakeStorage()
        await s.save("a/x.txt", b"1")
        await s.save("a/y.txt", b"2")
        await s.save("b/z.txt", b"3")
        files = await s.list_files("a/")
        assert files == ["a/x.txt", "a/y.txt"]

    @pytest.mark.asyncio
    async def test_get_metadata(self) -> None:
        s = FakeStorage()
        await s.save("f.txt", b"hello")
        meta = await s.get_metadata("f.txt")
        assert meta["size"] == 5


class TestLocalStorage:
    @pytest.fixture
    def tmp_root(self) -> str:
        d = tempfile.mkdtemp()
        yield d
        import shutil

        shutil.rmtree(d, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_save_and_load(self, tmp_root: str) -> None:
        s = LocalStorage(root=tmp_root)
        path = await s.save("test/file.txt", b"hello world")
        assert path == "test/file.txt"
        data = await s.load("test/file.txt")
        assert data == b"hello world"

    @pytest.mark.asyncio
    async def test_load_not_found(self, tmp_root: str) -> None:
        s = LocalStorage(root=tmp_root)
        with pytest.raises(FileNotFoundError):
            await s.load("nope")

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, tmp_root: str) -> None:
        s = LocalStorage(root=tmp_root)
        with pytest.raises(FilePermissionError):
            await s.load("../etc/passwd")

    @pytest.mark.asyncio
    async def test_delete(self, tmp_root: str) -> None:
        s = LocalStorage(root=tmp_root)
        await s.save("f.txt", b"data")
        assert await s.delete("f.txt") is True
        assert await s.exists("f.txt") is False

    @pytest.mark.asyncio
    async def test_list_files(self, tmp_root: str) -> None:
        s = LocalStorage(root=tmp_root)
        await s.save("a/1.txt", b"x")
        await s.save("a/2.txt", b"y")
        files = await s.list_files("a/")
        assert len(files) == 2

    @pytest.mark.asyncio
    async def test_exists(self, tmp_root: str) -> None:
        s = LocalStorage(root=tmp_root)
        await s.save("x.txt", b"data")
        assert await s.exists("x.txt") is True
        assert await s.exists("y.txt") is False

    @pytest.mark.asyncio
    async def test_move(self, tmp_root: str) -> None:
        s = LocalStorage(root=tmp_root)
        await s.save("src.txt", b"data")
        assert await s.move("src.txt", "dst.txt") is True
        assert await s.load("dst.txt") == b"data"

    @pytest.mark.asyncio
    async def test_copy(self, tmp_root: str) -> None:
        s = LocalStorage(root=tmp_root)
        await s.save("src.txt", b"data")
        assert await s.copy("src.txt", "dst.txt") is True
        assert await s.load("dst.txt") == b"data"


class TestFileUtils:
    def test_sha256_hash(self) -> None:
        h = sha256_hash(b"hello")
        assert len(h) == 64
        assert h == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_safe_filename(self) -> None:
        assert safe_filename("hello.txt") == "hello.txt"
        assert safe_filename("../foo/bar.txt") == "foo_bar.txt"
        name = safe_filename("")
        assert name.startswith("unnamed_")

    def test_get_extension(self) -> None:
        assert get_extension("file.txt") == ".txt"
        assert get_extension("file.TXT") == ".txt"
        assert get_extension("file") == ""
        assert get_extension("archive.tar.gz") == ".gz"

    def test_guess_mime_type(self) -> None:
        assert guess_mime_type("test.txt") == "text/plain"
        assert guess_mime_type("test.pdf") == "application/pdf"
        assert guess_mime_type("test.unknown") == "application/octet-stream"

    def test_is_supported_filename(self) -> None:
        assert is_supported_filename("test.txt") is True
        assert is_supported_filename("test.pdf") is True
        assert is_supported_filename("test.png") is True
        assert is_supported_filename("test.exe") is False
        assert is_supported_filename("test") is False

    def test_get_storage_subpath(self) -> None:
        path = get_storage_subpath("abc123def456", "test.txt")
        assert path == "abc1/test.txt"

    @pytest.mark.asyncio
    async def test_temp_file(self) -> None:
        async with temp_file(suffix=".txt") as tmp:
            assert tmp.exists()
            tmp.write_text("hello")
            assert tmp.read_text() == "hello"
        assert not tmp.exists()


class TestProcessors:
    @pytest.mark.asyncio
    async def test_text_processor(self) -> None:
        p = TextProcessor()
        assert p.name == "text"
        assert ".txt" in p.supported_extensions()
        meta = FileMetadata(
            filename="test.txt",
            mime_type="text/plain",
            extension=".txt",
            size=12,
            sha256="x",
            storage_path="",
        )
        text = await p.extract_text(b"hello world", meta)
        assert text == "hello world"
        processed = await p.process(b"line1\nline2\n", meta)
        assert processed.extra["line_count"] == 3

    @pytest.mark.asyncio
    async def test_text_unicode_decode(self) -> None:
        p = TextProcessor()
        meta = FileMetadata(
            filename="f.txt",
            mime_type="text/plain",
            extension=".txt",
            size=5,
            sha256="x",
            storage_path="",
        )
        text = await p.extract_text(b"\xff\xfe\x00\x68\x00", meta)
        assert isinstance(text, str)

    @pytest.mark.asyncio
    async def test_image_processor_png(self) -> None:
        p = ImageProcessor()
        assert ".png" in p.supported_extensions()

        header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
        w = 100
        h = 200
        import struct

        header += struct.pack(">II", w, h)
        header += b"\x00" * 8

        meta = FileMetadata(
            filename="img.png",
            mime_type="image/png",
            extension=".png",
            size=len(header),
            sha256="x",
            storage_path="",
        )
        processed = await p.process(header, meta)
        assert processed.width == 100
        assert processed.height == 200

    @pytest.mark.asyncio
    async def test_image_processor_jpeg(self) -> None:
        p = ImageProcessor()
        data = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xc0\x00\x11\x08\x02\x00\x01\x80\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01"
            b"\xff\xd9"
        )
        meta = FileMetadata(
            filename="img.jpg",
            mime_type="image/jpeg",
            extension=".jpg",
            size=len(data),
            sha256="x",
            storage_path="",
        )
        processed = await p.process(data, meta)
        assert processed.width == 384
        assert processed.height == 512

    @pytest.mark.asyncio
    async def test_pdf_processor(self) -> None:
        p = PDFProcessor()
        assert ".pdf" in p.supported_extensions()
        assert p.validate(b"%PDF-1.4 stuff", None) is True
        assert p.validate(b"not pdf", None) is False

    @pytest.mark.asyncio
    async def test_pdf_extract_text(self) -> None:
        p = PDFProcessor()
        pdf_data = b"%PDF-1.4\n1 0 obj<</Type /Page>>endobj\nxref\n...\n%%EOF"
        meta = FileMetadata(
            filename="doc.pdf",
            mime_type="application/pdf",
            extension=".pdf",
            size=len(pdf_data),
            sha256="x",
            storage_path="",
        )
        processed = await p.process(pdf_data, meta)
        assert processed.pages is not None

    @pytest.mark.asyncio
    async def test_audio_processor_wav(self) -> None:
        p = AudioProcessor()
        assert ".wav" in p.supported_extensions()
        import struct

        sample_rate = 44100
        channels = 2
        bits = 16
        data_size = 44100 * 2 * 2
        wav = b"RIFF" + struct.pack("<I", 36 + data_size) + b"WAVE"
        wav += b"fmt " + struct.pack(
            "<IHHIIHH",
            16,
            1,
            channels,
            sample_rate,
            sample_rate * channels * bits // 8,
            channels * bits // 8,
            bits,
        )
        wav += b"data" + struct.pack("<I", data_size) + b"\x00" * data_size
        meta = FileMetadata(
            filename="audio.wav",
            mime_type="audio/wav",
            extension=".wav",
            size=len(wav),
            sha256="x",
            storage_path="",
        )
        processed = await p.process(wav, meta)
        assert processed.duration is not None
        assert processed.duration > 0

    @pytest.mark.asyncio
    async def test_ocr_processor_extensions(self) -> None:
        p = OCRProcessor()
        exts = p.supported_extensions()
        assert ".png" in exts
        assert ".jpg" in exts
        assert ".pdf" in exts

    @pytest.mark.asyncio
    async def test_chain_processor(self) -> None:
        tp = TextProcessor()
        ip = ImageProcessor()
        chain = ChainProcessor([tp, ip])
        assert chain.name == "chain"
        assert ".txt" in chain.supported_extensions()
        assert ".png" in chain.supported_extensions()

        meta = FileMetadata(
            filename="test.txt",
            mime_type="text/plain",
            extension=".txt",
            size=5,
            sha256="x",
            storage_path="",
        )
        result = await chain.process(b"hello", meta)
        assert result.extra.get("char_count") == 5


class TestFileService:
    @pytest.fixture
    def service(self) -> FileService:
        return FileService(storage=FakeStorage(), max_size=1024 * 1024, deduplicate=True)

    @pytest.mark.asyncio
    async def test_save_text_file(self, service: FileService) -> None:
        sf = await service.save(b"hello world", "test.txt")
        assert sf.filename == "test.txt"
        assert sf.mime_type == "text/plain"
        assert sf.extension == ".txt"
        assert sf.size == 11
        assert len(sf.sha256) == 64
        assert sf.storage_provider == "fake"

    @pytest.mark.asyncio
    async def test_save_empty_fails(self, service: FileService) -> None:
        with pytest.raises(ValueError, match="empty"):
            await service.save(b"", "empty.txt")

    @pytest.mark.asyncio
    async def test_save_unsupported_type(self, service: FileService) -> None:
        with pytest.raises(InvalidFileTypeError):
            await service.save(b"data", "file.exe")

    @pytest.mark.asyncio
    async def test_save_too_large(self, service: FileService) -> None:
        service._max_size = 10
        with pytest.raises(InvalidFileTypeError, match="too large"):
            await service.save(b"x" * 100, "test.txt")

    @pytest.mark.asyncio
    async def test_deduplicate(self, service: FileService) -> None:
        await service.save(b"unique content", "a.txt")
        with pytest.raises(DuplicateFileError):
            await service.save(b"unique content", "b.txt")

    @pytest.mark.asyncio
    async def test_deduplicate_disabled(self) -> None:
        svc = FileService(storage=FakeStorage(), deduplicate=False)
        await svc.save(b"same data", "a.txt")
        sf = await svc.save(b"same data", "b.txt")
        assert sf.filename == "b.txt"

    @pytest.mark.asyncio
    async def test_save_with_custom_mime(self, service: FileService) -> None:
        sf = await service.save(b"{}", "data.json", mime_type="application/json")
        assert sf.mime_type == "application/json"

    @pytest.mark.asyncio
    async def test_load_file(self, service: FileService) -> None:
        sf = await service.save(b"content", "f.txt")
        data = await service.load(sf.storage_path)
        assert data == b"content"

    @pytest.mark.asyncio
    async def test_load_not_found(self, service: FileService) -> None:
        with pytest.raises(FileNotFoundError):
            await service.load("nonexistent/path")

    @pytest.mark.asyncio
    async def test_delete(self, service: FileService) -> None:
        sf = await service.save(b"data", "del.txt")
        assert await service.delete(sf.storage_path) is True
        with pytest.raises(FileNotFoundError):
            await service.load(sf.storage_path)

    @pytest.mark.asyncio
    async def test_copy(self, service: FileService) -> None:
        service._deduplicate = False
        sf = await service.save(b"data", "src.txt")
        copied = await service.copy(sf.storage_path, "dst.txt")
        assert copied.filename == "dst.txt"
        data = await service.load(copied.storage_path)
        assert data == b"data"

    @pytest.mark.asyncio
    async def test_move(self, service: FileService) -> None:
        service._deduplicate = False
        sf = await service.save(b"data", "src.txt")
        moved = await service.move(sf.storage_path, "moved.txt")
        assert moved.filename == "moved.txt"
        with pytest.raises(FileNotFoundError):
            await service.load(sf.storage_path)

    @pytest.mark.asyncio
    async def test_exists(self, service: FileService) -> None:
        sf = await service.save(b"x", "exists.txt")
        assert await service.exists(sf.storage_path) is True
        assert await service.exists("nope") is False

    @pytest.mark.asyncio
    async def test_extract_text(self, service: FileService) -> None:
        text = await service.extract_text(b"hello world", "test.txt")
        assert text == "hello world"

    @pytest.mark.asyncio
    async def test_extract_text_unsupported(self, service: FileService) -> None:
        text = await service.extract_text(b"\x00\x01", "file.bin")
        assert text == ""

    @pytest.mark.asyncio
    async def test_health_check(self, service: FileService) -> None:
        health = await service.health_check()
        assert health["storage"] == "fake"
        assert health["storage_ok"] is True
        assert health["max_size"] > 0
        assert len(health["registered_processors"]) > 0

    @pytest.mark.asyncio
    async def test_list_files(self, service: FileService) -> None:
        await service.save(b"a", "a.txt")
        await service.save(b"b", "b.txt")
        files = await service.list_files()
        assert len(files) >= 2

    @pytest.mark.asyncio
    async def test_get_metadata(self, service: FileService) -> None:
        sf = await service.save(b"data", "meta.txt")
        meta = await service.get_metadata(sf.storage_path)
        assert "size" in meta


class TestFileServiceProcessors:
    @pytest.mark.asyncio
    async def test_text_file_gets_char_count(self) -> None:
        svc = FileService(storage=FakeStorage())
        sf = await svc.save(b"hello\nworld\n", "test.txt")
        assert sf.extra.get("char_count") == 12
        assert sf.extra.get("line_count") == 3

    @pytest.mark.asyncio
    async def test_png_file_gets_dimensions(self) -> None:
        p = ImageProcessor()
        import struct
        import zlib

        sig = b"\x89PNG\r\n\x1a\n"
        ihdr_data = struct.pack(">IIBBBBB", 50, 75, 8, 2, 0, 0, 0)
        ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF)
        ihdr_len = struct.pack(">I", 13)
        iend_crc = struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
        iend_len = struct.pack(">I", 0)
        png_data = sig + ihdr_len + b"IHDR" + ihdr_data + ihdr_crc + iend_len + b"IEND" + iend_crc
        meta = FileMetadata(
            filename="img.png",
            mime_type="image/png",
            extension=".png",
            size=len(png_data),
            sha256="x",
            storage_path="",
        )
        processed = await p.process(png_data, meta)
        assert processed.width == 50
        assert processed.height == 75


class TestFileMetadata:
    def test_stored_file_to_metadata(self) -> None:
        sf = StoredFile(
            filename="test.txt",
            mime_type="text/plain",
            extension=".txt",
            size=5,
            sha256="abc",
            storage_path="ab/test.txt",
        )
        meta = sf.to_metadata()
        assert meta["filename"] == "test.txt"
        assert meta["sha256"] == "abc"
        assert meta["extension"] == ".txt"

    def test_stored_file_from_metadata(self) -> None:
        data = {
            "filename": "f.txt",
            "mime_type": "text/plain",
            "extension": ".txt",
            "size": 10,
            "sha256": "def",
            "storage_path": "de/f.txt",
        }
        sf = StoredFile.from_metadata(data)
        assert sf.filename == "f.txt"
        assert sf.sha256 == "def"

    def test_stored_file_default_values(self) -> None:
        sf = StoredFile(
            filename="a.txt",
            mime_type="text/plain",
            extension=".txt",
            size=1,
            sha256="h",
            storage_path="h/a.txt",
        )
        assert sf.file_id is not None
        assert sf.created_at is not None
        assert sf.storage_provider == "local"
        assert sf.width is None
        assert sf.extra == {}


class TestFileErrors:
    def test_error_classes(self) -> None:
        e1 = FileNotFoundError("not found", path="/f.txt")
        assert str(e1) == "not found"
        assert e1.path == "/f.txt"

        e2 = InvalidFileTypeError("bad type")
        assert isinstance(e2, FileNotFoundError) is False

        e3 = DuplicateFileError("dup")
        assert isinstance(e3, FileNotFoundError) is False

        e4 = ProcessingError("proc fail")
        assert isinstance(e4, FileNotFoundError) is False

        e5 = StorageError("storage fail")
        assert isinstance(e5, FileNotFoundError) is False
