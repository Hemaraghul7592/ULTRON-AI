from __future__ import annotations


class FileError(Exception):
    def __init__(self, message: str = "", path: str = "") -> None:
        self.path = path
        super().__init__(message)


class FileNotFoundError(FileError):
    pass


class InvalidFileTypeError(FileError):
    pass


class StorageError(FileError):
    pass


class DuplicateFileError(FileError):
    pass


class ProcessingError(FileError):
    pass


class FilePermissionError(FileError):
    pass
