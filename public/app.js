let appData = null;
let currentMode = "primary"; // "primary" | "high" | "all"
let currentThreshold = 35;
let currentLayout = "chronological"; // "chronological" | "force"
let selectedNodeId = null;
let selectedEdgeId = null;

// Viewport pan & zoom state
let panX = 40;
let panY = 30;
let scale = 0.95;
let isPanning = false;
let panStartX = 0;
let panStartY = 0;

// Node coordinates map: { [id]: { x, y, vx, vy } }
const nodePositions = new Map();

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatShortDate(iso) {
  if (!iso) return "Sin fecha";
  return iso.slice(5, 16).replace("T", " ");
}

async function initApp() {
  setupTabsAndControls();
  try {
    const res = await fetch("/api/results");
    appData = await res.json();
    populateReposModal();
    computeLayout();
    renderAll();
    // Auto-select the highest similarity edge to showcase evidence immediately
    if (appData.edges && appData.edges.length > 0) {
      selectEdge(appData.edges[0]);
    }
  } catch (err) {
    console.error("Error loading results:", err);
  }
}

function setupTabsAndControls() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const views = document.querySelectorAll(".view-section");
  const toolbar = document.getElementById("graphToolbar");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      views.forEach((v) => v.classList.remove("active"));
      btn.classList.add("active");
      const targetView = btn.dataset.view;
      document.getElementById(`view-${targetView}`).classList.add("active");
      toolbar.style.display = targetView === "graph" ? "flex" : "none";
    });
  });

  const modeSelect = document.getElementById("modeSelect");
  const thresholdSlider = document.getElementById("thresholdSlider");
  const thresholdVal = document.getElementById("thresholdVal");
  const layoutSelect = document.getElementById("layoutSelect");

  modeSelect.addEventListener("change", (e) => {
    currentMode = e.target.value;
    if (currentMode === "high" && currentThreshold < 45) {
      currentThreshold = 45;
      thresholdSlider.value = "45";
      thresholdVal.textContent = "45%";
    } else if (currentMode === "primary") {
      currentThreshold = 35;
      thresholdSlider.value = "35";
      thresholdVal.textContent = "35%";
    }
    renderGraph();
  });

  thresholdSlider.addEventListener("input", (e) => {
    currentThreshold = Number(e.target.value);
    thresholdVal.textContent = `${currentThreshold}%`;
    renderGraph();
  });

  layoutSelect.addEventListener("change", (e) => {
    currentLayout = e.target.value;
    computeLayout();
    renderGraph();
  });

  document.getElementById("btnResetZoom").addEventListener("click", () => {
    panX = 40;
    panY = 30;
    scale = 0.95;
    computeLayout();
    renderGraph();
  });

  // Modals
  const codeModal = document.getElementById("codeModal");
  document.getElementById("btnCloseModal").addEventListener("click", () => codeModal.close());
  codeModal.addEventListener("click", (e) => {
    if (e.target === codeModal) codeModal.close();
  });

  const reposModal = document.getElementById("reposModal");
  document.getElementById("btnAddRepos").addEventListener("click", () => reposModal.showModal());
  document.getElementById("btnCloseReposModal").addEventListener("click", () => reposModal.close());
  document.getElementById("btnRunReanalyze").addEventListener("click", handleReanalyze);
  document.getElementById("btnClearRepos").addEventListener("click", handleClearAllRepos);
  const btnClearInModal = document.getElementById("btnClearInModal");
  if (btnClearInModal) {
    btnClearInModal.addEventListener("click", handleClearAllRepos);
  }

  setupSvgPanZoom();
}

async function handleClearAllRepos() {
  if (!confirm("¿Estás seguro de que deseas borrar todos los repositorios analizados y limpiar el grafo?")) {
    return;
  }
  try {
    const res = await fetch("/api/clear-repos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ delete_cache: true }),
    });
    const data = await res.json();
    appData = data;
    selectedNodeId = null;
    selectedEdgeId = null;
    nodePositions.clear();
    populateReposModal();
    renderAll();
    document.getElementById("inspectorTitle").textContent = "Repositorios Borrados";
    document.getElementById("inspectorSubtitle").textContent = "Usa '+ Repositorios' para analizar nuevos proyectos";
    document.getElementById("inspectorBody").innerHTML = `
      <div class="info-card">
        <p style="color:var(--text-muted)">Se han eliminado todos los repositorios del análisis. Haz clic en <strong>+ Repositorios</strong> arriba a la derecha para pegar nuevas URLs de GitHub.</p>
      </div>
    `;
    const reposModal = document.getElementById("reposModal");
    if (reposModal.open) reposModal.close();
  } catch (err) {
    alert("Error al borrar repositorios: " + err.message);
  }
}

async function handleDeleteSingleRepo(repoId) {
  if (!confirm(`¿Eliminar el repositorio "${repoId}" del grafo?`)) {
    return;
  }
  try {
    const res = await fetch("/api/delete-repo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: repoId }),
    });
    const data = await res.json();
    appData = data;
    selectedNodeId = null;
    selectedEdgeId = null;
    populateReposModal();
    computeLayout();
    renderAll();
    document.getElementById("inspectorTitle").textContent = "Repositorio Eliminado";
    document.getElementById("inspectorSubtitle").textContent = repoId;
    document.getElementById("inspectorBody").innerHTML = `
      <div class="info-card">
        <p style="color:var(--text-muted)">El repositorio <code>${escapeHtml(repoId)}</code> fue eliminado del grafo.</p>
      </div>
    `;
  } catch (err) {
    alert("Error al eliminar repositorio: " + err.message);
  }
}

function populateReposModal() {
  if (!appData || !appData.nodes) return;
  const badge = document.getElementById("repoCountBadge");
  if (badge) badge.textContent = `${appData.nodes.length} Repositorios`;
  const textarea = document.getElementById("reposTextarea");
  textarea.value = appData.nodes.map((n) => n.url).join("\n");
}

async function handleReanalyze() {
  const btn = document.getElementById("btnRunReanalyze");
  const textarea = document.getElementById("reposTextarea");
  const urls = textarea.value
    .split("\n")
    .map((u) => u.trim())
    .filter(Boolean);
  if (!urls.length) return;

  btn.disabled = true;
  btn.textContent = "Analizando repositorios...";
  try {
    const res = await fetch("/api/reanalyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ urls }),
    });
    const data = await res.json();
    if (data.nodes) {
      appData = data;
      computeLayout();
      renderAll();
      document.getElementById("reposModal").close();
    }
  } catch (err) {
    alert("Error al re-analizar: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Clonar y Re-Analizar Repositorios";
  }
}

function getFilteredEdges() {
  if (!appData || !appData.edges) return [];
  return appData.edges.filter((e) => {
    if (e.similarity < currentThreshold && !e.same_owner) return false;
    if (currentMode === "primary") {
      return e.is_primary_copy_edge || e.same_owner;
    }
    if (currentMode === "high") {
      return e.similarity >= Math.max(45, currentThreshold) || e.same_owner;
    }
    return true;
  });
}

function computeLayout() {
  if (!appData || !appData.nodes) return;
  const svg = document.getElementById("graphSvg");
  const rect = svg.getBoundingClientRect();
  const width = Math.max(rect.width || 960, 860);
  const height = Math.max(rect.height || 680, 620);

  const nodes = appData.nodes;

  if (currentLayout === "chronological") {
    // Dynamically assign columns by topological depth in primary copy graph + timestamp
    const primaryParent = new Map();
    (appData.edges || []).forEach((e) => {
      if (e.is_primary_copy_edge || (e.same_owner && e.similarity >= 35)) {
        primaryParent.set(e.target, e.source);
      }
    });

    const getDepth = (id, visited = new Set()) => {
      if (visited.has(id)) return 0;
      visited.add(id);
      const p = primaryParent.get(id);
      if (!p) return 0;
      return Math.min(4, 1 + getDepth(p, visited));
    };

    const cols = [[], [], [], [], []];
    // Sort chronologically first so rows inside each column are ordered by time
    const sortedNodes = [...nodes].sort(
      (a, b) => (a.first_commit_ts || 0) - (b.first_commit_ts || 0)
    );

    sortedNodes.forEach((n) => {
      let c = getDepth(n.id);
      if (n.topic !== "UrbanInspect (Incidencias)" && c === 0) {
        c = 4; // Put unrelated control projects on the far right column
      }
      cols[c].push(n);
    });

    // Balance columns if col 0 has too many independent nodes
    if (cols[0].length > 7) {
      const overflow = cols[0].splice(6);
      cols[1].unshift(...overflow);
    }

    const colSpacing = Math.max(220, (width - 180) / 4);
    cols.forEach((colNodes, cIdx) => {
      const virtualHeight = Math.max(height - 90, colNodes.length * 86);
      const rowSpacing = virtualHeight / Math.max(colNodes.length, 1);
      colNodes.forEach((n, rIdx) => {
        nodePositions.set(n.id, {
          x: 95 + cIdx * colSpacing,
          y: 55 + rIdx * rowSpacing + rowSpacing * 0.35,
        });
      });
    });
  } else {
    // Force-directed layout simulation (deterministic)
    nodes.forEach((n, idx) => {
      const angle = (2 * Math.PI * idx) / nodes.length;
      nodePositions.set(n.id, {
        x: width / 2 + Math.cos(angle) * 240,
        y: height / 2 + Math.sin(angle) * 200,
        vx: 0,
        vy: 0,
      });
    });

    const edges = getFilteredEdges();
    for (let iter = 0; iter < 160; iter++) {
      // Repulsion
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const p1 = nodePositions.get(nodes[i].id);
          const p2 = nodePositions.get(nodes[j].id);
          let dx = p2.x - p1.x;
          let dy = p2.y - p1.y;
          let dist = Math.hypot(dx, dy) || 1;
          if (dist < 260) {
            const force = (260 - dist) * 0.12;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            p1.x -= fx;
            p1.y -= fy;
            p2.x += fx;
            p2.y += fy;
          }
        }
      }
      // Attraction along edges
      edges.forEach((e) => {
        const p1 = nodePositions.get(e.source);
        const p2 = nodePositions.get(e.target);
        if (!p1 || !p2) return;
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        const dist = Math.hypot(dx, dy) || 1;
        const targetDist = 210;
        const force = (dist - targetDist) * 0.03;
        p1.x += (dx / dist) * force;
        p1.y += (dy / dist) * force;
        p2.x -= (dx / dist) * force;
        p2.y -= (dy / dist) * force;
      });
    }
  }
}

function getNodeCategory(node) {
  if (node.topic !== "UrbanInspect (Incidencias)") {
    return { color: "#64748b", bg: "#1e293b", label: "Otro Proyecto" };
  }
  if (node.ai_assisted) {
    return { color: "#ec4899", bg: "#3b0f2b", label: "Copia + IA (Claude)" };
  }
  // Check if node is an early original (no high incoming primary edge)
  const incomingHigh = (appData.edges || []).filter(
    (e) => e.target === node.id && e.similarity >= 45 && !e.same_owner
  );
  const outgoingHigh = (appData.edges || []).filter(
    (e) => e.source === node.id && e.similarity >= 45 && !e.same_owner
  );

  if (incomingHigh.length === 0 && outgoingHigh.length > 0) {
    return { color: "#10b981", bg: "#063729", label: "Origen / Semilla" };
  }
  if (incomingHigh.length > 0) {
    return { color: "#ef4444", bg: "#3b1219", label: "Derivado / Copia" };
  }
  return { color: "#3b82f6", bg: "#122645", label: "Independiente" };
}

function renderGraph() {
  if (!appData) return;
  const viewport = document.getElementById("graphViewport");
  viewport.setAttribute("transform", `translate(${panX}, ${panY}) scale(${scale})`);

  const edgesLayer = document.getElementById("edgesLayer");
  const labelsLayer = document.getElementById("edgeLabelsLayer");
  const nodesLayer = document.getElementById("nodesLayer");

  edgesLayer.innerHTML = "";
  labelsLayer.innerHTML = "";
  nodesLayer.innerHTML = "";

  const edges = getFilteredEdges();

  // Render Edges
  edges.forEach((edge) => {
    const p1 = nodePositions.get(edge.source);
    const p2 = nodePositions.get(edge.target);
    if (!p1 || !p2) return;

    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    const dist = Math.hypot(dx, dy) || 1;

    // Slight curve for visual clarity
    const midX = (p1.x + p2.x) / 2 - (dy / dist) * 24;
    const midY = (p1.y + p2.y) / 2 + (dx / dist) * 24;

    const isSelected = selectedEdgeId === edge.id;
    const isHigh = edge.similarity >= 48;
    const strokeColor = edge.same_owner
      ? "#8b5cf6"
      : isHigh
      ? "#ef4444"
      : "#f59e0b";
    const markerId = edge.same_owner
      ? "url(#arrow-same)"
      : isHigh
      ? "url(#arrow-high)"
      : "url(#arrow-med)";

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", `M ${p1.x} ${p1.y} Q ${midX} ${midY} ${p2.x} ${p2.y}`);
    path.setAttribute("stroke", strokeColor);
    path.setAttribute("stroke-width", isSelected ? "4.5" : isHigh ? "3.2" : "2.2");
    path.setAttribute("stroke-opacity", isSelected ? "1" : isHigh ? "0.88" : "0.62");
    if (edge.same_owner && edge.similarity < 45) {
      path.setAttribute("stroke-dasharray", "6 4");
    }
    path.setAttribute("marker-end", markerId);
    path.classList.add("edge-path");
    if (isSelected) path.classList.add("selected");

    path.addEventListener("click", (ev) => {
      ev.stopPropagation();
      selectEdge(edge);
    });
    edgesLayer.appendChild(path);

    // Pill label at curve midpoint (t = 0.5 of quadratic bezier)
    const labelX = 0.25 * p1.x + 0.5 * midX + 0.25 * p2.x;
    const labelY = 0.25 * p1.y + 0.5 * midY + 0.25 * p2.y;

    const gLabel = document.createElementNS("http://www.w3.org/2000/svg", "g");
    gLabel.setAttribute("transform", `translate(${labelX}, ${labelY})`);
    gLabel.classList.add("edge-label-pill");

    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", "-24");
    rect.setAttribute("y", "-10");
    rect.setAttribute("width", "48");
    rect.setAttribute("height", "20");
    rect.setAttribute("rx", "6");
    rect.setAttribute("fill", "#0f172a");
    rect.setAttribute("stroke", strokeColor);
    rect.setAttribute("stroke-width", "1.4");

    const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
    txt.setAttribute("text-anchor", "middle");
    txt.setAttribute("dy", "4");
    txt.setAttribute("fill", "#f8fafc");
    txt.setAttribute("font-size", "10.5");
    txt.setAttribute("font-weight", "700");
    txt.textContent = edge.same_owner && edge.similarity < 35 ? "Autor" : `${edge.similarity}%`;

    gLabel.appendChild(rect);
    gLabel.appendChild(txt);
    gLabel.addEventListener("click", (ev) => {
      ev.stopPropagation();
      selectEdge(edge);
    });
    labelsLayer.appendChild(gLabel);
  });

  // Render Nodes
  appData.nodes.forEach((node) => {
    const pos = nodePositions.get(node.id);
    if (!pos) return;
    const cat = getNodeCategory(node);
    const isSelected = selectedNodeId === node.id;

    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("transform", `translate(${pos.x}, ${pos.y})`);
    g.classList.add("node-group");
    if (isSelected) g.classList.add("selected");

    const cardW = 166;
    const cardH = 66;

    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", String(-cardW / 2));
    rect.setAttribute("y", String(-cardH / 2));
    rect.setAttribute("width", String(cardW));
    rect.setAttribute("height", String(cardH));
    rect.setAttribute("rx", "10");
    rect.setAttribute("fill", cat.bg);
    rect.setAttribute("stroke", cat.color);
    rect.setAttribute("stroke-width", isSelected ? "3.2" : "2");
    rect.classList.add("node-rect");

    // Top badge
    const badgeText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    badgeText.setAttribute("x", String(-cardW / 2 + 10));
    badgeText.setAttribute("y", String(-cardH / 2 + 15));
    badgeText.setAttribute("fill", cat.color);
    badgeText.setAttribute("font-size", "9.5");
    badgeText.setAttribute("font-weight", "700");
    badgeText.textContent = `${cat.label} • ${node.commit_count}c`;

    // Owner title
    const ownerText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    ownerText.setAttribute("x", String(-cardW / 2 + 10));
    ownerText.setAttribute("y", String(-cardH / 2 + 32));
    ownerText.setAttribute("fill", "#ffffff");
    ownerText.setAttribute("font-size", "12");
    ownerText.setAttribute("font-weight", "700");
    ownerText.textContent = node.owner.slice(0, 19);

    // Repo name + date
    const repoText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    repoText.setAttribute("x", String(-cardW / 2 + 10));
    repoText.setAttribute("y", String(-cardH / 2 + 47));
    repoText.setAttribute("fill", "#cbd5e1");
    repoText.setAttribute("font-size", "10");
    repoText.textContent = (node.subpath ? `${node.repo}/${node.subpath}` : node.repo).slice(0, 23);

    const dateText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    dateText.setAttribute("x", String(-cardW / 2 + 10));
    dateText.setAttribute("y", String(-cardH / 2 + 59));
    dateText.setAttribute("fill", "#94a3b8");
    dateText.setAttribute("font-size", "9");
    dateText.textContent = `⏱ ${formatShortDate(node.first_commit_date)}`;

    g.appendChild(rect);
    g.appendChild(badgeText);
    g.appendChild(ownerText);
    g.appendChild(repoText);
    g.appendChild(dateText);

    // Node dragging & click
    let dragMoved = false;
    g.addEventListener("pointerdown", (ev) => {
      ev.stopPropagation();
      dragMoved = false;
      const startX = ev.clientX;
      const startY = ev.clientY;
      const origX = pos.x;
      const origY = pos.y;

      const onMove = (moveEv) => {
        const dx = (moveEv.clientX - startX) / scale;
        const dy = (moveEv.clientY - startY) / scale;
        if (Math.hypot(dx, dy) > 4) dragMoved = true;
        pos.x = origX + dx;
        pos.y = origY + dy;
        renderGraph();
      };

      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        if (!dragMoved) {
          selectNode(node);
        }
      };

      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    });

    nodesLayer.appendChild(g);
  });
}

function setupSvgPanZoom() {
  const svg = document.getElementById("graphSvg");
  svg.addEventListener("pointerdown", (ev) => {
    if (ev.target !== svg && ev.target.tagName !== "g") return;
    isPanning = true;
    panStartX = ev.clientX - panX;
    panStartY = ev.clientY - panY;
  });

  window.addEventListener("pointermove", (ev) => {
    if (!isPanning) return;
    panX = ev.clientX - panStartX;
    panY = ev.clientY - panStartY;
    const viewport = document.getElementById("graphViewport");
    viewport.setAttribute("transform", `translate(${panX}, ${panY}) scale(${scale})`);
  });

  window.addEventListener("pointerup", () => {
    isPanning = false;
  });

  svg.addEventListener(
    "wheel",
    (ev) => {
      ev.preventDefault();
      const factor = ev.deltaY < 0 ? 1.08 : 0.92;
      scale = Math.min(2.2, Math.max(0.45, scale * factor));
      const viewport = document.getElementById("graphViewport");
      viewport.setAttribute("transform", `translate(${panX}, ${panY}) scale(${scale})`);
    },
    { passive: false }
  );
}

function selectEdge(edge) {
  selectedEdgeId = edge.id;
  selectedNodeId = null;
  renderGraph();

  const titleEl = document.getElementById("inspectorTitle");
  const subEl = document.getElementById("inspectorSubtitle");
  const bodyEl = document.getElementById("inspectorBody");

  titleEl.textContent = `Evidencia de Copia (${edge.similarity}%)`;
  subEl.textContent = `${edge.source} → ${edge.target}`;

  const matchesHtml = (edge.custom_matches || [])
    .map(
      (m, idx) => `
      <div class="file-match-item" data-match-idx="${idx}">
        <div class="file-match-top">
          <span>📄 ${escapeHtml(m.file_a.split("/").pop())} ↔ ${escapeHtml(m.file_b.split("/").pop())}</span>
          <span class="sim-badge ${m.similarity >= 50 ? "sim-high" : "sim-med"}">${m.similarity}%</span>
        </div>
        <div style="font-size:0.72rem; color:var(--text-muted)">
          <div>Origen: <code>${escapeHtml(m.file_a)}</code> (${m.lines_a} líns)</div>
          <div>Copia: <code>${escapeHtml(m.file_b)}</code> (${m.lines_b} líns)</div>
          <div style="color:var(--accent-color); margin-top:4px; font-weight:600">🔍 Clic para ver código lado a lado</div>
        </div>
      </div>
    `
    )
    .join("");

  const reasonsHtml = (edge.reasons || [])
    .map((r) => `<li>${escapeHtml(r)}</li>`)
    .join("");

  bodyEl.innerHTML = `
    <div class="Copy-direction-banner">
      <div class="flow-row">
        <span class="flow-tag tag-source">Autor / Origen</span>
        <span>${escapeHtml(edge.source)}</span>
      </div>
      <div style="text-align:center; font-size:0.8rem; color:#f87171; font-weight:700">
        ⬇ COPIADO / DERIVADO POR (${edge.diff_hours}h después) ⬇
      </div>
      <div class="flow-row">
        <span class="flow-tag ${edge.same_owner ? "tag-same" : "tag-copier"}">${
    edge.same_owner ? "Mismo Autor (v2)" : "Copió / Derivó"
  }</span>
        <span>${escapeHtml(edge.target)}</span>
      </div>
    </div>

    <div class="info-card">
      <h3>
        <span>Veredicto Forense</span>
        <span class="sim-badge ${edge.similarity >= 48 ? "sim-high" : "sim-med"}">${escapeHtml(edge.verdict)}</span>
      </h3>
      <ul class="reason-list">
        ${reasonsHtml}
      </ul>
    </div>

    <div class="info-card">
      <h3>
        <span>Archivos de Lógica Coincidentes (${edge.matched_custom_files_count})</span>
      </h3>
      ${matchesHtml || "<p style='color:var(--text-muted)'>Relación detectada por autoría / configuración.</p>"}
    </div>

    <div class="info-card">
      <h3>Métricas Técnicas</h3>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; font-size:0.76rem">
        <div>Top Archivo Lógico: <strong>${edge.top_file_sim}%</strong></div>
        <div>Contención Shingles: <strong>${edge.custom_containment}%</strong></div>
        <div>Firmas Raras Comunes: <strong>${edge.shared_signatures_count}</strong></div>
        <div>Plantilla Ionic Idéntica: <strong>${edge.boilerplate_exact_files} arch.</strong></div>
      </div>
    </div>
  `;

  bodyEl.querySelectorAll(".file-match-item").forEach((el) => {
    el.addEventListener("click", () => {
      const idx = Number(el.dataset.matchIdx);
      openCodeDiffModal(edge, edge.custom_matches[idx]);
    });
  });
}

function selectNode(node) {
  selectedNodeId = node.id;
  selectedEdgeId = null;
  renderGraph();

  const titleEl = document.getElementById("inspectorTitle");
  const subEl = document.getElementById("inspectorSubtitle");
  const bodyEl = document.getElementById("inspectorBody");

  titleEl.textContent = node.short_name;
  subEl.textContent = `Tema: ${node.topic}`;

  const incoming = (appData.edges || []).filter((e) => e.target === node.id);
  const outgoing = (appData.edges || []).filter((e) => e.source === node.id);

  const inHtml = incoming
    .map(
      (e) => `
      <div class="file-match-item" data-edge-id="${escapeHtml(e.id)}">
        <div class="file-match-top">
          <span>⬅ Copió/derivó de: <strong>${escapeHtml(e.source)}</strong></span>
          <span class="sim-badge sim-high">${e.similarity}%</span>
        </div>
        <div style="font-size:0.72rem; color:var(--text-muted)">${escapeHtml(e.verdict)} (${e.diff_hours}h después)</div>
      </div>
    `
    )
    .join("");

  const outHtml = outgoing
    .map(
      (e) => `
      <div class="file-match-item" data-edge-id="${escapeHtml(e.id)}">
        <div class="file-match-top">
          <span>➡ Fue copiado por: <strong>${escapeHtml(e.target)}</strong></span>
          <span class="sim-badge sim-med">${e.similarity}%</span>
        </div>
        <div style="font-size:0.72rem; color:var(--text-muted)">${escapeHtml(e.verdict)} (${e.diff_hours}h antes)</div>
      </div>
    `
    )
    .join("");

  const commitsHtml = (node.commits || [])
    .slice(0, 8)
    .map(
      (c) => `
      <div style="padding:0.35rem 0; border-bottom:1px solid var(--border-color); font-size:0.74rem">
        <div style="font-weight:600">${escapeHtml(c.subject)}</div>
        <div style="color:var(--text-muted)">${escapeHtml(c.author)} • ${formatShortDate(c.date)}</div>
      </div>
    `
    )
    .join("");

  bodyEl.innerHTML = `
    <div class="info-card">
      <h3>
        <span>Resumen del Repositorio</span>
        <div style="display:flex; align-items:center; gap:0.55rem">
          <a href="${escapeHtml(node.url)}" target="_blank" rel="noopener" style="color:var(--accent-color); font-size:0.76rem">Abrir GitHub ↗</a>
          <button type="button" class="btn-danger" id="btnDeleteThisNode" style="padding:0.2rem 0.5rem; font-size:0.72rem">🗑 Quitar</button>
        </div>
      </h3>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.45rem; font-size:0.78rem">
        <div>Primer Commit: <strong>${formatShortDate(node.first_commit_date)}</strong></div>
        <div>Total Commits: <strong>${node.commit_count}</strong></div>
        <div>Archivos Propios: <strong>${node.custom_file_count}</strong> (${node.custom_lines} líns)</div>
        <div>package.json: <code>${escapeHtml(node.pkg_name || "N/A")}</code></div>
      </div>
      <div style="margin-top:0.5rem; font-size:0.75rem; color:var(--text-muted)">
        <strong>Autores Git:</strong> ${escapeHtml((node.authors || []).join(", "))}
      </div>
      ${
        node.mockapi_urls && node.mockapi_urls.length
          ? `<div style="margin-top:0.4rem; font-size:0.74rem; word-break:break-all"><strong>MockAPI:</strong> <code>${escapeHtml(
              node.mockapi_urls[0]
            )}</code></div>`
          : ""
      }
    </div>

    <div class="info-card">
      <h3>¿De quién copió? (${incoming.length})</h3>
      ${inHtml || "<p style='color:#10b981; font-size:0.78rem'>✓ No se detecta copia entrante (Repositorio Original / Independiente).</p>"}
    </div>

    <div class="info-card">
      <h3>¿Quiénes le copiaron? (${outgoing.length})</h3>
      ${outHtml || "<p style='color:var(--text-muted); font-size:0.78rem'>Ningún repositorio posterior deriva directamente de este.</p>"}
    </div>

    <div class="info-card">
      <h3>Huellas Digitales en el Código (${(node.signatures || []).length})</h3>
      <ul class="reason-list" style="font-size:0.75rem">
        ${(node.signatures || []).map((s) => `<li>${escapeHtml(s)}</li>`).join("")}
      </ul>
    </div>

    <div class="info-card">
      <h3>Historial de Commits (${node.commit_count})</h3>
      ${commitsHtml}
    </div>
  `;

  const btnDel = bodyEl.querySelector("#btnDeleteThisNode");
  if (btnDel) {
    btnDel.addEventListener("click", () => handleDeleteSingleRepo(node.id));
  }

  bodyEl.querySelectorAll("[data-edge-id]").forEach((el) => {
    el.addEventListener("click", () => {
      const eid = el.dataset.edgeId;
      const found = appData.edges.find((e) => e.id === eid);
      if (found) selectEdge(found);
    });
  });
}

function openCodeDiffModal(edge, match) {
  const modal = document.getElementById("codeModal");
  document.getElementById("modalTitle").textContent = `${match.file_a} ↔ ${match.file_b} (${match.similarity}% Similitud)`;
  document.getElementById("modalSubtitle").textContent = `Origen (${edge.source}) → Copiado/Derivado por (${edge.target})`;

  const body = document.getElementById("modalBody");
  body.innerHTML = `
    <div class="code-split">
      <div class="code-pane">
        <div class="code-pane-header">
          <span>🟢 ORIGEN: ${escapeHtml(edge.source)} — ${escapeHtml(match.file_a)}</span>
          <span>${match.lines_a} líneas</span>
        </div>
        <pre><code>${escapeHtml(match.snippet_a)}</code></pre>
      </div>
      <div class="code-pane">
        <div class="code-pane-header">
          <span>🔴 DERIVADO: ${escapeHtml(edge.target)} — ${escapeHtml(match.file_b)}</span>
          <span>${match.lines_b} líneas</span>
        </div>
        <pre><code>${escapeHtml(match.snippet_b)}</code></pre>
      </div>
    </div>
  `;
  modal.showModal();
}

function renderMatrix() {
  if (!appData) return;
  const container = document.getElementById("matrixContainer");
  const nodes = appData.nodes;
  const compMap = new Map();
  (appData.all_comparisons || []).forEach((c) => {
    compMap.set(`${c.source}|${c.target}`, c);
    compMap.set(`${c.target}|${c.source}`, c);
  });

  let html = `<table class="matrix-table"><thead><tr><th>Repositorio</th>`;
  nodes.forEach((n, idx) => {
    html += `<th title="${escapeHtml(n.short_name)}">${idx + 1}. ${escapeHtml(n.owner.slice(0, 8))}</th>`;
  });
  html += `</tr></thead><tbody>`;

  nodes.forEach((rNode, rIdx) => {
    html += `<tr><th class="row-header">${rIdx + 1}. ${escapeHtml(rNode.short_name)}</th>`;
    nodes.forEach((cNode) => {
      if (rNode.id === cNode.id) {
        html += `<td style="background:var(--bg-elevated); color:var(--text-muted)">—</td>`;
      } else {
        const comp = compMap.get(`${rNode.id}|${cNode.id}`);
        const sim = comp ? comp.similarity : 0;
        let bg = "transparent";
        let color = "var(--text-muted)";
        if (sim >= 50) {
          bg = "rgba(239, 68, 68, 0.32)";
          color = "#fca5a5";
        } else if (sim >= 38) {
          bg = "rgba(245, 158, 11, 0.25)";
          color = "#fde68a";
        } else if (sim >= 28) {
          bg = "rgba(59, 130, 246, 0.15)";
          color = "#93c5fd";
        }
        html += `<td class="matrix-cell" data-a="${escapeHtml(rNode.id)}" data-b="${escapeHtml(
          cNode.id
        )}" style="background:${bg}; color:${color}">${sim}%</td>`;
      }
    });
    html += `</tr>`;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;

  container.querySelectorAll(".matrix-cell").forEach((cell) => {
    cell.addEventListener("click", () => {
      const a = cell.dataset.a;
      const b = cell.dataset.b;
      const comp = compMap.get(`${a}|${b}`);
      if (comp) {
        selectEdge(comp);
        if (comp.custom_matches && comp.custom_matches.length > 0) {
          openCodeDiffModal(comp, comp.custom_matches[0]);
        }
      }
    });
  });
}

function renderTimeline() {
  if (!appData) return;
  const container = document.getElementById("timelineContainer");
  const sorted = [...appData.nodes].sort(
    (a, b) => (a.first_commit_ts || 0) - (b.first_commit_ts || 0)
  );

  // Filter UrbanInspect timeframe for proportional bar scaling (Oct 27 - Oct 29)
  const urbanNodes = sorted.filter((n) => n.topic === "UrbanInspect (Incidencias)");
  const minTs = Math.min(...urbanNodes.map((n) => n.first_commit_ts || Infinity));
  const maxTs = Math.max(...urbanNodes.map((n) => n.last_commit_ts || 0));
  const span = Math.max(maxTs - minTs, 3600);

  container.innerHTML = sorted
    .map((n, idx) => {
      const cat = getNodeCategory(n);
      let leftPct = 0;
      let widthPct = 100;
      if (n.topic === "UrbanInspect (Incidencias)" && n.first_commit_ts) {
        leftPct = Math.max(0, Math.min(92, ((n.first_commit_ts - minTs) / span) * 100));
        const endPct = Math.max(leftPct + 3, Math.min(100, ((n.last_commit_ts - minTs) / span) * 100));
        widthPct = endPct - leftPct;
      }
      return `
        <div class="timeline-row" data-node-id="${escapeHtml(n.id)}">
          <div>
            <div style="font-weight:700; font-size:0.84rem">#${idx + 1} ${escapeHtml(n.short_name)}</div>
            <div style="font-size:0.74rem; color:var(--text-muted)">Inicio: ${formatShortDate(
              n.first_commit_date
            )}</div>
          </div>
          <div class="timeline-bar-track">
            <div class="timeline-bar-fill" style="inset-inline-start:${leftPct}%; inline-size:${widthPct}%; background:${
        cat.color
      }"></div>
          </div>
          <div style="text-align:end; font-size:0.78rem">
            <div><strong>${n.commit_count}</strong> commit(s)</div>
            <div style="color:${cat.color}; font-size:0.72rem; font-weight:600">${escapeHtml(cat.label)}</div>
          </div>
        </div>
      `;
    })
    .join("");

  container.querySelectorAll(".timeline-row").forEach((row) => {
    row.addEventListener("click", () => {
      const node = appData.nodes.find((n) => n.id === row.dataset.nodeId);
      if (node) selectNode(node);
    });
  });
}

function renderReport() {
  if (!appData) return;
  const container = document.getElementById("reportContainer");
  const primaryEdges = appData.edges.filter((e) => e.is_primary_copy_edge || e.same_owner);

  const cardsHtml = primaryEdges
    .map(
      (e) => `
      <div class="info-card" style="cursor:pointer" data-report-edge="${escapeHtml(e.id)}">
        <h3>
          <span>🔴 ${escapeHtml(e.target.split("/")[0])} ← copió de ${escapeHtml(e.source.split("/")[0])}</span>
          <span class="sim-badge sim-high">${e.similarity}%</span>
        </h3>
        <p style="font-size:0.78rem; color:var(--text-muted); margin-bottom:0.5rem">
          <strong>Origen:</strong> <code>${escapeHtml(e.source)}</code><br>
          <strong>Derivado:</strong> <code>${escapeHtml(e.target)}</code>
        </p>
        <ul class="reason-list" style="font-size:0.76rem">
          ${(e.reasons || []).slice(0, 4).map((r) => `<li>${escapeHtml(r)}</li>`).join("")}
        </ul>
      </div>
    `
    )
    .join("");

  container.innerHTML = cardsHtml;
  container.querySelectorAll("[data-report-edge]").forEach((card) => {
    card.addEventListener("click", () => {
      const edge = appData.edges.find((e) => e.id === card.dataset.reportEdge);
      if (edge) {
        selectEdge(edge);
        if (edge.custom_matches && edge.custom_matches.length > 0) {
          openCodeDiffModal(edge, edge.custom_matches[0]);
        }
      }
    });
  });
}

function renderAll() {
  renderGraph();
  renderMatrix();
  renderTimeline();
  renderReport();
}

window.addEventListener("resize", () => {
  computeLayout();
  renderGraph();
});

initApp();

