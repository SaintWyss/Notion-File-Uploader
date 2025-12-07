import base64
from pathlib import Path

from src.domain import IMagicLinkGenerator


class SantiFSMagicLinkGenerator(IMagicLinkGenerator):
    """Implementación concreta usando Servidor Local (http://localhost)"""

    def generate(self, relative_path: Path) -> str:
        # Forzamos formato UNIX (/) para consistencia
        path_str = relative_path.as_posix()
        path_b64 = base64.urlsafe_b64encode(path_str.encode()).decode()
        # Usamos localhost en lugar de santifs://
        return f"http://localhost:12345/open?f={path_b64}"
