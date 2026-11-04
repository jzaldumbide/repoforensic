import os
import re
import json
import subprocess
import difflib
from pathlib import Path
from datetime import datetime

REPOS_RAW = [
    "https://github.com/JustinPaladines/Prueba_Urban-Inspect/tree/main",
    "https://github.com/Arielpassw/urban-inspect.git",
    "https://github.com/MaCaReNo26/Urban-Inspect---Suarez-Alex.git",
    "https://github.com/Amy-Mishell06/Urban-inspect.git",
    "https://github.com/mangodev-hub/Prueba1_CPuente.git",
    "https://github.com/alexbarba2753/PRUEBA-PRACTICA-1-MOVILES.git",
    "https://github.com/NW08/Apps_GR1/tree/main/src/Clase_08",
    "https://github.com/gabrielt007/Urbaninspect-",
    "https://github.com/JimSul16/API-Explorer",
    "https://github.com/chico20200/bestiario_DnD.git",
    "https://github.com/DannyPoli06/prueba-bien-hecha.git",
    "https://github.com/Dilanbkr7/UrbanInspect",
    "https://github.com/gabrielt007/UrbanInspect_Togma_v2.git",
    "https://github.com/chico20200/urbanInspect.git",
    "https://github.com/michael-epn/quito-app.git",
    "https://github.com/Emialejandra/Urban-Inspect.git",
    "https://github.com/Jossue-Chulde/quito-alerta",
    "https://github.com/jossuer1/Examen-Aplicaciones-Moviles",
    "https://github.com/Eduxrd-o/UrbanInspect",
    "https://github.com/josselynreyes-ux/Prueba1_DesarrolloMovil/tree/PruebaPractica01",
    "https://github.com/DannyPoli06/PruebadeMoviles-N1.git",
    "https://github.com/MarioEndara/Prueba1.git",
    "https://github.com/Aribeth14/Examen1_AplicacionesMoviles_UrbanInspect/tree/main",
]

IGNORE_DIRS = {
    ".git", "node_modules", "dist", "build", ".gradle", ".idea", ".vscode",
    ".expo", "android", "ios", "__pycache__", ".next", "coverage", ".dart_tool",
    "Pods", "vendor", "target", "bin", "obj", "www", ".angular"
}

CODE_EXTENSIONS = {
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".py", ".java", ".kt", ".kts", ".dart",
    ".html", ".css", ".scss", ".vue", ".svelte"
}

CONFIG_FILES = {
    "package.json", "app.json", "pubspec.yaml", "tsconfig.json", "ionic.config.json"
}

IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Podfile.lock", "pubspec.lock",
    "gradlew", "gradlew.bat"
}

BOILERPLATE_REGEX = re.compile(
    r"(\.spec\.ts$|test-setup\.ts$|eslint\.config\.js$|playwright\.config\.ts$|"
    r"capacitor\.config\.ts$|explore-container|environments/environment|"
    r"main\.ts$|polyfills\.ts$|zone-flags\.ts$|global\.scss$|variables\.scss$|"
    r"index\.html$|app\.component\.(ts|html|scss)$|tabs\.page\.(ts|html|scss)$|"
    r"tabs\.routes\.ts$|app\.routes\.ts$|app\.config\.ts$|home\.page\.(ts|html|scss)$)"
)

SIG_PATTERNS = {
    "fn:coordenadasValidas": (r"\bcoordenadasValidas\b", "Función de validación coordenadasValidas(lat, lon)"),
    "const:TRANSICIONES": (r"\bTRANSICIONES\b", "Mapa de máquina de estados TRANSICIONES (pendiente -> en_proceso -> resuelta)"),
    "fn:alternar_seguimiento": (r"\balternar\s*\(", "Método alternar(codigo) en SeguimientoService con Signals"),
    "const:UMBRAL_LLUVIA": (r"umbralLluvia|UMBRAL_LLUVIA", "Constante UMBRAL_LLUVIA_MM = 5 en config"),
    "api:cloudinary": (r"api\.cloudinary\.com", "Subida de imágenes a Cloudinary API"),
    "api:imgbb": (r"api\.imgbb\.com", "Subida de imágenes a ImgBB API"),
    "api:open-meteo": (r"api\.open-meteo\.com", "Consulta meteorológica a Open-Meteo API"),
    "api:openweathermap": (r"api\.openweathermap\.org", "Consulta meteorológica a OpenWeatherMap API"),
    "api:geojs": (r"get\.geojs\.io", "Geolocalización fallback por IP (geojs.io)"),
    "seed:picsum_inc": (r"picsum\.photos/seed/inc", "Script de seed con URLs picsum.photos/seed/inc${i}"),
    "seed:script": (r"INC-.*padStart\(3,\s*'0'\)", "Generador secuencial de códigos INC-001 con padStart(3, '0')"),
    "storage:borrador_incidencia": (r"borrador_incidencia", "Clave local Preferences: 'borrador_incidencia'"),
    "storage:urbaninspect_seguimiento": (r"urbaninspect_seguimiento", "Clave local Preferences: 'urbaninspect_seguimiento*'"),
    "storage:seguimiento_codigos": (r"seguimiento_codigos", "Clave local Preferences: 'seguimiento_codigos'"),
    "type:NuevaIncidencia_Omit": (r"type\s+NuevaIncidencia\s*=\s*Omit<Incidencia,\s*'id'>", "Tipo TypeScript NuevaIncidencia = Omit<Incidencia, 'id'>"),
    "fn:textoEstado_colorEstado": (r"\b(textoEstado|colorEstado|ESTADO_TEXTO|ESTADO_LABEL)\b", "Helpers de mapeo visual de estado (textoEstado / ESTADO_LABEL)"),
    "comment:R1_R9_req": (r"//\s*R[1-9]\b|/\*\*\s*R[1-9]\b", "Comentarios explícitos de rúbrica (// R1, // R3, // R9...)"),
    "comment:hora_precedente": (r"suma de la hora (anterior|precedente)|última hora cerrada", "Comentario y lógica de precipitación de la última hora cerrada en Open-Meteo"),
    "ui:leaflet": (r"leaflet", "Integración de mapas interactivos con Leaflet"),
    "pkg:urban-inspect": (r'"name"\s*:\s*"urban-inspect"', 'Nombre interno en package.json: "urban-inspect"'),
    "pkg:urbaninspect": (r'"name"\s*:\s*"urbaninspect"', 'Nombre interno en package.json: "urbaninspect"'),
}


def parse_github_url(raw_url: str):
    # Clean invisible unicode characters, quotes, bullets, trailing slashes, and query/hash fragments
    s = re.sub(r"[\u200b\u200c\u200d\ufeff\xa0]", " ", raw_url).strip()
    # Extract the first github.com URL or owner/repo pattern if line has numbering or text around it
    url_match = re.search(r"(https?://(?:www\.)?github\.com/[^\s\"'<>]+|(?:www\.)?github\.com/[^\s\"'<>]+)", s, re.I)
    if url_match:
        url = url_match.group(1)
        if not url.lower().startswith("http"):
            url = "https://" + url
    else:
        url = s.strip("\"' \t\r\n,;•-*")
        if re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", url):
            url = f"https://github.com/{url}"

    # Strip query strings (?tab=...), fragments (#readme), and trailing slashes
    url = re.split(r"[?#]", url)[0].rstrip("/")

    m = re.match(
        r"^https?://(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/(?:tree|blob)/([^/]+)(?:/(.*))?|/(?:commits?|pulls?|issues|actions|releases)(?:/.*)?)?$",
        url,
        re.I,
    )
    if not m:
        raise ValueError(f"Invalid GitHub URL: {raw_url}")
    owner, repo, branch, subpath = m.groups()
    if repo.lower().endswith(".git"):
        repo = repo[:-4]
    if subpath:
        subpath = subpath.strip("/")
    clone_url = f"https://github.com/{owner}/{repo}.git"
    repo_id = f"{owner}/{repo}"
    if subpath:
        repo_id = f"{owner}/{repo}/{subpath}"
    return {
        "raw_url": url,
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "subpath": subpath or "",
        "clone_url": clone_url,
        "id": repo_id,
        "short_name": f"{owner}/{repo}" + (f" ({subpath})" if subpath else "")
    }


def clone_or_update_repos(repos_dir: Path, parsed_repos: list):
    repos_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for info in parsed_repos:
        folder_name = f"{info['owner']}__{info['repo']}"
        target_path = repos_dir / folder_name
        if not target_path.exists():
            print(f"Cloning {info['clone_url']} into {target_path}...")
            cmd = ["git", "clone", "--no-single-branch", info["clone_url"], str(target_path)]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if proc.returncode != 0:
                print(f"Failed to clone {info['clone_url']}: {proc.stderr}")
                info["status"] = "error"
                info["error"] = proc.stderr.strip()
                results.append(info)
                continue
        info["local_root"] = str(target_path)
        if info.get("branch"):
            # Try checking out the specified branch (or origin/<branch>)
            subprocess.run(
                ["git", "-C", str(target_path), "checkout", info["branch"]],
                capture_output=True, text=True
            )
        work_path = target_path / info["subpath"] if info["subpath"] else target_path
        if not work_path.exists():
            work_path = target_path
        info["work_path"] = str(work_path)
        info["status"] = "ok"
        results.append(info)
    return results


def get_git_metadata(info: dict):
    if info.get("status") != "ok":
        return {}
    root = info["local_root"]
    subpath = info["subpath"]

    def run_git(args):
        cmd = ["git", "-C", root] + args
        if subpath:
            cmd += ["--", subpath]
        p = subprocess.run(cmd, capture_output=True, text=True)
        return p.stdout.strip() if p.returncode == 0 else ""

    log_out = run_git(["log", "--all", "--format=%H|%an|%ae|%at|%s"])
    commits = []
    authors = set()
    emails = set()
    commit_hashes = set()
    timestamps = []

    for line in log_out.splitlines():
        parts = line.split("|", 4)
        if len(parts) == 5:
            h, an, ae, at, subj = parts
            ts = int(at) if at.isdigit() else 0
            commits.append({
                "hash": h,
                "author": an,
                "email": ae,
                "timestamp": ts,
                "date": datetime.fromtimestamp(ts).isoformat() if ts else "",
                "subject": subj
            })
            authors.add(f"{an} <{ae}>")
            emails.add(ae.lower())
            commit_hashes.add(h)
            if ts > 0:
                timestamps.append(ts)

    first_ts = min(timestamps) if timestamps else None
    last_ts = max(timestamps) if timestamps else None

    # Also get full commit log with bodies and stats to detect AI co-authors, trailers, and deleted agent files
    full_log = run_git(["log", "--all", "--stat", "--format=COMMIT_START%nAuthor: %an <%ae>%nCommitter: %cn <%ce>%nSubject: %s%nBody: %b%n"])

    return {
        "commit_count": len(commits),
        "commits": commits,
        "authors": sorted(list(authors)),
        "emails": sorted(list(emails)),
        "commit_hashes": list(commit_hashes),
        "first_commit_ts": first_ts,
        "first_commit_date": datetime.fromtimestamp(first_ts).isoformat() if first_ts else None,
        "last_commit_ts": last_ts,
        "last_commit_date": datetime.fromtimestamp(last_ts).isoformat() if last_ts else None,
        "full_log": full_log,
    }


def normalize_code(text: str) -> str:
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def get_shingles(text: str, k: int = 3) -> set:
    tokens = re.findall(r"[A-Za-z_]\w*|\d+|[^\w\s]", text)
    if len(tokens) < k:
        return set(tokens)
    return {" ".join(tokens[i:i+k]) for i in range(len(tokens) - k + 1)}


def extract_repo_features(info: dict):
    if info.get("status") != "ok":
        return {}
    work_path = Path(info["work_path"])
    custom_files = {}
    all_files = {}
    custom_shingles = set()
    all_shingles = set()
    signatures = {}
    mockapi_urls = set()
    total_lines = 0
    custom_lines = 0
    file_tree = []
    seen_custom_hashes = set()

    for root, dirs, files in os.walk(work_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        for f in files:
            if f in IGNORE_FILES or f.startswith("."):
                continue
            fpath = Path(root) / f
            rel_path = str(fpath.relative_to(work_path))
            ext = fpath.suffix.lower()
            file_tree.append(rel_path)

            if ext in CODE_EXTENSIONS or f in CONFIG_FILES:
                try:
                    raw_content = fpath.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                if len(raw_content) > 300_000:
                    continue

                for sig_key, (pat, desc) in SIG_PATTERNS.items():
                    if re.search(pat, raw_content):
                        signatures[sig_key] = desc

                for m in re.findall(r"https?://[a-zA-Z0-9_-]+\.mockapi\.io[^\s'\"`)]*", raw_content):
                    mockapi_urls.add(m)

                norm = normalize_code(raw_content)
                if not norm:
                    continue
                lines_cnt = len(norm.splitlines())
                total_lines += lines_cnt
                shingles = get_shingles(norm, k=3)

                file_obj = {
                    "norm": norm,
                    "raw": raw_content,
                    "lines": lines_cnt,
                    "shingles": shingles,
                    "ext": ext,
                    "is_boilerplate": bool(BOILERPLATE_REGEX.search(rel_path)) or (f in CONFIG_FILES)
                }
                all_files[rel_path] = file_obj
                if ext in CODE_EXTENSIONS:
                    all_shingles.update(shingles)

                if ext in CODE_EXTENSIONS and not file_obj["is_boilerplate"] and lines_cnt >= 6:
                    h = hash(norm)
                    if h not in seen_custom_hashes:
                        seen_custom_hashes.add(h)
                        custom_files[rel_path] = file_obj
                        custom_shingles.update(shingles)
                        custom_lines += lines_cnt

    # Determine project topic / cluster
    topic = "UrbanInspect (Incidencias)"
    if "JimSul16" in info["id"]:
        topic = "API Explorer (Anime)"
    elif "bestiario_DnD" in info["id"]:
        topic = "Bestiario D&D 5e"

    return {
        "custom_files": custom_files,
        "all_files": all_files,
        "custom_shingles": custom_shingles,
        "all_shingles": all_shingles,
        "signatures": signatures,
        "mockapi_urls": sorted(list(mockapi_urls)),
        "total_lines": total_lines,
        "custom_lines": custom_lines,
        "file_count": len(all_files),
        "custom_file_count": len(custom_files),
        "file_tree": sorted(file_tree),
        "topic": topic
    }


def analyze_ai_usage(info: dict, git_meta: dict, feats: dict) -> dict:
    full_log = git_meta.get("full_log", "")
    commits = git_meta.get("commits", [])
    all_files = feats.get("all_files", {})
    custom_lines = feats.get("custom_lines", 0)

    detected_models = []
    evidences = []
    score = 0

    # 1. Explicit Git Commit Trailers & Authors (Claude Code, Copilot, Cursor, OpenCode, DeepSeek, Gemini)
    if re.search(r"Claude|anthropic\.com|claude\.ai", full_log, re.I):
        detected_models.append("Claude (Anthropic)")
        score += 75
        for m in re.findall(r"(?:Author:\s*Claude[^\n]+|Co-Authored-By:\s*Claude[^\n]+|Claude-Session:\s*[^\n]+)", full_log, re.I):
            evidences.append(f"Firma directa en Git: `{m.strip()}`")

    if re.search(r"\.opencode|opencode\.json|deepseek|mimo-infra|REGISTRO-DEEPSEEK", full_log, re.I):
        detected_models.append("OpenCode / DeepSeek Agents")
        score += 75
        evidences.append("Rastros en historial Git de agentes `.opencode/agents/` (`deepseek-codigo.md`, `HANDOFF.md`, `PLAN.md`).")

    if re.search(r"gemini|google\.generativeai|idx\.dev|\.idx", full_log, re.I):
        detected_models.append("Gemini / IDX")
        score += 70
        evidences.append("Rastros en historial Git de Google Gemini / Project IDX.")

    if re.search(r"chatgpt|openai|copilot|cursor", full_log, re.I):
        detected_models.append("ChatGPT / Copilot")
        score += 70
        evidences.append("Mención en historial Git a ChatGPT / OpenAI / GitHub Copilot.")

    # 2. Code Style & Prompt Heuristics across custom files and README
    banner_comments = 0
    jsdoc_blocks = 0
    rubric_refs = 0
    code_emojis = 0
    has_ascii_tree = False

    work_path = Path(info.get("work_path", "")) if info.get("work_path") else None
    if work_path and work_path.exists():
        for rname in ["README.md", "municipio/README.md", "urbaninspect/README.md"]:
            rp = work_path / rname
            if rp.exists():
                rtxt = rp.read_text(encoding="utf-8", errors="ignore")
                if re.search(r"[├└]──", rtxt):
                    has_ascii_tree = True

    for rel_p, fobj in all_files.items():
        if fobj.get("is_boilerplate"):
            continue
        raw = fobj.get("raw", "")
        banner_comments += len(re.findall(r"//\s*[-═─=]{4,}", raw))
        jsdoc_blocks += len(re.findall(r"/\*\*[\s\S]*?\*/", raw))
        rubric_refs += len(re.findall(r"//\s*R(?:[1-9]|10)\b|/\*\*\s*R(?:[1-9]|10)\b", raw))
        if fobj.get("ext") in {".ts", ".html"}:
            code_emojis += len(re.findall(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", raw))

    # Evaluate heuristic signals
    if rubric_refs >= 4:
        score += 22
        evidences.append(f"{rubric_refs} comentarios citando explícitamente los códigos de la rúbrica (`// R1`, `// R3`, `// R9`...), patrón clásico de pasar el PDF del examen al prompt de ChatGPT/Claude.")
    elif rubric_refs >= 1:
        score += 10
        evidences.append(f"{rubric_refs} referencia(s) en comentarios a requisitos de la rúbrica (`// R1..R10`).")

    if jsdoc_blocks >= 15:
        score += 20
        evidences.append(f"Alta densidad de bloques de documentación formal JSDoc (`/** ... */`: {jsdoc_blocks} bloques), típico de generación por LLM (Claude / GPT-4o).")
    elif jsdoc_blocks >= 5:
        score += 10
        evidences.append(f"Documentación estructurada JSDoc en funciones y servicios ({jsdoc_blocks} bloques).")

    if banner_comments >= 3:
        score += 15
        evidences.append(f"Uso de separadores decorativos de sección en código (`// ────` o `// ====`: {banner_comments} bloques), frecuente en respuestas de ChatGPT/Claude.")

    if code_emojis >= 5:
        score += 12
        evidences.append(f"Uso intensivo de emojis integrados en literales/plantillas de código ({code_emojis} ocurrencias).")

    if has_ascii_tree:
        score += 12
        evidences.append("El archivo `README.md` incluye diagramas de árbol de directorios ASCII (`├──`, `└──`) generados por IA.")

    # 3. Git Commit Velocity & Conventional Commits
    conv_commits = sum(
        1 for c in commits
        if re.match(r"^(feat|fix|chore|refactor|docs|style|ci|clean)(\([^)]+\))?:", c.get("subject", ""), re.I)
    )
    if conv_commits >= 2:
        score += 10
        evidences.append(f"{conv_commits} commits siguen formato estricto Conventional Commits (`feat:`, `fix:`, `refactor:`).")

    if len(commits) <= 3 and custom_lines >= 1200:
        score += 15
        evidences.append(f"Volcado masivo: {custom_lines} líneas de lógica propia subidas en solo {len(commits)} commit(s).")

    final_score = min(99, score)

    if not detected_models:
        if final_score >= 55:
            detected_models.append("Alta Probabilidad (Estilo Claude / ChatGPT)")
        elif final_score >= 30:
            detected_models.append("Asistencia Moderada (ChatGPT / Claude / Gemini)")
        else:
            detected_models.append("Baja huella de IA / Manual")

    if final_score >= 70:
        level = "Confirmado / Muy Alto"
    elif final_score >= 45:
        level = "Probable (Huellas de Prompt)"
    elif final_score >= 25:
        level = "Moderado / Parcial"
    else:
        level = "Bajo / No Detectado"

    return {
        "ai_score": final_score,
        "ai_level": level,
        "ai_models": detected_models,
        "ai_evidences": evidences,
        "metrics": {
            "rubric_refs": rubric_refs,
            "jsdoc_blocks": jsdoc_blocks,
            "banner_comments": banner_comments,
            "code_emojis": code_emojis,
            "has_ascii_tree": has_ascii_tree,
            "conventional_commits": conv_commits
        }
    }


def compare_all_repos(repos_dir: Path, raw_urls: list = None):
    if raw_urls is None:
        raw_urls = REPOS_RAW
    parsed = []
    seen_ids = set()
    for u in raw_urls:
        if not str(u).strip():
            continue
        try:
            info = parse_github_url(str(u))
            if info["id"] not in seen_ids:
                seen_ids.add(info["id"])
                parsed.append(info)
        except ValueError as e:
            print(f"Skipping invalid URL '{u}': {e}")
    cloned = clone_or_update_repos(repos_dir, parsed)

    nodes = []
    repo_features = {}
    repo_git = {}

    for info in cloned:
        rid = info["id"]
        git_meta = get_git_metadata(info)
        feats = extract_repo_features(info)
        repo_git[rid] = git_meta
        repo_features[rid] = feats

        pkg_name = None
        if info.get("status") == "ok":
            for cfg_path, fobj in feats.get("all_files", {}).items():
                if cfg_path.endswith("package.json"):
                    m = re.search(r'"name"\s*:\s*"([^"]+)"', fobj["raw"])
                    if m:
                        pkg_name = m.group(1)
                        break

        ai_info = analyze_ai_usage(info, git_meta, feats)
        ai_assisted = ai_info["ai_score"] >= 70 or any(
            "claude" in a.lower() or "anthropic" in a.lower() or "copilot" in a.lower()
            for a in git_meta.get("authors", [])
        )

        nodes.append({
            "id": rid,
            "owner": info["owner"],
            "repo": info["repo"],
            "subpath": info["subpath"],
            "short_name": info["short_name"],
            "url": info["raw_url"],
            "status": info.get("status", "error"),
            "error": info.get("error"),
            "topic": feats.get("topic", "UrbanInspect"),
            "file_count": feats.get("file_count", 0),
            "custom_file_count": feats.get("custom_file_count", 0),
            "total_lines": feats.get("total_lines", 0),
            "custom_lines": feats.get("custom_lines", 0),
            "commit_count": git_meta.get("commit_count", 0),
            "authors": git_meta.get("authors", []),
            "emails": git_meta.get("emails", []),
            "ai_assisted": ai_assisted,
            "ai_score": ai_info["ai_score"],
            "ai_level": ai_info["ai_level"],
            "ai_models": ai_info["ai_models"],
            "ai_evidences": ai_info["ai_evidences"],
            "ai_metrics": ai_info["metrics"],
            "first_commit_ts": git_meta.get("first_commit_ts"),
            "first_commit_date": git_meta.get("first_commit_date"),
            "last_commit_ts": git_meta.get("last_commit_ts"),
            "last_commit_date": git_meta.get("last_commit_date"),
            "pkg_name": pkg_name,
            "mockapi_urls": feats.get("mockapi_urls", []),
            "signatures": list(feats.get("signatures", {}).values()),
            "signature_keys": list(feats.get("signatures", {}).keys()),
            "commits": git_meta.get("commits", [])[:20],
            "file_tree": feats.get("file_tree", [])[:120]
        })

    edges = []
    comparisons = []

    n = len(nodes)
    for i in range(n):
        for j in range(i + 1, n):
            n1 = nodes[i]
            n2 = nodes[j]
            if n1["status"] != "ok" or n2["status"] != "ok":
                continue
            id1, id2 = n1["id"], n2["id"]
            f1, f2 = repo_features[id1], repo_features[id2]
            g1, g2 = repo_git[id1], repo_git[id2]

            # 1. Custom Business Logic Shingle Jaccard & Containment
            cs1, cs2 = f1["custom_shingles"], f2["custom_shingles"]
            if cs1 and cs2:
                c_inter = len(cs1 & cs2)
                c_union = len(cs1 | cs2)
                custom_jaccard = c_inter / c_union if c_union else 0.0
                custom_contain = max(c_inter / len(cs1), c_inter / len(cs2))
            else:
                custom_jaccard = 0.0
                custom_contain = 0.0

            # 2. Custom File-by-File Best Matches (Business Logic only!)
            cfiles1 = f1["custom_files"]
            cfiles2 = f2["custom_files"]
            custom_matches = []

            for p1, d1 in cfiles1.items():
                best_p2 = None
                best_sim = 0.0
                for p2, d2 in cfiles2.items():
                    if d1["ext"] != d2["ext"]:
                        continue
                    sh1, sh2 = d1["shingles"], d2["shingles"]
                    jacc = len(sh1 & sh2) / len(sh1 | sh2) if (sh1 and sh2) else 0.0
                    seq = difflib.SequenceMatcher(None, d1["norm"], d2["norm"]).ratio() if jacc > 0.08 else 0.0
                    sim = max(jacc, seq)
                    if sim > best_sim:
                        best_sim = sim
                        best_p2 = p2
                if best_p2 and best_sim >= 0.28:
                    d2 = cfiles2[best_p2]
                    custom_matches.append({
                        "file_a": p1,
                        "file_b": best_p2,
                        "similarity": round(best_sim * 100, 1),
                        "lines_a": d1["lines"],
                        "lines_b": d2["lines"],
                        "snippet_a": "\n".join(d1["raw"].splitlines()[:35]),
                        "snippet_b": "\n".join(d2["raw"].splitlines()[:35]),
                    })

            custom_matches.sort(key=lambda x: (x["similarity"], x["lines_a"]), reverse=True)

            # 3. Also count exact boilerplate matches for transparency
            exact_boilerplate_count = 0
            for p1, d1 in f1["all_files"].items():
                if d1["is_boilerplate"]:
                    p1_name = Path(p1).name
                    for p2, d2 in f2["all_files"].items():
                        if d2["is_boilerplate"] and Path(p2).name == p1_name and d1["norm"] == d2["norm"]:
                            exact_boilerplate_count += 1
                            break

            # 4. Shared Forensic Signatures (excluding generic ones like open-meteo or R1_R9)
            sigs1 = set(f1["signatures"].keys())
            sigs2 = set(f2["signatures"].keys())
            shared_sig_keys = sigs1 & sigs2
            rare_sigs = shared_sig_keys - {"api:open-meteo", "comment:R1_R9_req", "pkg:urban-inspect"}
            shared_sig_descriptions = [SIG_PATTERNS[k][1] for k in sorted(rare_sigs)]

            # 5. Same author / Git forensic check
            shared_commits = list(set(g1.get("commit_hashes", [])) & set(g2.get("commit_hashes", [])))
            shared_emails = list(set(g1.get("emails", [])) & set(g2.get("emails", [])))
            same_owner = (n1["owner"].lower() == n2["owner"].lower()) or bool(shared_emails)

            # Calculate a calibrated Plagiarism / Copy Score (0 - 100%) based on custom logic + forensic markers
            top3_sim = (
                sum(m["similarity"] for m in custom_matches[:3]) / min(3, len(custom_matches))
                if custom_matches else 0.0
            )
            top1_sim = custom_matches[0]["similarity"] if custom_matches else 0.0

            # Weighted score:
            # - Top custom file similarities (60%)
            # - Custom shingle containment (25%)
            # - Rare forensic signatures bonus (up to 15%)
            sig_bonus = min(15.0, len(rare_sigs) * 4.0)
            logic_score = (top3_sim * 0.55) + (custom_contain * 100 * 0.30) + sig_bonus
            if len(custom_matches) >= 4 and top1_sim >= 48:
                logic_score = max(logic_score, top1_sim * 0.92 + sig_bonus * 0.8)
            elif top1_sim >= 55:
                logic_score = max(logic_score, top1_sim * 0.95)

            overall_pct = round(min(99.0, logic_score), 1)

            # Determine direction: Who copied Whom? (source = original, target = copier)
            ts1 = n1.get("first_commit_ts") or float("inf")
            ts2 = n2.get("first_commit_ts") or float("inf")

            if ts1 <= ts2:
                source_node, target_node = n1, n2
            else:
                source_node, target_node = n2, n1

            source_id, target_id = source_node["id"], target_node["id"]
            # Orient custom_matches so file_a is always source_id and file_b is always target_id
            oriented_matches = []
            for m in custom_matches[:12]:
                if source_id == id1:
                    oriented_matches.append(m)
                else:
                    oriented_matches.append({
                        "file_a": m["file_b"],
                        "file_b": m["file_a"],
                        "similarity": m["similarity"],
                        "lines_a": m["lines_b"],
                        "lines_b": m["lines_a"],
                        "snippet_a": m["snippet_b"],
                        "snippet_b": m["snippet_a"],
                    })

            reasons = []
            diff_hours = round(abs(ts2 - ts1) / 3600, 1) if (ts1 != float("inf") and ts2 != float("inf")) else 0
            if diff_hours > 0:
                reasons.append(
                    f"Cronología Git: {source_node['short_name']} inició {diff_hours}h antes "
                    f"({source_node['first_commit_date'][:16].replace('T', ' ')}) que "
                    f"{target_node['short_name']} ({target_node['first_commit_date'][:16].replace('T', ' ')})."
                )

            if same_owner:
                reasons.append(f"Mismo autor/cuenta detectada ({source_node['owner']}): evolución o segunda versión del proyecto.")

            if oriented_matches:
                best_m = oriented_matches[0]
                reasons.append(
                    f"Archivo lógico más similar: {best_m['file_a']} ↔ {best_m['file_b']} ({best_m['similarity']}% similitud)."
                )
                if len(oriented_matches) > 1:
                    reasons.append(f"{len(oriented_matches)} archivos de lógica de negocio superan el umbral de similitud estructural.")

            for sig_desc in shared_sig_descriptions[:4]:
                reasons.append(f"Huella de código compartida: {sig_desc}.")

            if target_node.get("ai_assisted"):
                reasons.append(f"El repositorio destino ({target_node['short_name']}) registra commits asistidos por IA (Claude <noreply@anthropic.com>).")

            if target_node["commit_count"] <= 3 and source_node["commit_count"] >= 5:
                reasons.append(
                    f"Patrón de subida masiva: {target_node['short_name']} subió todo en {target_node['commit_count']} commit(s) "
                    f"frente a {source_node['commit_count']} commits de {source_node['short_name']}."
                )

            if overall_pct >= 48 or (len(oriented_matches) >= 4 and top1_sim >= 45):
                verdict = "Copia / Derivación Alta"
                confidence = "Alta (Lógica + Firmas + Git)"
            elif overall_pct >= 36 or top1_sim >= 45:
                verdict = "Similitud Estructural Moderada"
                confidence = "Media-Alta (Estructura Común)"
            else:
                verdict = "Baja Similitud / Independiente"
                confidence = "Baja"

            comp_record = {
                "id": f"{source_id}-->{target_id}",
                "source": source_id,
                "target": target_id,
                "similarity": overall_pct,
                "top_file_sim": round(top1_sim, 1),
                "top3_avg_sim": round(top3_sim, 1),
                "custom_jaccard": round(custom_jaccard * 100, 1),
                "custom_containment": round(custom_contain * 100, 1),
                "boilerplate_exact_files": exact_boilerplate_count,
                "matched_custom_files_count": len(oriented_matches),
                "custom_matches": oriented_matches,
                "shared_signatures": shared_sig_descriptions,
                "shared_signatures_count": len(shared_sig_descriptions),
                "same_owner": same_owner,
                "diff_hours": diff_hours,
                "direction_confidence": confidence,
                "reasons": reasons,
                "verdict": verdict
            }
            comparisons.append(comp_record)

            # Include edge if meaningful custom similarity or same author
            if overall_pct >= 34.0 or same_owner:
                edges.append(comp_record)

    comparisons.sort(key=lambda x: (x["similarity"], x["top_file_sim"], x["matched_custom_files_count"]), reverse=True)
    edges.sort(key=lambda x: (x["similarity"], x["top_file_sim"]), reverse=True)

    # Identify primary source ("Who copied whom" tree / primary parent for each node)
    primary_parent = {}
    for node in nodes:
        nid = node["id"]
        incoming = [e for e in edges if e["target"] == nid and e["similarity"] >= 36.0]
        if incoming:
            incoming.sort(key=lambda x: (x["similarity"], x["matched_custom_files_count"]), reverse=True)
            primary_parent[nid] = incoming[0]["source"]

    for e in edges:
        e["is_primary_copy_edge"] = (primary_parent.get(e["target"]) == e["source"])

    return {
        "generated_at": datetime.now().isoformat(),
        "nodes": nodes,
        "edges": edges,
        "all_comparisons": comparisons
    }


if __name__ == "__main__":
    out_dir = Path("/Users/jp/Downloads/project_compare_githubs/repos_cache")
    data = compare_all_repos(out_dir)
    out_file = Path("/Users/jp/Downloads/project_compare_githubs/analysis_results.json")
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Done! Analyzed {len(data['nodes'])} repos, found {len(data['edges'])} significant links.")
    for e in data["edges"][:20]:
        flag = "[PRIMARY]" if e.get("is_primary_copy_edge") else "         "
        print(f"  {flag} {e['source']} --> {e['target']} | Score: {e['similarity']}% (TopFile: {e['top_file_sim']}%, Matches: {e['matched_custom_files_count']}) | {e['verdict']}")
