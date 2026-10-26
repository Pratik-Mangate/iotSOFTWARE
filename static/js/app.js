/* ================================================================
   app.js — Skin Monitor Dashboard client-side logic
   ================================================================ */

document.addEventListener("DOMContentLoaded", () => {
    initNavToggle();
    initDropZone();
    initAnalyzeForm();
    syncCurrentResult();
    hydrateHistoryPage();
    restoreClientReport();
    hydrateDashboard();
});


/* ── Mobile navigation toggle ──────────────────────────────────── */
function initNavToggle() {
    const toggle = document.getElementById("nav-toggle");
    const links  = document.getElementById("nav-links");
    if (!toggle || !links) return;

    toggle.addEventListener("click", () => {
        links.classList.toggle("open");
    });

    // Close menu on outside click
    document.addEventListener("click", (e) => {
        if (!toggle.contains(e.target) && !links.contains(e.target)) {
            links.classList.remove("open");
        }
    });
}


/* ── Drag-and-drop upload zone ─────────────────────────────────── */
function initDropZone() {
    const dropZone  = document.getElementById("drop-zone");
    const fileInput = document.getElementById("skin-image-input");
    if (!dropZone || !fileInput) return;

    // Click on drop zone triggers file dialog
    dropZone.addEventListener("click", () => {
        fileInput.click();
    });

    // Prevent default drag behaviours
    ["dragenter", "dragover", "dragleave", "drop"].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // Visual feedback
    ["dragenter", "dragover"].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.add("drag-over"));
    });
    ["dragleave", "drop"].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.remove("drag-over"));
    });

    // Handle dropped files
    dropZone.addEventListener("drop", (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            showPreview(files[0]);
        }
    });

    // Handle file input change (choose file / gallery)
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            const cam = document.getElementById("camera-input");
            if (cam) cam.value = ""; // clear other input
            showPreview(fileInput.files[0]);
        }
    });

    // Also listen on the camera input if present
    const cameraInput = document.getElementById("camera-input");
    if (cameraInput) {
        cameraInput.addEventListener("change", () => {
            if (cameraInput.files.length > 0) {
                fileInput.value = ""; // clear gallery input so camera is used
                // Try sync if supported, otherwise camera_image name attribute handles it
                try {
                    const dt = new DataTransfer();
                    dt.items.add(cameraInput.files[0]);
                    fileInput.files = dt.files;
                } catch (e) {
                    // Fallback: camera_image input itself will be submitted
                }
                showPreview(cameraInput.files[0]);
            }
        });
    }
}


/* ── Image preview ─────────────────────────────────────────────── */
function showPreview(file) {
    const container  = document.getElementById("preview-container");
    const imgEl      = document.getElementById("preview-image");
    const nameEl     = document.getElementById("preview-filename");
    const analyzeBtn = document.getElementById("analyze-btn");

    if (!container || !imgEl) return;

    // Validate on client side
    const allowed = ["image/jpeg", "image/png", "image/webp"];
    if (!allowed.includes(file.type)) {
        alert("Please select a JPG, PNG, or WebP image.");
        return;
    }

    const maxMB = 10;
    if (file.size > maxMB * 1024 * 1024) {
        alert(`Image is too large. Maximum size is ${maxMB} MB.`);
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        imgEl.src = e.target.result;
        if (nameEl) nameEl.textContent = file.name;
        container.classList.add("visible");
        if (analyzeBtn) analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}


/* ── Form submission with loader ───────────────────────────────── */
function initAnalyzeForm() {
    const form    = document.getElementById("analyze-form");
    const loader  = document.getElementById("loader-overlay");
    if (!form) return;

    form.addEventListener("submit", (e) => {
        const fileInput = document.getElementById("skin-image-input");
        const cameraInput = document.getElementById("camera-input");
        const hasFile = (fileInput && fileInput.files && fileInput.files.length > 0) ||
                        (cameraInput && cameraInput.files && cameraInput.files.length > 0);

        if (!hasFile) {
            e.preventDefault();
            alert("Please select or capture an image first.");
            return;
        }

        // Show loading overlay
        if (loader) loader.classList.add("active");
    });
}


/* ── History clear confirmation ────────────────────────────────── */
function confirmClear() {
    return confirm(
        "Are you sure you want to clear all history and uploaded images? This action cannot be undone."
    );
}


/* ── Clear preview selection ───────────────────────────────────── */
function clearPreview() {
    const container   = document.getElementById("preview-container");
    const fileInput   = document.getElementById("skin-image-input");
    const cameraInput = document.getElementById("camera-input");
    const imgEl       = document.getElementById("preview-image");
    const nameEl      = document.getElementById("preview-filename");
    const analyzeBtn  = document.getElementById("analyze-btn");

    if (fileInput) fileInput.value = "";
    if (cameraInput) cameraInput.value = "";
    if (imgEl) imgEl.src = "";
    if (nameEl) nameEl.textContent = "";
    if (container) container.classList.remove("visible");
    if (analyzeBtn) analyzeBtn.disabled = true;
}


/* ── Evaluation Case Registry & Persistent Hydration System ────── */
const REGISTRY_STORAGE_KEY = "dermaScan_registry";

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function getStoredRegistry() {
    try {
        const raw = localStorage.getItem(REGISTRY_STORAGE_KEY);
        if (!raw) return [];
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
        console.warn("[DermaScan] Registry read exception:", e);
        return [];
    }
}

function saveRecordToRegistry(rec) {
    if (!rec || !rec.predicted) return;
    try {
        let list = getStoredRegistry();
        const existingIdx = list.findIndex(item => {
            if (rec.id && item.id && String(item.id) === String(rec.id)) return true;
            if (rec.timestamp && item.timestamp === rec.timestamp && item.predicted === rec.predicted) return true;
            return false;
        });

        if (existingIdx >= 0) {
            list[existingIdx] = Object.assign({}, list[existingIdx], rec);
        } else {
            // Assign client-side synthetic ID if none provided
            if (!rec.id) rec.id = list.length > 0 ? (Number(list[0].id) || 0) + 1 : 1;
            list.unshift(rec);
        }

        // Cap at 50 records to stay safely within localStorage limits
        if (list.length > 50) list = list.slice(0, 50);
        localStorage.setItem(REGISTRY_STORAGE_KEY, JSON.stringify(list));
    } catch (e) {
        console.warn("[DermaScan] Registry write exception:", e);
    }
}

/* Sync current evaluated diagnostic report into browser storage */
function syncCurrentResult() {
    const payloadEl = document.getElementById("current-eval-payload");
    if (!payloadEl) return;
    try {
        const data = JSON.parse(payloadEl.textContent);
        if (data && data.predicted) {
            saveRecordToRegistry(data);
        }
    } catch (e) {
        console.warn("[DermaScan] Current result sync error:", e);
    }
}

/* Hydrate the Evaluation Case Registry page (/history) */
function hydrateHistoryPage() {
    const tableWrap = document.getElementById("history-table-container");
    const emptyState = document.getElementById("history-empty-state");
    const tbody = document.getElementById("history-table-body");
    const cardsContainer = document.getElementById("history-cards-container");
    const countHeading = document.getElementById("history-count-heading");
    const clearForm = document.getElementById("clear-history-form");

    if (!tbody && !emptyState) return;

    // Attach clear history listener
    if (clearForm) {
        clearForm.addEventListener("submit", () => {
            try {
                localStorage.removeItem(REGISTRY_STORAGE_KEY);
            } catch (e) {}
        });
    }

    // Merge any server records from data island into local storage
    const serverScript = document.getElementById("server-records-payload");
    if (serverScript) {
        try {
            const serverRecs = JSON.parse(serverScript.textContent);
            if (Array.isArray(serverRecs)) {
                serverRecs.forEach(sr => {
                    if (sr && sr.predicted) saveRecordToRegistry(sr);
                });
            }
        } catch (e) {
            console.warn("[DermaScan] Server records sync error:", e);
        }
    }

    const stored = getStoredRegistry();

    if (stored.length === 0) {
        if (tableWrap) tableWrap.style.display = "none";
        if (emptyState) emptyState.style.display = "";
        return;
    }

    // Show table, hide empty state
    if (emptyState) emptyState.style.display = "none";
    if (tableWrap) tableWrap.style.display = "";
    if (countHeading) countHeading.textContent = `Archived Clinical Evaluations (${stored.length})`;

    // Rebuild desktop table rows
    if (tbody) {
        tbody.innerHTML = stored.map(r => {
            const pct = r.confidence ? `${(r.confidence * 100).toFixed(1)}%` : "N/A";
            const imgSrc = r.image_data || (r.image_file ? `/uploads/${encodeURIComponent(r.image_file)}` : "");
            return `
                <tr data-record-id="${escapeHtml(String(r.id))}">
                    <td class="case-id">#${escapeHtml(String(r.id))}</td>
                    <td>
                        <img class="case-thumb" src="${imgSrc}" alt="Case #${escapeHtml(String(r.id))}" loading="lazy"
                             onerror="this.style.opacity='0.4';">
                    </td>
                    <td>
                        <span class="condition-pill">${escapeHtml(r.predicted)}</span>
                    </td>
                    <td>
                        <span class="score-badge">${pct}</span>
                    </td>
                    <td class="timestamp-text">${escapeHtml(r.timestamp || "")}</td>
                    <td style="text-align: right;">
                        <a href="/result/${encodeURIComponent(String(r.id))}" class="btn btn-outline btn-sm" style="padding: 4px 10px; font-size: var(--fs-xs);">
                            View &amp; Rx &rarr;
                        </a>
                    </td>
                </tr>
            `;
        }).join("");
    }

    // Rebuild mobile cards
    if (cardsContainer) {
        cardsContainer.innerHTML = stored.map(r => {
            const pct = r.confidence ? `${(r.confidence * 100).toFixed(1)}%` : "N/A";
            const imgSrc = r.image_data || (r.image_file ? `/uploads/${encodeURIComponent(r.image_file)}` : "");
            return `
                <div class="history-card-row" data-record-id="${escapeHtml(String(r.id))}">
                    <img class="case-thumb" src="${imgSrc}" alt="Case #${escapeHtml(String(r.id))}" loading="lazy"
                         onerror="this.style.opacity='0.4';">
                    <div style="flex:1; min-width:0;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="condition-pill">${escapeHtml(r.predicted)}</span>
                            <span class="score-badge">${pct}</span>
                        </div>
                        <div class="timestamp-text" style="margin-top:4px;">Case #${escapeHtml(String(r.id))} &bull; ${escapeHtml(r.timestamp || "")}</div>
                        <div style="margin-top: 6px;">
                            <a href="/result/${encodeURIComponent(String(r.id))}" style="font-size: var(--fs-xs); color: var(--clr-accent); font-weight: 600; text-decoration: none;">
                                View Assessment &amp; Rx Protocol &rarr;
                            </a>
                        </div>
                    </div>
                </div>
            `;
        }).join("");
    }
}

/* Restore diagnostic report dynamically when container rotates on Vercel */
function restoreClientReport() {
    const restoreArea = document.getElementById("client-restoration-area");
    if (!restoreArea) return;

    const lookupId = restoreArea.getAttribute("data-lookup-id");
    const stored = getStoredRegistry();

    // Match by ID or take most recent if user asked for latest
    let record = stored.find(r => String(r.id) === String(lookupId));
    if (!record && stored.length > 0) {
        if (lookupId === "1" || lookupId === "latest") {
            record = stored[0];
        }
    }

    if (!record) {
        restoreArea.innerHTML = `
            <div class="card fade-in" style="text-align:center; padding:var(--sp-12) var(--sp-6); margin-top:var(--sp-6);">
                <div style="width:48px; height:48px; border-radius:50%; background-color:var(--clr-surface-muted); color:var(--clr-text-muted); display:flex; align-items:center; justify-content:center; margin:0 auto var(--sp-4); border:1px solid var(--clr-border);">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                </div>
                <h2>Case #${escapeHtml(lookupId)} Not Found In Local Browser Registry</h2>
                <p style="color:var(--clr-text-muted); max-width:520px; margin:var(--sp-2) auto var(--sp-6);">
                    This case record was logged in a different browsing session or device. You can review all cases recorded in this browser inside the Evaluation Case Registry.
                </p>
                <div class="btn-group centered">
                    <a href="/history" class="btn btn-primary">Open Evaluation Case Registry</a>
                    <a href="/analyze" class="btn btn-outline">Start New Analysis</a>
                </div>
            </div>
        `;
        return;
    }

    // Get clinical protocols dictionary
    let allProtocols = {};
    const protoScript = document.getElementById("all-clinical-protocols");
    if (protoScript) {
        try { allProtocols = JSON.parse(protoScript.textContent); } catch (e) {}
    }

    const proto = record.treatment_protocol || allProtocols[record.predicted] || null;
    const pct = (Number(record.confidence) * 100).toFixed(1);
    const fillClass = pct >= 70 ? "fill-high" : (pct >= 40 ? "fill-medium" : "fill-low");
    const certaintyText = pct >= 70
        ? `<strong>High model certainty:</strong> Features closely match training distributions for ${escapeHtml(record.predicted)}.`
        : (pct >= 40
            ? `<strong>Moderate model certainty:</strong> Image displays overlapping features; review differential candidates below.`
            : `<strong>Low model certainty:</strong> Substantial uncertainty observed. Consider acquiring an image with improved lighting and focus.`);

    // Top 3 differential items
    let top3Html = "";
    if (record.top3 && record.top3.length > 1) {
        const items = record.top3.map(item => {
            const itemPct = (Number(item.confidence) * 100).toFixed(1);
            return `
                <li class="differential-item">
                    <div class="differential-row">
                        <span>${escapeHtml(item.class)}</span>
                        <span style="font-weight:700;">${itemPct}%</span>
                    </div>
                    <div class="differential-bar">
                        <div class="differential-fill" style="width: ${itemPct}%;"></div>
                    </div>
                </li>
            `;
        }).join("");

        top3Html = `
            <div class="differential-card">
                <h3>Differential Diagnosis Ranking (Top-3)</h3>
                <ul class="differential-list">
                    ${items}
                </ul>
            </div>
        `;
    }

    // Treatment Protocol & Prescription Guidance Section
    let protoHtml = "";
    if (proto) {
        const rxCards = (proto.rx_first_line || []).map(rx => `
            <div class="rx-card">
                <div class="rx-card-top">
                    <div class="rx-med-name">${escapeHtml(rx.medication)}</div>
                    <span class="rx-class-tag">${escapeHtml(rx.class_type)}</span>
                </div>
                <div class="rx-dosage-box">
                    <strong>Dosage &amp; Regimen:</strong> ${escapeHtml(rx.dosage)}
                </div>
                ${rx.note ? `
                <div class="rx-note-text">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                    <span>${escapeHtml(rx.note)}</span>
                </div>` : ""}
            </div>
        `).join("");

        let adjunctBlock = "";
        if (proto.adjunct_otc && proto.adjunct_otc.length > 0) {
            const adjCards = proto.adjunct_otc.map(adj => `
                <div class="adjunct-card">
                    <div class="adjunct-name">${escapeHtml(adj.medication)}</div>
                    <div class="adjunct-purpose">${escapeHtml(adj.purpose)}</div>
                    <div class="adjunct-dosage"><strong>Regimen:</strong> ${escapeHtml(adj.dosage)}</div>
                </div>
            `).join("");

            adjunctBlock = `
                <div class="protocol-sub-block">
                    <div class="block-title-row">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M2 12h20"/></svg>
                        <h3>Adjunct &amp; Symptomatic Measures</h3>
                    </div>
                    <div class="adjunct-grid">
                        ${adjCards}
                    </div>
                </div>
            `;
        }

        const measures = (proto.non_pharma_measures || []).map(m => `
            <li class="measure-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--clr-accent)" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                <span>${escapeHtml(m)}</span>
            </li>
        `).join("");

        const contraList = (proto.contraindications || []).map(c => `<li>${escapeHtml(c)}</li>`).join("");
        const referralList = (proto.urgent_referral || []).map(r => `<li>${escapeHtml(r)}</li>`).join("");

        protoHtml = `
            <section class="card protocol-section fade-in">
                <div class="protocol-header">
                    <div class="protocol-header-title">
                        <div class="protocol-icon-box">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
                                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
                            </svg>
                        </div>
                        <div>
                            <div class="protocol-badge-row">
                                <span class="protocol-badge">${escapeHtml(proto.category)}</span>
                                <span class="rx-pill">Clinical Rx Protocol</span>
                            </div>
                            <h2 class="protocol-title">Treatment Protocol &amp; Prescription Guidance: ${escapeHtml(proto.title)}</h2>
                        </div>
                    </div>
                </div>

                <p class="protocol-description">${escapeHtml(proto.description)}</p>

                <div class="protocol-sub-block">
                    <div class="block-title-row">
                        <span class="rx-symbol">℞</span>
                        <h3>Primary Prescription Measures (First-Line Therapies)</h3>
                    </div>
                    <div class="rx-cards-grid">
                        ${rxCards}
                    </div>
                </div>

                ${adjunctBlock}

                <div class="protocol-sub-block">
                    <div class="block-title-row">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                        <h3>Non-Pharmacological Care &amp; Hygiene Measures</h3>
                    </div>
                    <ul class="measures-list">
                        ${measures}
                    </ul>
                </div>

                <div class="contraindication-box">
                    <div class="contra-header">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                        <h4>Critical Precautions &amp; Contraindications</h4>
                    </div>
                    <ul class="contra-list">
                        ${contraList}
                    </ul>
                </div>

                <div class="referral-box">
                    <div class="referral-header">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                        <h4>When to Seek Immediate In-Person Dermatologist Evaluation</h4>
                    </div>
                    <ul class="referral-list">
                        ${referralList}
                    </ul>
                </div>

                <p class="rx-disclaimer">
                    <strong>Prescription Notice:</strong> Pharmaceutical regimens, active dosages, and application durations listed above are curated from standard clinical dermatological reference standards. Prescription medications must only be dispensed and initiated under the direct clinical assessment and prescription of a licensed medical practitioner.
                </p>
            </section>
        `;
    }

    // Update hero subtitle if timestamp present
    if (record.timestamp) {
        const sub = document.querySelector(".hero-text .subtitle");
        if (sub) sub.textContent = `Evaluated on ${record.timestamp} • EfficientNet-B0 Classifier`;
    }

    // Render full report
    restoreArea.innerHTML = `
        <div class="result-grid fade-in">
            <div class="result-image-box">
                <img src="${record.image_data || ''}" alt="Clinical skin evaluation sample">
                <p style="font-size: var(--fs-xs); color: var(--clr-text-muted); margin-top: var(--sp-3);">
                    Submitted Clinical Photograph (Input Dimension: 224&times;224 px normalized)
                </p>
            </div>
            <div class="prediction-panel">
                <div class="finding-card">
                    <div class="finding-top-label">Primary Diagnostic Finding</div>
                    <div class="finding-name">${escapeHtml(record.predicted)}</div>
                    <div class="confidence-widget">
                        <div class="confidence-header">
                            <span class="confidence-label">Classification Confidence</span>
                            <span class="confidence-score">${pct}%</span>
                        </div>
                        <div class="progress-track">
                            <div class="progress-fill ${fillClass}" style="width: ${pct}%;"></div>
                        </div>
                        <p class="confidence-interpretation">
                            ${certaintyText}
                        </p>
                    </div>
                </div>
                ${top3Html}
            </div>
        </div>
        ${protoHtml}
        <div class="advisory-box fade-in">
            <div class="advisory-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
            </div>
            <div class="advisory-content">
                <strong>Investigational Medical Disclaimer:</strong>
                This classification output was generated by a deep neural network trained for educational and comparative research purposes. It does <strong>not</strong> constitute a formal clinical or histopathological diagnosis.
                An AI confidence score quantifies internal activation alignment, not the clinical probability of patient disease.
                Always consult a board-certified dermatologist or qualified healthcare provider for proper diagnosis, dermoscopy, and medical treatment.
            </div>
        </div>
    `;
}

/* Hydrate Dashboard summary counters from client registry */
function hydrateDashboard() {
    const stored = getStoredRegistry();
    if (!stored || stored.length === 0) return;

    const caseValueEl = document.querySelector(".card.stat-card:nth-child(2) .stat-value");
    if (caseValueEl) {
        const curVal = parseInt(caseValueEl.textContent.trim(), 10) || 0;
        if (stored.length > curVal) {
            caseValueEl.textContent = stored.length;
        }
    }
}

