from pathlib import Path
from typing import Any

import httpx
from notion_client import Client

from src.domain import FileMeta, IMagicLinkGenerator, INotionRepository


class NotionRepository(INotionRepository):
    def __init__(
        self, api_token: str, database_id: str, link_generator: IMagicLinkGenerator
    ):
        self._client = Client(auth=api_token)
        self._api_token = api_token
        # Limpieza y formateo de ID
        clean_id = database_id.strip()
        if len(clean_id) == 32:
            self._db_id = f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"
        else:
            self._db_id = clean_id

        print(f"[DEBUG] Notion DB ID: {self._db_id}")
        self._link_gen = link_generator
        self._id_cache: dict[str, str] = {}
        self._ensure_hierarchy_property()

    def _ensure_hierarchy_property(self):
        """Verifica y crea la propiedad de relación para sub-items si no existe."""
        try:
            db = self._client.databases.retrieve(self._db_id)
            # Verificamos si existe "ítem principal" (Español) o "Parent item" (Inglés)
            if "ítem principal" in db["properties"]:
                print("[INIT] Detectada propiedad de jerarquía: 'ítem principal'")
                return
            if "Parent item" in db["properties"]:
                print("[INIT] Detectada propiedad de jerarquía: 'Parent item'")
                return

            print(
                "[INIT] Creando propiedad 'Parent item' para jerarquía de carpetas..."
            )
            # Creamos una relación dual (bidireccional) con la misma base de datos
            self._client.databases.update(
                database_id=self._db_id,
                properties={
                    "Parent item": {
                        "relation": {
                            "database_id": self._db_id,
                            "type": "dual_property",
                            "dual_property": {},
                        }
                    }
                },
            )
            print("[INIT] Propiedad creada exitosamente.")
        except Exception as e:
            print(f"[WARN] No se pudo configurar la jerarquía automática: {e}")
            print(
                "Asegúrate de activar 'Sub-items' en la configuración de la base de datos en Notion."
            )

    def get_all_active_files(self) -> dict[str, str]:
        """
        Recupera todos los archivos activos (no archivados) de la base de datos.
        Retorna un diccionario {relative_path: page_id}.
        """
        print("[SYNC] Fetching all pages from Notion...")
        url = f"https://api.notion.com/v1/databases/{self._db_id}/query"
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        mapping = {}
        has_more = True
        next_cursor = None

        while has_more:
            body = {"page_size": 100}
            if next_cursor:
                body["start_cursor"] = next_cursor

            try:
                response = httpx.post(url, headers=headers, json=body, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                for page in data["results"]:
                    page_id = page["id"]
                    props = page["properties"]
                    # Extraer RelativeID
                    rel_id_list = props.get("RelativeID", {}).get("rich_text", [])
                    if rel_id_list:
                        rel_id = rel_id_list[0]["text"]["content"]
                        mapping[rel_id] = page_id

                has_more = data.get("has_more", False)
                next_cursor = data.get("next_cursor")
                print(f"[SYNC] Fetched {len(mapping)} items so far...")

            except Exception as e:
                print(f"[ERROR] Fetching pages: {e}")
                break

        self._id_cache = mapping.copy()
        return mapping

    def _find_page_by_relative_id(self, rel_path: str) -> str | None:
        if rel_path in self._id_cache:
            return self._id_cache[rel_path]

        # Usamos httpx directo porque la librería notion-client está dando problemas
        url = f"https://api.notion.com/v1/databases/{self._db_id}/query"
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        body = {"filter": {"property": "RelativeID", "rich_text": {"equals": rel_path}}}

        try:
            response = httpx.post(url, headers=headers, json=body, timeout=10.0)
            # Si da 404 o 400, lanzará error aquí
            response.raise_for_status()
            data = response.json()
            results = data.get("results")
            return results[0]["id"] if results else None
        except Exception as e:
            # print(f"[DEBUG ERROR HTTPX] {e}")
            return None

    def _ensure_parent_folder(self, relative_path: Path) -> str | None:
        """
        Asegura que la carpeta padre exista en Notion.
        Retorna el ID de la página de la carpeta padre, o None si es raíz.
        """
        if len(relative_path.parts) <= 1:
            return None

        parent_path = relative_path.parent
        parent_rel_id = parent_path.as_posix()

        # Buscamos si ya existe la carpeta padre
        parent_id = self._find_page_by_relative_id(parent_rel_id)

        if parent_id:
            return parent_id

        # Si no existe, la creamos recursivamente
        print(f"[AUTO-CREATE FOLDER] {parent_path.name}")

        # Recursión para el abuelo
        grandparent_id = self._ensure_parent_folder(parent_path)

        # Creamos la carpeta padre
        properties: dict[str, Any] = {
            "Name": {"title": [{"text": {"content": parent_path.name}}]},
            "RelativeID": {"rich_text": [{"text": {"content": parent_rel_id}}]},
            "Extension": {"rich_text": [{"text": {"content": "FOLDER"}}]},
            "MagicLink": {"url": "https://notion.so"},  # Placeholder para carpetas
        }

        # Intentamos vincular con el abuelo si existe (Sub-items)
        if grandparent_id:
            # Intentamos con "ítem principal" primero (Español), luego "Parent item"
            properties["ítem principal"] = {"relation": [{"id": grandparent_id}]}

        try:
            print(f"[AUTO-CREATE FOLDER] {parent_path.name}")
            new_page = self._client.pages.create(
                parent={"database_id": self._db_id},
                properties=properties,
                icon={"type": "emoji", "emoji": "📁"},
            )
            return new_page["id"]
        except Exception as e:
            # Si falla, probamos con "Parent item" (Inglés)
            if "ítem principal" in properties:
                del properties["ítem principal"]
                properties["Parent item"] = {"relation": [{"id": grandparent_id}]}
                try:
                    new_page = self._client.pages.create(
                        parent={"database_id": self._db_id},
                        properties=properties,
                        icon={"type": "emoji", "emoji": "📁"},
                    )
                    return new_page["id"]
                except Exception:
                    pass  # Falló con ambos, seguimos sin padre

            print(f"[ERROR] Creating folder {parent_path.name}: {e}")
            # Intentamos crear sin relación por si falla todo
            if "Parent item" in properties:
                del properties["Parent item"]
            if "ítem principal" in properties:
                del properties["ítem principal"]

            try:
                new_page = self._client.pages.create(
                    parent={"database_id": self._db_id},
                    properties=properties,
                    icon={"type": "emoji", "emoji": "📁"},
                )
                return new_page["id"]
            except Exception:
                return None
            return None

    def upsert_file(self, meta: FileMeta) -> None:
        rel_id = meta.relative_path.as_posix()

        try:
            existing_page_id = self._find_page_by_relative_id(rel_id)
        except Exception:
            existing_page_id = None

        # Delegamos la generación del link a la estrategia inyectada
        magic_link = self._link_gen.generate(meta.relative_path)

        properties: dict[str, Any] = {
            "Name": {"title": [{"text": {"content": meta.filename}}]},
            "RelativeID": {"rich_text": [{"text": {"content": rel_id}}]},
            "Extension": {
                "rich_text": [
                    {
                        "text": {
                            "content": (
                                "FOLDER"
                                if meta.is_directory
                                else meta.extension.lower().replace(".", "") or "None"
                            )
                        }
                    }
                ]
            },
            "MagicLink": {"url": magic_link},
        }

        # Icono según tipo
        icon = (
            {"type": "emoji", "emoji": "📁"}
            if meta.is_directory
            else {"type": "emoji", "emoji": "📄"}
        )

        # Intentamos buscar y vincular con el padre
        parent_id = self._ensure_parent_folder(meta.relative_path)
        if parent_id:
            # Usamos el ID de la propiedad directamente: 'zK%3E%3A' (ítem principal)
            properties["zK%3E%3A"] = {"relation": [{"id": parent_id}]}

        try:
            if existing_page_id:
                print(f"[UPDATE] {meta.filename}")
                try:
                    self._client.pages.update(
                        page_id=existing_page_id, properties=properties, icon=icon
                    )
                except Exception as e:
                    # Fallback por nombre
                    if "zK%3E%3A" in properties:
                        del properties["zK%3E%3A"]
                        properties["ítem principal"] = {"relation": [{"id": parent_id}]}
                        try:
                            self._client.pages.update(
                                page_id=existing_page_id,
                                properties=properties,
                                icon=icon,
                            )
                        except Exception:
                            # Si falla todo, sin padre
                            if "ítem principal" in properties:
                                del properties["ítem principal"]
                            self._client.pages.update(
                                page_id=existing_page_id,
                                properties=properties,
                                icon=icon,
                            )

            else:
                print(f"[CREATE] {meta.filename}")
                try:
                    self._client.pages.create(
                        parent={"database_id": self._db_id},
                        properties=properties,
                        icon=icon,
                    )
                except Exception as e:
                    # Fallback por nombre
                    if "zK%3E%3A" in properties:
                        del properties["zK%3E%3A"]
                        properties["ítem principal"] = {"relation": [{"id": parent_id}]}
                        try:
                            self._client.pages.create(
                                parent={"database_id": self._db_id},
                                properties=properties,
                                icon=icon,
                            )
                        except Exception:
                            # Si falla todo, sin padre
                            if "ítem principal" in properties:
                                del properties["ítem principal"]
                            self._client.pages.create(
                                parent={"database_id": self._db_id},
                                properties=properties,
                                icon=icon,
                            )
        except Exception as e:
            print(f"[ERROR] Syncing {meta.filename}: {e}")

    def mark_as_missing(self, relative_path: Path) -> None:
        rel_id = relative_path.as_posix()
        page_id = self._find_page_by_relative_id(rel_id)
        if page_id:
            print(f"[DELETE] {relative_path}")
            self._client.pages.update(page_id=page_id, archived=True)

    def move_file(self, old_relative_path: Path, meta: FileMeta) -> None:
        old_rel_id = old_relative_path.as_posix()
        new_rel_id = meta.relative_path.as_posix()

        print(f"[MOVE] {old_rel_id} -> {new_rel_id}")

        try:
            # 1. Buscar la página con el ID antiguo
            page_id = self._find_page_by_relative_id(old_rel_id)

            if not page_id:
                # Si no existe, lo tratamos como un archivo nuevo
                print(
                    f"[MOVE WARN] No se encontró origen. Creando nuevo: {meta.filename}"
                )
                self.upsert_file(meta)
                return

            # 2. Preparar propiedades actualizadas
            magic_link = self._link_gen.generate(meta.relative_path)

            properties: dict[str, Any] = {
                "Name": {"title": [{"text": {"content": meta.filename}}]},
                "RelativeID": {"rich_text": [{"text": {"content": new_rel_id}}]},
                "Extension": {
                    "rich_text": [
                        {
                            "text": {
                                "content": (
                                    "FOLDER"
                                    if meta.is_directory
                                    else meta.extension.lower().replace(".", "")
                                    or "None"
                                )
                            }
                        }
                    ]
                },
                "MagicLink": {"url": magic_link},
            }

            # 3. Actualizar Padre (si cambió de carpeta)
            parent_id = self._ensure_parent_folder(meta.relative_path)
            if parent_id:
                # Usamos el ID de la propiedad directamente: 'zK%3E%3A' (ítem principal)
                properties["zK%3E%3A"] = {"relation": [{"id": parent_id}]}

            # 4. Ejecutar actualización
            try:
                self._client.pages.update(page_id=page_id, properties=properties)
            except Exception as e:
                # Fallback por nombre si falla ID de propiedad
                if "zK%3E%3A" in properties:
                    del properties["zK%3E%3A"]
                    properties["ítem principal"] = {"relation": [{"id": parent_id}]}
                    try:
                        self._client.pages.update(
                            page_id=page_id, properties=properties
                        )
                    except Exception:
                        if "ítem principal" in properties:
                            del properties["ítem principal"]
                        self._client.pages.update(
                            page_id=page_id, properties=properties
                        )

        except Exception as e:
            print(f"[ERROR] Moving {old_relative_path}: {e}")
