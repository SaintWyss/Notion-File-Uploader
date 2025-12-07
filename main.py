"""
CRC Card:
    Module: Main
    Responsibilities:
        - Entry point of the application.
        - Loads environment variables.
        - Initializes dependencies (Repository, Factory, Synchronizer).
        - Executes the sync process.
    Collaborators:
        - Synchronizer
        - NotionRepository
        - FileMetaFactory
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.application.factories import FileMetaFactory
from src.application.synchronizer import Synchronizer
from src.domain import IMagicLinkGenerator
from src.infrastructure.notion_adapter import NotionRepository


class FileUriGenerator(IMagicLinkGenerator):
    """Generates file:// URIs (Passive link generation)."""

    def generate(self, relative_path: Path) -> str:
        # Since we don't have a server, we return a file URI.
        # Note: Notion Desktop might block this, but it's the standard way without a server.
        return Path(relative_path).as_uri()


def main():
    load_dotenv()

    token = os.getenv("NOTION_TOKEN")
    db_id = os.getenv("NOTION_DATABASE_ID")
    watch_dir_str = os.getenv("WATCH_DIR")
    device_name = os.getenv("DEVICE_NAME", "DockerWorker")

    if not all([token, db_id, watch_dir_str]):
        print(
            "ERROR: Missing .env variables (NOTION_TOKEN, NOTION_DATABASE_ID, WATCH_DIR)"
        )
        sys.exit(1)

    watch_dir = Path(watch_dir_str)
    if not watch_dir.exists():
        # In Docker, we expect the volume to be mounted here
        print(
            f"WARNING: Watch directory {watch_dir} does not exist. Ensure Docker volume is mounted."
        )

    print(f"--- SantiFS Sync Tool (Dockerized) ---")
    print(f"Target: {watch_dir}")

    # Dependency Injection
    link_gen = FileUriGenerator()
    repo = NotionRepository(token, db_id, link_gen)
    factory = FileMetaFactory(watch_dir, device_name)

    synchronizer = Synchronizer(repo, factory, watch_dir)

    try:
        synchronizer.sync()
    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
