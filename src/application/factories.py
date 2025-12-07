"""
CRC Card:
    Class: FileMetaFactory
    Responsibilities:
        - Creates FileMeta instances from filesystem paths.
        - Validates if a file should be processed (filtering hidden/temp files).
        - Calculates relative paths based on the root watch directory.
    Collaborators: FileMeta
"""

from pathlib import Path

from src.domain import FileMeta


class FileMetaFactory:
    def __init__(self, root_path: Path, device_id: str):
        self._root = root_path.resolve()
        self._device_id = device_id

    def should_process(self, path: Path) -> bool:
        """Filters out hidden files and temporary files."""
        if path.name.startswith(".") or path.name.startswith("~$"):
            return False
        return True

    def create_from_path(self, absolute_path: Path) -> FileMeta | None:
        """Creates a FileMeta object if the path is valid and within root."""
        try:
            path = absolute_path.resolve()
            stat = path.stat()

            try:
                rel_path = path.relative_to(self._root)
            except ValueError:
                return None

            return FileMeta(
                absolute_path=path,
                relative_path=rel_path,
                filename=path.name,
                extension=path.suffix if not path.is_dir() else "DIR",
                size_bytes=stat.st_size,
                last_modified_epoch=stat.st_mtime,
                device_id=self._device_id,
                is_directory=path.is_dir(),
            )
        except (FileNotFoundError, PermissionError):
            return None
