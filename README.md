# Notion File Uploader

A robust, Dockerized tool that mirrors your local filesystem structure into a Notion Database. It creates a "Digital Twin" of your hard drive in Notion, allowing you to search and organize your local files using Notion's powerful interface.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-green.svg)

## ✨ Features

- **One-Way Sync:** Scans your local folder and updates Notion.
- **Recursive Hierarchy:** Recreates your folder tree using Notion "Sub-items".
- **Smart Updates:** Only updates changed files. Archives missing files.
- **Magic Links:** Generates local `file://` links to open files directly (OS dependent).
- **Clean Architecture:** Built with SOLID principles for reliability.

---

## 🚀 Getting Started

### 1. Notion Setup (Crucial Step!)

Create a new Database in Notion with the following properties. **The names must match exactly:**

| Property Name   | Type       | Description                                                                                                                            |
| :-------------- | :--------- | :------------------------------------------------------------------------------------------------------------------------------------- |
| **Name**        | `Title`    | The name of the file or folder.                                                                                                        |
| **RelativeID**  | `Text`     | Unique ID for sync (Do not edit manually).                                                                                             |
| **Extension**   | `Text`     | File extension (e.g., `.pdf`, `FOLDER`).                                                                                               |
| **MagicLink**   | `URL`      | Link to open the file locally.                                                                                                         |
| **Parent item** | `Relation` | **Important:** Create a Relation to _this same database_. Select "Use separate column for other relation". This enables the hierarchy. |

> **Tip:** Enable "Sub-items" in your Database view options and link it to the `Parent item` property to see the nested folder structure.

### 2. Get your Credentials

1.  **Notion Token:** Go to [Notion My Integrations](https://www.notion.so/my-integrations), create a new integration, and copy the "Internal Integration Secret".
2.  **Share Database:** Open your Database in Notion -> Click `...` (top right) -> `Connections` -> Add your new integration.
3.  **Database ID:** Open your Database as a full page. The ID is the 32-character code in the URL: `https://notion.so/myworkspace/THIS_IS_THE_ID?v=...`

---

## 🐳 Usage with Docker (Recommended)

No need to install Python. Just run the container.

### 1. Build the Image

```bash
docker build -t notion-uploader .
```

### 2. Run the Sync

**On Linux / macOS:**

```bash
docker run --rm \
  -v "/path/to/your/folder:/data" \
  -e NOTION_TOKEN="secret_your_token_here" \
  -e NOTION_DATABASE_ID="your_database_id_here" \
  -e WATCH_DIR="/data" \
  notion-uploader
```

**On Windows (PowerShell):**

```powershell
docker run --rm `
  -v "D:\Your\Folder:/data" `
  -e NOTION_TOKEN="secret_your_token_here" `
  -e NOTION_DATABASE_ID="your_database_id_here" `
  -e WATCH_DIR="/data" `
  notion-uploader
```

---

## 🛠 Manual Usage (Python)

If you prefer running it directly:

1.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment:**
    Create a `.env` file in the root directory:

    ```dotenv
    NOTION_TOKEN=secret_your_token_here
    NOTION_DATABASE_ID=your_database_id_here
    WATCH_DIR=D:/Path/To/Sync
    DEVICE_NAME=MyLaptop
    ```

3.  **Run:**
    ```bash
    python main.py
    ```

---

## 🏗 Architecture

For developers interested in the code structure:

- **Domain Layer:** Pure Python entities (`FileMeta`) and interfaces.
- **Application Layer:** Business logic (`Synchronizer`, `Factory`).
- **Infrastructure Layer:** Notion API implementation (`NotionRepository`).

The project follows **Clean Architecture** and **SOLID** principles. Each class is documented with **CRC Cards** in the source code.

## 🔄 n8n Migration

This repository includes a `n8n_migration/` folder with JSON workflows to replicate this functionality using **n8n** (a workflow automation tool), for those who prefer a low-code approach.

## 📄 License

This project is licensed under the MIT License.
