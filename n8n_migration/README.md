# Migración a n8n (SantiFS)

Este documento detalla cómo reemplazar el script de Python con un flujo de trabajo de **n8n**.

## 📋 Prerrequisitos

1.  **n8n instalado:** Preferiblemente usando Docker.
2.  **Acceso a archivos:** n8n debe tener acceso a la carpeta que quieres indexar.

## 🐳 Configuración con Docker (Recomendado)

Para que n8n pueda "ver" tus archivos locales, debes montar el volumen al iniciar el contenedor.

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v "D:/Data:/data" \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

_Nota: Esto monta tu carpeta `D:/Data` en `/data` dentro del contenedor._

## 📥 Importar el Workflow

1.  Abre n8n (`http://localhost:5678`).
2.  Crea un nuevo Workflow.
3.  Menú (arriba derecha) -> **Import from File**.
4.  Selecciona `workflow_full_sync.json`.

## ⚙️ Configuración del Workflow

Una vez importado, debes ajustar 3 cosas:

1.  **Credenciales de Notion:**

    - Haz doble clic en el nodo **Get Notion Pages**.
    - En "Credential for Notion API", selecciona "Create New" y pega tu Token.
    - En "Database ID", pega el ID de tu base de datos.
    - Repite esto para los nodos **Create Page**, **Update Page** y **Archive Page** (o copia y pega el ID).

2.  **Ruta de Archivos (Nodo "List Local Files"):**

    - El comando por defecto es para Linux/Docker:
      `find /data -type f ...`
    - Si estás corriendo n8n en **Windows nativo** (sin Docker), cambia el comando a:
      ```powershell
      Get-ChildItem "D:\Data" -Recurse -File | Select-Object FullName, Name, Length | ConvertTo-Json -Compress
      ```

3.  **Lógica de Comparación (Nodo "Compare Logic"):**
    - Abre el nodo de código.
    - Busca la línea `const WATCH_DIR = '/data';`.
    - Cámbiala si tu ruta de montaje es diferente (ej. `D:/Data` si usas Windows nativo).

## 🚀 Ejecución

1.  Haz clic en **Execute Workflow**.
2.  El sistema:
    - Descargará el estado de Notion.
    - Listará tus archivos locales.
    - Comparará ambos.
    - Creará/Actualizará/Borrará lo necesario.

## ⚠️ Limitaciones vs Python

- **Jerarquía Recursiva:** Este flujo crea los archivos en Notion, pero **NO crea automáticamente la estructura de carpetas padre** (Sub-items) si no existen. Implementar recursividad en n8n es complejo y requiere bucles avanzados. Este flujo asume una lista plana o que organizas las carpetas manualmente.
- **Rendimiento:** Para miles de archivos, n8n puede ser más lento que el script de Python optimizado.
