import os
from pathlib import Path

from src.application.factories import FileMetaFactory
from src.domain import INotionRepository


class Synchronizer:
    def __init__(
        self, repository: INotionRepository, factory: FileMetaFactory, watch_dir: Path
    ):
        self._repo = repository
        self._factory = factory
        self._watch_dir = watch_dir

    def sync(self):
        print("--- STARTING SYNC ---")

        # 1. Get Notion State (and prime cache)
        notion_files = self._repo.get_all_active_files()
        print(f"[SYNC] Found {len(notion_files)} items in Notion.")

        # 2. Scan Local Files
        local_files_processed = set()

        # Walk directory
        for root, dirs, files in os.walk(self._watch_dir):
            # Process directories
            for d in dirs:
                dir_path = Path(root) / d
                if self._factory.should_process(dir_path):
                    rel_id = self._process_item(dir_path)
                    if rel_id:
                        local_files_processed.add(rel_id)

            # Process files
            for f in files:
                file_path = Path(root) / f
                if self._factory.should_process(file_path):
                    rel_id = self._process_item(file_path)
                    if rel_id:
                        local_files_processed.add(rel_id)

        # 3. Detect Deletions (Items in Notion but not in Local)
        print("[SYNC] Checking for deleted files...")
        for rel_path in notion_files.keys():
            if rel_path not in local_files_processed:
                print(f"[SYNC] Item missing locally: {rel_path}")
                self._repo.mark_as_missing(Path(rel_path))

        print("--- SYNC COMPLETE ---")

    def _process_item(self, path: Path) -> str | None:
        try:
            meta = self._factory.create_from_path(path)
            if not meta:
                return None
            self._repo.upsert_file(meta)
            return meta.relative_path.as_posix()
        except Exception as e:
            print(f"[ERROR] Processing {path}: {e}")
            return None
