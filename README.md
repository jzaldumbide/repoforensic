# 🕵️‍♂️ RepoForensics — Análisis Forense de Plagio, Derivación de Código y Uso de IA en GitHub

[![Aplicación en Vivo](https://img.shields.io/badge/🌐_Demo_en_Vivo-repoforensic.onrender.com-2563eb?style=for-the-badge)](https://repoforensic.onrender.com/)
[![Descargar App (.ZIP)](https://img.shields.io/badge/⬇_Descargar_Aplicación-.ZIP-10b981?style=for-the-badge)](https://github.com/jzaldumbide/repoforensic/archive/refs/heads/main.zip)
[![Fork me on GitHub](https://img.shields.io/badge/🍴_Fork_me_on_GitHub-jzaldumbide%2Frepoforensic-f59e0b?style=for-the-badge&logo=github)](https://github.com/jzaldumbide/repoforensic/fork)
[![Sin Dependencias Externas](https://img.shields.io/badge/Dependencias-Zero_(Stdlib)-8b5cf6?style=for-the-badge)](#arquitectura-técnica)

**RepoForensics** es una plataforma web interactiva de auditoría académica y análisis forense de repositorios de GitHub. Permite determinar con precisión quirúrgica **quién copió a quién** (direccionalidad de la copia), visualizar cadenas de derivación en un grafo dirigido, comparar archivos de código lado a lado, cuantificar la **huella de uso de Inteligencia Artificial** (Claude, ChatGPT, Gemini, DeepSeek / OpenCode) y obtener un **% recomendado de amonestación orientativo** basado en la copia de un autor anterior y el arrastre del PDF del enunciado.

🔗 **Enlaces Rápidos:**
- 🌐 **Aplicación Web en Vivo (Render):** **[https://repoforensic.onrender.com/](https://repoforensic.onrender.com/)**
- ⬇️ **Descargar Aplicación Completa (.ZIP):** **[Descargar `repoforensic-main.zip`](https://github.com/jzaldumbide/repoforensic/archive/refs/heads/main.zip)**
- 🍴 **Hacer Fork en GitHub:** **[Fork `jzaldumbide/repoforensic`](https://github.com/jzaldumbide/repoforensic/fork)**

---

## 📋 Tabla de Contenidos

1. [Características Principales](#-características-principales)
2. [Cómo Usar la Aplicación Web (Guía Paso a Paso)](#-cómo-usar-la-aplicación-web-guía-paso-a-paso)
3. [Metodología Forense: ¿Cómo determina quién copió a quién?](#-metodología-forense-cómo-determina-quién-copió-a-quién)
4. [Métrica de Detección de Uso de IA (Claude, ChatGPT, Gemini, DeepSeek)](#-métrica-de-detección-de-uso-de-ia-claude-chatgpt-gemini-deepseek)
5. [Ejecución Local](#-ejecución-local)
6. [Arquitectura Técnica y Endpoints API](#-arquitectura-técnica-y-endpoints-api)

---

## ✨ Características Principales

- **🕸️ Grafo Dirigido Interactivo ("Quién copió a Quién"):**
  - Nodos codificados por color según su rol forense: **Semilla / Origen Temprano** (verde), **Derivado / Copia** (rojo), **Commits con IA Confirmada** (rosa), **Repositorio Pivote** (dorado) e **Independientes / Otros temas** (gris/azul).
  - Las flechas apuntan desde el **autor original** (commit más antiguo / mayor historial evolutivo) hacia el **repositorio que copió o derivó** el código.
  - Soporte completo para arrastrar nodos (*drag & drop*), hacer *zoom* con la rueda del ratón y desplazar el lienzo (*pan*).
- **🎯 Modo Repositorio Pivote (Estrella / Todos contra Uno):**
  - Permite seleccionar a cualquier estudiante como **Pivot** para colocarlo en el centro del grafo y comparar todos los demás repositorios frente a él en anillos concéntricos de similitud.
- **🔍 Comparador de Código Lado a Lado (Diff Inspector):**
  - Al hacer clic en cualquier arista, celda de la matriz o archivo coincidente, se abre un visor modal con el código fuente del repositorio origen a la izquierda y el del repositorio derivado a la derecha.
- **📊 Matriz Cruzada de Similitud ($N \times N$):**
  - Mapa de calor interactivo con los porcentajes de similitud de lógica de negocio pura entre todos los pares de repositorios.
- **⏱️ Cronología Forense de Git:**
  - Línea de tiempo comparativa con la fecha y hora exacta del primer y último commit de cada estudiante, junto con el conteo de commits (desarrollo incremental vs. subida masiva en 1 solo commit).
- **🤖 Auditoría de Uso de IA:**
  - Escaneo profundo del historial de Git (`Co-Authored-By`, `Claude-Session`, carpetas de agentes borradas como `.opencode/`) y heurísticas de prompts en el código (`// R1..R10`, densidad de bloques JSDoc, separadores ASCII y árboles de directorios).
- **➕ Gestión Dinámica de Repositorios:**
  - Permite agregar nuevos enlaces de GitHub (con o sin `.git`, rutas de ramas `/tree/rama` o subcarpetas), eliminar un repositorio individual o vaciar todo el análisis con un clic.

---

## 🚀 Cómo Usar la Aplicación Web (Guía Paso a Paso)

Ingresa a **[https://repoforensic.onrender.com/](https://repoforensic.onrender.com/)**:

### 1. Explorar el Grafo de Copia (Pestaña `Grafo de Copia`)
1. **Inspeccionar una copia (Flecha):** Haz clic sobre cualquier **flecha roja/naranja** o sobre su etiqueta de porcentaje (ej. `79.5%`). En el panel lateral derecho (`Inspector de Evidencia`) verás:
   - Quién es el **Autor / Origen** y quién **Copió / Derivó**, con la diferencia exacta en horas entre ambos.
   - El listado de razones forenses (cronología Git, firmas compartidas, cantidad de commits).
   - La lista de **Archivos de Lógica Coincidentes**. Haz clic en cualquier archivo de esa lista para abrir el **Comparador de Código Lado a Lado**.
2. **Inspeccionar un Estudiante (Nodo):** Haz clic sobre cualquier tarjeta del grafo para ver en el panel derecho:
   - Enlace directo a su GitHub, fecha del primer commit, total de commits, autores de Git y URL de MockAPI.
   - Su tarjeta de **🤖 Métrica de Uso de IA** con las evidencias detectadas.
   - Su **🎯 Ranking de Similitud (Top 12)** frente al resto de la clase.
   - Qué repositorios le copiaron (`➡ Fue copiado por`) y de quién copió (`⬅ Copió/derivó de`).
3. **Filtrar y Cambiar Disposición:** En la barra de herramientas superior puedes ajustar:
   - **Modo del Grafo:**
     - `Árbol Principal (¿Quién copió a quién?)`: Muestra únicamente la cadena primaria de derivación para evitar ruido visual.
     - `Centrado en el Pivot (Todos vs. Pivot)`: Organiza el grafo en estrella alrededor del repositorio pivote elegido.
     - `Copia / Derivación Alta (≥ 45%)`: Muestra todas las relaciones fuertes de plagio/derivación.
     - `Todas las Conexiones (≥ Umbral)`: Muestra la red completa según el deslizador de umbral.
   - **Umbral Mínimo:** Desliza entre `25%` y `75%` para filtrar conexiones en tiempo real.
   - **Disposición:** Alterna entre `Jerarquía Cronológica (Origen → Copia)` (de izquierda a derecha según el flujo temporal) y `Fuerzas Dirigidas (Clusters)`.

### 2. Fijar un Repositorio como Pivot (`🎯 Repo Pivote`)
Si deseas auditar a un estudiante específico frente a todo el curso:
1. Selecciona el repositorio en el menú desplegable **`🎯 Repo Pivote`** de la barra superior (o haz clic en un nodo y pulsa el botón **`🎯 Fijar como Pivot`** en el panel derecho).
2. El grafo colocará automáticamente a ese repositorio en el centro (resaltado en dorado), ubicando en el **anillo interior** a los 8 repositorios más similares y en el **anillo exterior** al resto.
3. Para regresar a la vista general, selecciona `— Ninguno (Vista Global) —` o pulsa **`✕ Quitar Pivot`**.

### 3. Consultar las Vistas Analíticas Superiores
Usa las pestañas centrales del encabezado para cambiar de vista:
- **`Matriz de Similitud`:** Tabla cruzada de todos contra todos. Haz clic en cualquier celda coloreada para abrir inmediatamente la comparación de código entre esos dos estudiantes.
- **`Cronología Git`:** Muestra en orden estrictamente cronológico quién empezó primero y cuánto tiempo duró su desarrollo.
- **`Veredicto Forense`:** Tarjetas ejecutivas con los casos principales de copia detectados listos para revisión.
- **`🤖 Uso de IA`:** Tabla detallada con el porcentaje de uso de IA, herramienta detectada (Claude, OpenCode/DeepSeek, ChatGPT/Gemini), conteo de citas a la rúbrica (`// R1..R10`), bloques JSDoc y evidencia en commits.
- **`⚖️ % Amonestación (Sugerido)`:** Tabla orientativa (solo como recomendación para el docente) que calcula un porcentaje de penalización sugerido combinando:
  1. **Copia / derivación respecto a un autor cronológicamente anterior** (`+15%` a `+75%` según el grado de similitud de archivos de lógica).
  2. **Arrastre del PDF completo del enunciado** (`+10%` a `+30%` si subió el archivo `.pdf` al repositorio/historial Git o si volcó íntegramente los literales `// R1..R10` del PDF en el prompt sin desarrollo progresivo).

### 4. Agregar o Borrar Repositorios
- **Agregar o Modificar lista (`+ Repositorios`):** Haz clic en el botón superior derecho **`+ Repositorios`**, pega las URLs de GitHub (acepta enlaces con o sin `.git`, con `/` final, ramas `/tree/nombre-rama` o subcarpetas `/tree/main/src/carpeta`) y pulsa **`Clonar y Re-Analizar Repositorios`**.
- **Eliminar un solo repositorio (`🗑 Quitar`):** Selecciona un nodo en el grafo y pulsa **`🗑 Quitar`** en la esquina superior de su resumen en el panel derecho.
- **Vaciar todo (`🗑 Borrar Repos`):** Pulsa el botón rojo **`🗑 Borrar Repos`** en la barra superior para limpiar todos los repositorios y comenzar un análisis desde cero.

---

## 🧬 Metodología Forense: ¿Cómo determina quién copió a quién?

En proyectos basados en frameworks modernos (como **Ionic + Angular + Capacitor**), más de 15 archivos generados por el CLI (`eslint.config.js`, `playwright.config.ts`, `test-setup.ts`, `*.spec.ts`, `explore-container`, `main.ts`, `app.component.*`) son 100% idénticos entre todos los estudiantes por defecto.

Para evitar **falsos positivos**, `RepoForensics` aplica un pipeline de 4 etapas en [`analyzer.py`](analyzer.py):

1. **Filtrado Estricto de Boilerplate:** Excluye automáticamente los archivos de plantilla del framework y evalúa únicamente los **archivos de lógica de negocio propia** (servicios HTTP, almacenamiento local, modelos de datos, páginas/componentes con lógica y scripts de poblado *seed*).
2. **Comparación Agonística de Rutas (*Path-Agnostic Matching*) + *k-Shingles*:** Aunque un estudiante renombre `src/app/services/imagen.ts` a `municipio/src/app/core/services/fotos.service.ts`, el motor compara todos los archivos propios entre sí mediante conjuntos de *3-shingles* léxicos y alineación de secuencias (`difflib.SequenceMatcher`) tras normalizar espacios y comentarios.
3. **Extracción de Huellas Digitales de Código (*Forensic Signatures*):** Detecta 20 marcadores específicos de implementación, tales como:
   - Nombres exactos de funciones utilitarias (`coordenadasValidas(lat, lon)`), constantes (`TRANSICIONES`, `UMBRAL_LLUVIA_MM`) y tipos (`export type NuevaIncidencia = Omit<Incidencia, 'id'>`).
   - Claves internas de `@capacitor/preferences` (`seguimiento_codigos`, `borrador_incidencia`, `urbaninspect_seguimiento`).
   - Scripts de *seed* con patrones idénticos (`https://picsum.photos/seed/inc${i}`, `padStart(3, '0')`).
4. **Dirección Temporal y Autoría en Git (`Origen → Copia`):**
   - Cruza la matriz de similitud con la marca de tiempo Unix (`git log --all --format=%at`) del primer commit y la densidad de commits, orientando la flecha desde el proyecto original hacia el derivado y detectando cuentas múltiples del mismo autor.

---

## 🤖 Métrica de Detección de Uso de IA (Claude, ChatGPT, Gemini, DeepSeek)

El módulo `analyze_ai_usage` en [`analyzer.py`](analyzer.py) combina dos niveles de verificación:

1. **Evidencia Directa en el Historial Profundo de Git (`git log --all --stat`):**
   - Detecta *trailers* y cabeceras de autoría dejadas por herramientas de IA en línea de comandos o web, como `Author: Claude <noreply@anthropic.com>`, `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` y enlaces `Claude-Session: https://claude.ai/code/...`.
   - Detecta carpetas de configuración de agentes que fueron creadas durante el desarrollo y **eliminadas antes de la entrega final** (por ejemplo, `.opencode/agents/deepseek-codigo.md`, `REGISTRO-DEEPSEEK.md`, `HANDOFF.md`, `.cursor/`, `.claude/`).
2. **Heurísticas Estilísticas de Prompts en el Código:**
   - **Citas explícitas a la rúbrica (`// R1`, `// R3`, `// R9`):** Cuando se adjunta el PDF de un examen a un LLM (ChatGPT, Claude o Gemini), el modelo etiqueta cada método con el código del requisito de la rúbrica.
   - **Densidad de bloques JSDoc (`/** ... */`) y banners decorativos (`// ────────`):** Cuantifica la estructura documental típica de salidas generadas por LLMs.
   - **Árboles de directorios ASCII (`├──`, `└──`) en `README.md` y emojis en literales de código.**
   - **Patrón de volcado masivo (*Bulk Commit*) y *Conventional Commits*.**

---

## 💻 Ejecución Local

El proyecto utiliza únicamente la librería estándar de Python 3 y `git` (cero dependencias externas en `pip`):

```bash
# 1. Clonar el repositorio
git clone https://github.com/jzaldumbide/repoforensic.git
cd repoforensic

# 2. Iniciar el servidor web (por defecto en el puerto 8765)
python3 server.py
```

Abre en tu navegador: **`http://localhost:8765`**

*(Opcional)* Si deseas volver a clonar y regenerar `analysis_results.json` por consola:
```bash
python3 analyzer.py
```

---

## 🛠️ Arquitectura Técnica y Endpoints API

```
repoforensic/
├── analyzer.py             # Motor forense (Git log, k-shingles, firmas de código y detector de IA)
├── server.py               # Servidor HTTP Python + API REST (/api/results, /api/reanalyze, etc.)
├── analysis_results.json   # Resultados precalculados listos para carga instantánea en Render
├── public/
│   ├── index.html          # Estructura de las 5 vistas, barra de herramientas y modales <dialog>
│   ├── styles.css          # Diseño adaptable Light/Dark mode y estilos del grafo/matriz
│   └── app.js              # Renderizado SVG interactivo, modo Pivot, matriz, cronología y diff modal
├── render.yaml             # Blueprint de configuración para despliegue en Render.com
├── requirements.txt        # Sin dependencias pesadas (despliegue rápido en Render Free Tier)
└── .python-version         # Versión de Python fijada (3.11.9)
```

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/results` | Devuelve el JSON completo con nodos, aristas, comparaciones y métricas de IA. |
| `POST` | `/api/reanalyze` | Recibe `{"urls": [...]}` en el cuerpo, clona/actualiza los repositorios y recalcula todo el grafo. |
| `POST` | `/api/delete-repo` | Recibe `{"id": "owner/repo"}` y elimina ese repositorio específico del grafo actual. |
| `POST` | `/api/clear-repos` | Borra todos los repositorios analizados y limpia la caché local (`repos_cache`). |
| `GET` | `/api/health` | Endpoint de verificación de estado (`{"status": "ok"}`). |

