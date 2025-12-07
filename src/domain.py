import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class FileMeta:
    """Entidad inmutable que representa un archivo físico o directorio."""

    absolute_path: Path
    relative_path: Path
    filename: str
    extension: str
    size_bytes: int
    last_modified_epoch: float
    device_id: str
    is_directory: bool = False


class IMagicLinkGenerator(Protocol):
    """Strategy: Define cómo se generan los links para abrir archivos."""

    def generate(self, relative_path: Path) -> str: ...


class INotionRepository(Protocol):
    """Repository: Abstracción para el almacenamiento de datos."""

    def upsert_file(self, file_meta: FileMeta) -> None: ...
    def mark_as_missing(self, relative_path: Path) -> None: ...
    def move_file(self, old_relative_path: Path, new_file_meta: FileMeta) -> None: ...
    def get_all_active_files(self) -> dict[str, str]: ...
