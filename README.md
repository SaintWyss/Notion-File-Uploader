# SantiFS (Notion Indexer) - Dockerized

A robust synchronization tool that mirrors your local filesystem structure into a Notion Database.

## 🏗 Architecture & Design

This project follows **Clean Architecture** principles and **SOLID** design patterns to ensure maintainability and scalability.

### Layers

1.  **Domain (`src/domain.py`)**:
    - Contains core entities (`FileMeta`) and interfaces (`INotionRepository`, `IMagicLinkGenerator`).
    - _Pattern:_ **Data Transfer Object (DTO)** for `FileMeta`.
2.  **Application (`src/application/`)**:
    - Contains business logic.
    - `Synchronizer`: Orchestrates the sync process (Service Layer).
    - `FileMetaFactory`: Creates domain objects (Factory Pattern).
3.  **Infrastructure (`src/infrastructure/`)**:
    - `NotionRepository`: Implements the repository interface using Notion API.
    - _Pattern:_ **Repository Pattern** to decouple data access.
    - _Pattern:_ **Adapter Pattern** to adapt Notion API to our domain interface.

### Documentation (CRC)

The code is fully documented using **CRC (Class-Responsibility-Collaborator)** cards within the docstrings of each class.

## 🐳 Docker Usage

This tool is designed to run as a Docker container.

### 1. Build Image

```bash
docker build -t santifs .
```

### 2. Run Container

You need to mount the directory you want to index to `/data` (or whatever path you set in ENV) and provide the `.env` file.

```bash
docker run --rm \
  -v "D:/Data:/data" \
  -e NOTION_TOKEN="secret_..." \
  -e NOTION_DATABASE_ID="your_db_id" \
  -e WATCH_DIR="/data" \
  santifs
```

## 🛠 Manual Installation (Python)

1.  Install Python 3.11+.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Configure `.env`.
4.  Run: `python main.py`

## 🔄 Migration to n8n

This Python project serves as the "Legacy Core" or "Reference Implementation".
To migrate to n8n:

1.  Use the workflows provided in `n8n_migration/`.
2.  The logic in `src/infrastructure/notion_adapter.py` (specifically recursive folder creation) is the most complex part to replicate in n8n.

## 📄 License

MIT
