# Migración a n8n

Este documento explica cómo reemplazar el script de Python con flujos de trabajo de n8n.

## Requisitos

1.  **Node.js** instalado en tu PC.
2.  **n8n** instalado globalmente:
    ```powershell
    npm install n8n -g
    ```

## Configuración

### 1. Iniciar n8n

Abre una terminal (PowerShell) y ejecuta:

```powershell
n8n start --tunnel
```

_El flag `--tunnel` es opcional, pero útil si quieres recibir webhooks externos. Para uso local, `n8n start` basta._

### 2. Importar Flujos de Trabajo

1.  Abre tu navegador en `http://localhost:5678`.
2.  Crea un nuevo Workflow.
3.  Ve al menú (tres puntos arriba a la derecha) -> **Import from File**.
4.  Selecciona `workflow_opener.json` (este maneja la apertura de archivos).
5.  Activa el workflow (Switch "Active" arriba a la derecha).
6.  Repite el proceso para `workflow_indexer.json` (este maneja la sincronización).

### 3. Configurar Credenciales de Notion

1.  En n8n, ve a **Credentials**.
2.  Busca "Notion API".
3.  Pega tu `NOTION_TOKEN` (el que estaba en el archivo `.env`).

### 4. Ajustar Nodos

- **En el Workflow Indexer:**
  - Abre el nodo **Local File Trigger**.
  - Asegúrate de que `Path to Watch` sea `D:/Data`.
  - Abre los nodos de **Notion** y selecciona tu credencial recién creada.
  - Selecciona tu `Database ID` en los nodos de Notion (o pégalo manualmente si no carga la lista).

### 5. Ejecución

Una vez activados los workflows, n8n debe permanecer abierto (puedes minimizar la terminal) para que la sincronización funcione.

## Notas sobre Limitaciones en n8n

- **Jerarquía Recursiva:** El workflow JSON incluido maneja la creación básica de archivos. La lógica recursiva de "crear carpeta padre si no existe" es compleja de implementar visualmente en un solo paso en n8n sin usar bucles complejos o múltiples llamadas API. El workflow actual asume una estructura plana o que las carpetas ya existen.
- **Rendimiento:** n8n consume más RAM que el script de Python optimizado.
