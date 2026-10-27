/* ================================================================
   app.js — Skin Monitor Dashboard client-side logic
   ================================================================ */

document.addEventListener("DOMContentLoaded", () => {
    initNavToggle();
    initDropZone();
    initAnalyzeForm();
    initProtocolTabs();
    syncCurrentResult();
    hydrateHistoryPage();
    restoreClientReport();
    hydrateDashboard();
    initSensorPolling();
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


/* ── Client-side image compression & optimization ───────────────── */
let currentOptimizedFile = null;

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
}

function compressImage(file, maxDimension = 1600, quality = 0.82) {
    return new Promise((resolve) => {
        // If not a standard web image, resolve as-is
        if (!file.type.startsWith("image/") && !/\.(jpe?g|png|webp)$/i.test(file.name)) {
            resolve(file);
            return;
        }

        const reader = new FileReader();
        reader.onerror = () => resolve(file);
        reader.onload = (e) => {
            const img = new Image();
            img.onerror = () => resolve(file);
            img.onload = () => {
                let { width, height } = img;

                // If already within reasonable dimensions and under 2 MB, return as-is
                if (width <= maxDimension && height <= maxDimension && file.size <= 2 * 1024 * 1024) {
                    resolve(file);
                    return;
                }

                // Downscale preserving aspect ratio
                if (width > maxDimension || height > maxDimension) {
                    if (width > height) {
                        height = Math.round((height * maxDimension) / width);
                        width = maxDimension;
                    } else {
                        width = Math.round((width * maxDimension) / height);
                        height = maxDimension;
                    }
                }

                const canvas = document.createElement("canvas");
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext("2d");
                if (!ctx) {
                    resolve(file);
                    return;
                }
                ctx.drawImage(img, 0, 0, width, height);

                canvas.toBlob(
                    (blob) => {
                        if (!blob) {
                            resolve(file);
                            return;
                        }
                        const cleanName = (file.name || "skin_photo.jpg").replace(/\.[^/.]+$/, "") + ".jpg";
                        const compressedFile = new File([blob], cleanName, {
                            type: "image/jpeg",
                            lastModified: Date.now(),
                        });
                        resolve(compressedFile);
                    },
                    "image/jpeg",
                    quality
                );
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
}

/* ── Process selected image with optimization & preview ─────────── */
async function processSelectedFile(file) {
    const container   = document.getElementById("preview-container");
    const imgEl       = document.getElementById("preview-image");
    const nameEl      = document.getElementById("preview-filename");
    const statusEl    = container ? container.querySelector(".preview-status") : null;
    const analyzeBtn  = document.getElementById("analyze-btn");
    const fileInput   = document.getElementById("skin-image-input");
    const cameraInput = document.getElementById("camera-input");

    if (!container || !imgEl) return;

    // Validate on client side
    const allowed = ["image/jpeg", "image/png", "image/webp", "image/jpg"];
    if (file.type && !allowed.includes(file.type.toLowerCase()) && !/\.(jpe?g|png|webp)$/i.test(file.name)) {
        alert("Please select a JPG, PNG, or WebP image.");
        return;
    }

    // Show instant preview using Object URL
    const previewUrl = URL.createObjectURL(file);
    imgEl.src = previewUrl;
    if (nameEl) nameEl.textContent = file.name;
    if (statusEl) {
        statusEl.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="spin">
                <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                <path d="M12 2a10 10 0 0 1 10 10"/>
            </svg>
            Optimizing image for fast analysis (${formatBytes(file.size)})...
        `;
    }
    container.classList.add("visible");
    if (analyzeBtn) analyzeBtn.disabled = true;

    try {
        // Automatically optimize/compress the image (especially high-res phone camera shots)
        const optimized = await compressImage(file, 1600, 0.82);
        currentOptimizedFile = optimized;

        // Sync into file input so native form submission carries the optimized payload
        if (fileInput) {
            try {
                const dt = new DataTransfer();
                dt.items.add(optimized);
                fileInput.files = dt.files;
                if (cameraInput) cameraInput.value = "";
            } catch (dtErr) {
                console.warn("DataTransfer sync fallback active:", dtErr);
            }
        }

        if (statusEl) {
            statusEl.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
                Ready for AI analysis (${formatBytes(optimized.size)})
            `;
        }
    } catch (err) {
        console.error("Image compression error:", err);
        currentOptimizedFile = file;
        if (statusEl) {
            statusEl.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
                Ready for AI analysis (${formatBytes(file.size)})
            `;
        }
    } finally {
        if (analyzeBtn) analyzeBtn.disabled = false;
    }
}

function showPreview(file) {
    processSelectedFile(file);
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
            processSelectedFile(files[0]);
        }
    });

    // Handle file input change (choose file / gallery)
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            const cam = document.getElementById("camera-input");
            if (cam) cam.value = "";
            processSelectedFile(fileInput.files[0]);
        }
    });

    // Also listen on the camera input if present
    const cameraInput = document.getElementById("camera-input");
    if (cameraInput) {
        cameraInput.addEventListener("change", () => {
            if (cameraInput.files.length > 0) {
                processSelectedFile(cameraInput.files[0]);
            }
        });
    }
}

/* ── Form submission with loader & payload safeguard ────────────── */
function initAnalyzeForm() {
    const form    = document.getElementById("analyze-form");
    const loader  = document.getElementById("loader-overlay");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        const fileInput   = document.getElementById("skin-image-input");
        const cameraInput = document.getElementById("camera-input");

        let file = currentOptimizedFile;
        if (!file) {
            file = (fileInput && fileInput.files && fileInput.files[0]) ||
                   (cameraInput && cameraInput.files && cameraInput.files[0]);
        }

        if (!file) {
            e.preventDefault();
            alert("Please select or capture an image first.");
            return;
        }

        // Vercel serverless request body ceiling is 4.5 MB.
        // If file exceeds 3.5 MB, guarantee compression before upload to avoid 413 error
        if (file.size > 3.5 * 1024 * 1024) {
            e.preventDefault();
            if (loader) {
                const textEl = loader.querySelector(".loader-text");
                if (textEl) textEl.textContent = "Optimizing high-resolution photo for upload…";
                loader.classList.add("active");
            }

            try {
                const compressed = await compressImage(file, 1400, 0.78);
                currentOptimizedFile = compressed;

                if (compressed.size > 4.2 * 1024 * 1024) {
                    alert("This image is too large even after compression. Please choose a photo under 4 MB.");
                    if (loader) loader.classList.remove("active");
                    return;
                }

                try {
                    const dt = new DataTransfer();
                    dt.items.add(compressed);
                    fileInput.files = dt.files;
                    if (cameraInput) cameraInput.value = "";
                    if (loader) {
                        const textEl = loader.querySelector(".loader-text");
                        if (textEl) textEl.textContent = "Evaluating lesion with EfficientNet-B0…";
                    }
                    form.submit();
                    return;
                } catch (dtErr) {
                    // Fallback to fetch + manual page render if DataTransfer is blocked
                    const formData = new FormData();
                    formData.append("skin_image", compressed, compressed.name);
                    const resp = await fetch(form.action || "/predict", {
                        method: "POST",
                        body: formData
                    });
                    if (resp.redirected) {
                        window.location.href = resp.url;
                    } else {
                        const html = await resp.text();
                        document.open();
                        document.write(html);
                        document.close();
                    }
                    return;
                }
            } catch (err) {
                console.error("Compression failed before submit:", err);
                alert("Could not optimize the image. Please select a smaller photo.");
                if (loader) loader.classList.remove("active");
                return;
            }
        }

        // Normal payload (< 3.5 MB)
        if (loader) {
            const textEl = loader.querySelector(".loader-text");
            if (textEl) textEl.textContent = "Evaluating lesion with EfficientNet-B0…";
            loader.classList.add("active");
        }
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
    currentOptimizedFile = null;
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

    // Rebuild mobile card list view (Visible on mobile <= 768px)
    const cardsView = document.getElementById("history-cards-view");
    if (cardsView) {
        cardsView.innerHTML = stored.map(r => {
            const pct = r.confidence ? `${(r.confidence * 100).toFixed(1)}%` : "N/A";
            const imgSrc = r.image_data || (r.image_file ? `/uploads/${encodeURIComponent(r.image_file)}` : "");
            return `
                <a href="/result/${encodeURIComponent(String(r.id))}" class="history-card-row">
                    <img class="case-thumb" src="${imgSrc}" alt="Case #${escapeHtml(String(r.id))}" loading="lazy"
                         onerror="this.style.opacity='0.4';">
                    <div class="history-card-info">
                        <div class="history-card-top-row">
                            <span class="pred">${escapeHtml(r.predicted)}</span>
                            <span class="condition-pill pill-sm">${pct}</span>
                        </div>
                        <div class="ts">
                            <span class="case-tag">Case #${escapeHtml(String(r.id))}</span> &bull; <span>${escapeHtml(r.timestamp || "")}</span>
                        </div>
                    </div>
                    <div class="history-card-action">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
                    </div>
                </a>
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
            <div class="rx-card-modern">
                <div class="rx-card-header">
                    <span class="rx-symbol-mini">℞</span>
                    <div style="flex:1;">
                        <div class="rx-med-name">${escapeHtml(rx.medication)}</div>
                        <span class="rx-class-badge">${escapeHtml(rx.class_type)}</span>
                    </div>
                </div>

                <div class="rx-regimen-box">
                    <div class="regimen-tag">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        HOW TO APPLY / DOSAGE
                    </div>
                    <div class="regimen-text">${escapeHtml(rx.dosage)}</div>
                </div>

                ${rx.note ? `
                <div class="rx-tip-box">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--clr-accent)" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                    <span><strong>Clinical Tip:</strong> ${escapeHtml(rx.note)}</span>
                </div>` : ""}
            </div>
        `).join("");

        let adjunctBlock = "";
        if (proto.adjunct_otc && proto.adjunct_otc.length > 0) {
            const adjCards = proto.adjunct_otc.map(adj => `
                <div class="adjunct-mini-card">
                    <div class="adjunct-mini-name">${escapeHtml(adj.medication)}</div>
                    <div class="adjunct-mini-purpose">${escapeHtml(adj.purpose)}</div>
                    <div class="adjunct-mini-regimen"><strong>Regimen:</strong> ${escapeHtml(adj.dosage)}</div>
                </div>
            `).join("");

            adjunctBlock = `
                <div class="care-column-card">
                    <div class="care-column-title">
                        <div class="column-icon-circle info-circle">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2v20M2 12h20"/></svg>
                        </div>
                        <h4>Supportive &amp; Symptomatic Relief</h4>
                    </div>
                    <div class="adjunct-cards-list">
                        ${adjCards}
                    </div>
                </div>
            `;
        }

        const measures = (proto.non_pharma_measures || []).map(m => `
            <li class="clean-check-item">
                <div class="check-icon-circle">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
                <span>${escapeHtml(m)}</span>
            </li>
        `).join("");

        const contraList = (proto.contraindications || []).map(c => `
            <li>
                <span class="bullet-x">&times;</span>
                <span>${escapeHtml(c)}</span>
            </li>
        `).join("");

        const referralList = (proto.urgent_referral || []).map(r => `
            <li>
                <span class="bullet-alert">!</span>
                <span>${escapeHtml(r)}</span>
            </li>
        `).join("");

        protoHtml = `
            <section class="card protocol-section fade-in" id="treatment-protocol-card">
                <!-- Header -->
                <div class="protocol-header">
                    <div class="protocol-header-title">
                        <div class="protocol-icon-box">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
                                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
                            </svg>
                        </div>
                        <div>
                            <div class="protocol-badge-row">
                                <span class="protocol-badge">${escapeHtml(proto.category)}</span>
                                <span class="rx-pill">Standard Medical Protocol</span>
                            </div>
                            <h2 class="protocol-title">Treatment Protocol &amp; Prescription Guidance: ${escapeHtml(proto.title)}</h2>
                        </div>
                    </div>
                </div>

                <!-- Brief Overview Callout -->
                <div class="protocol-summary-box">
                    <div class="summary-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                    </div>
                    <div class="summary-content">
                        <span class="summary-label">Condition Overview</span>
                        <p class="summary-text">${escapeHtml(proto.description)}</p>
                    </div>
                </div>

                <!-- Quick Navigation Filter Tabs -->
                <div class="protocol-nav-tabs" role="tablist">
                    <button type="button" class="proto-tab-btn active" data-target="all">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
                        All Guidance
                    </button>
                    <button type="button" class="proto-tab-btn" data-target="medications">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/></svg>
                        1. Prescribed Medications (Rx)
                    </button>
                    <button type="button" class="proto-tab-btn" data-target="daily-care">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                        2. Daily Care &amp; Routine
                    </button>
                    <button type="button" class="proto-tab-btn" data-target="safety">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                        3. Safety &amp; Red Flags
                    </button>
                </div>

                <!-- Section 1: Prescribed Medications (First-Line Rx) -->
                <div class="protocol-section-block" data-section="medications">
                    <div class="section-block-header">
                        <div class="section-num-pill">1</div>
                        <div>
                            <h3>Prescribed Medications (First-Line Therapies)</h3>
                            <p class="section-subtext">Primary evidence-based pharmaceutical regimens for symptom relief and flare suppression.</p>
                        </div>
                    </div>

                    <div class="rx-cards-grid">
                        ${rxCards}
                    </div>
                </div>

                <!-- Section 2: Daily Skin Care & Supportive Remedies -->
                <div class="protocol-section-block" data-section="daily-care">
                    <div class="section-block-header">
                        <div class="section-num-pill">2</div>
                        <div>
                            <h3>Daily Skin Care Routine &amp; Supportive Care</h3>
                            <p class="section-subtext">Essential non-pharmacological habits and over-the-counter measures to rebuild the skin barrier.</p>
                        </div>
                    </div>

                    <div class="daily-care-grid">
                        <div class="care-column-card">
                            <div class="care-column-title">
                                <div class="column-icon-circle success-circle">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                                </div>
                                <h4>Recommended Daily Habits</h4>
                            </div>
                            <ul class="clean-check-list">
                                ${measures}
                            </ul>
                        </div>
                        ${adjunctBlock}
                    </div>
                </div>

                <!-- Section 3: Safety Warnings & Red Flags -->
                <div class="protocol-section-block" data-section="safety">
                    <div class="section-block-header">
                        <div class="section-num-pill warning-pill">3</div>
                        <div>
                            <h3>Safety Precautions &amp; When to See a Doctor</h3>
                            <p class="section-subtext">Critical safety precautions and urgent warning signs that necessitate physician intervention.</p>
                        </div>
                    </div>

                    <div class="safety-cards-grid">
                        <div class="safety-card precautions-card">
                            <div class="safety-card-header">
                                <div class="safety-icon-box warn-icon">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                                </div>
                                <h4>Important Precautions (What to Avoid)</h4>
                            </div>
                            <ul class="safety-list warn-items">
                                ${contraList}
                            </ul>
                        </div>

                        <div class="safety-card urgent-card">
                            <div class="safety-card-header">
                                <div class="safety-icon-box alert-icon">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                                </div>
                                <h4>Seek Immediate In-Person Evaluation If:</h4>
                            </div>
                            <ul class="safety-list alert-items">
                                ${referralList}
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Clean Legal Prescription Notice Footer -->
                <div class="protocol-legal-footer">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                    <span><strong>Prescription Notice:</strong> Dosages, formulations, and durations listed above are curated from standard dermatological reference guidelines. Prescription medicines must only be dispensed and used under the direct clinical assessment and prescription of a qualified healthcare provider.</span>
                </div>
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

    // Re-initialize interactive tabs on dynamically restored section
    initProtocolTabs();
}

/* Interactive Navigation Tabs for Clinical Protocol Section */
function initProtocolTabs() {
    const tabButtons = document.querySelectorAll(".proto-tab-btn");
    if (!tabButtons.length) return;

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const target = btn.getAttribute("data-target");
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const sections = document.querySelectorAll(".protocol-section-block");
            sections.forEach(sec => {
                const secType = sec.getAttribute("data-section");
                if (target === "all" || secType === target) {
                    sec.style.display = "";
                    sec.style.opacity = "1";
                } else {
                    sec.style.display = "none";
                }
            });
        });
    });
}

/* Hydrate Dashboard summary counters and recent assessment cards from client registry */
function hydrateDashboard() {
    const stored = getStoredRegistry();
    if (!stored || stored.length === 0) return;

    // Update total cases metric counter
    const caseValueEl = document.querySelector(".card.stat-card:nth-child(2) .stat-value");
    if (caseValueEl) {
        const curVal = parseInt(caseValueEl.textContent.trim(), 10) || 0;
        if (stored.length > curVal) {
            caseValueEl.textContent = stored.length;
        }
    }

    // Hydrate Recent Clinical Assessments list on Dashboard
    const recentCards = document.getElementById("dashboard-recent-cards");
    const emptyGuide = document.getElementById("dashboard-empty-guide");
    const recentSection = document.getElementById("dashboard-recent-section");

    if (emptyGuide && !recentSection && stored.length > 0) {
        emptyGuide.style.display = "none";
        const newSection = document.createElement("section");
        newSection.className = "card fade-in";
        newSection.id = "dashboard-recent-section";
        newSection.style.marginTop = "var(--sp-6)";
        newSection.innerHTML = `
            <div class="table-toolbar">
                <div>
                    <h2>Recent Clinical Assessments</h2>
                    <p style="font-size: var(--fs-xs); color: var(--clr-text-muted);">Latest image classifications logged in the local database</p>
                </div>
                <a href="/history" class="btn btn-outline btn-sm">View Full History</a>
            </div>
            <div class="history-cards" id="dashboard-recent-cards" style="margin-top: var(--sp-4);"></div>
        `;
        emptyGuide.parentNode.insertBefore(newSection, emptyGuide);
    }

    const cardsContainer = document.getElementById("dashboard-recent-cards");
    if (cardsContainer && stored.length > 0) {
        const top5 = stored.slice(0, 5);
        cardsContainer.innerHTML = top5.map(r => {
            const pct = r.confidence ? `${(r.confidence * 100).toFixed(1)}%` : "N/A";
            const imgSrc = r.image_data || (r.image_file ? `/uploads/${encodeURIComponent(r.image_file)}` : "");
            return `
                <a href="/result/${encodeURIComponent(String(r.id))}" class="history-card-item" style="text-decoration:none; color:inherit; display:flex;">
                    <img src="${imgSrc}" alt="Analysis sample #${escapeHtml(String(r.id))}" loading="lazy" onerror="this.style.opacity='0.4';">
                    <div class="history-card-info">
                        <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                            <span class="pred">${escapeHtml(r.predicted)}</span>
                            <span class="condition-pill pill-sm">${pct}</span>
                        </div>
                        <div class="ts">
                            <span class="case-tag">Case #${escapeHtml(String(r.id))}</span> &bull; <span>${escapeHtml(r.timestamp || "")}</span>
                        </div>
                    </div>
                </a>
            `;
        }).join("");
    }
}


/* ── Live IoT Environmental Telemetry Polling (Raspberry Pi 3 + DHT11) ────── */
function initSensorPolling() {
    const card = document.getElementById("iot-telemetry-card");
    if (!card) return;

    const badgeEl    = document.getElementById("sensor-status-badge");
    const labelEl    = document.getElementById("sensor-status-label");
    const tempValEl  = document.getElementById("sensor-temp-val");
    const humValEl   = document.getElementById("sensor-hum-val");
    const tempSubEl  = document.getElementById("sensor-temp-sub");
    const humSubEl   = document.getElementById("sensor-hum-sub");
    const deviceIdEl = document.getElementById("sensor-device-id");
    const lastSeenEl = document.getElementById("sensor-last-seen");
    const refreshBtn = document.getElementById("sensor-refresh-btn");

    let isFetching = false;

    function formatRelativeTime(seconds) {
        if (seconds === null || seconds === undefined) return "Never";
        if (seconds < 5) return "Just now";
        if (seconds < 60) return `${seconds}s ago`;
        const mins = Math.floor(seconds / 60);
        if (mins < 60) return `${mins}m ago`;
        const hrs = Math.floor(mins / 60);
        return `${hrs}h ago`;
    }

    async function fetchSensorTelemetry() {
        if (isFetching) return;
        isFetching = true;
        if (refreshBtn) refreshBtn.classList.add("refreshing");

        try {
            const resp = await fetch("/api/sensor/latest", {
                headers: { "Accept": "application/json" },
                cache: "no-store",
            });

            if (!resp.ok) {
                throw new Error(`HTTP ${resp.status}`);
            }

            const data = await resp.json();
            renderTelemetry(data);
        } catch (err) {
            console.warn("[DermaScan IoT] Sensor poll error:", err);
            if (badgeEl) {
                badgeEl.className = "sensor-status-badge status-offline";
            }
            if (labelEl) labelEl.textContent = "Network Error";
            if (tempSubEl) tempSubEl.textContent = "Unable to reach sensor gateway.";
            if (humSubEl) humSubEl.textContent = "Will retry automatically.";
        } finally {
            isFetching = false;
            if (refreshBtn) {
                setTimeout(() => refreshBtn.classList.remove("refreshing"), 400);
            }
        }
    }

    function renderTelemetry(data) {
        if (!data) return;

        const status = data.status || "offline";
        if (deviceIdEl && data.device_id) deviceIdEl.textContent = data.device_id;

        // Reset badge classes
        if (badgeEl) {
            badgeEl.className = `sensor-status-badge status-${status}`;
        }

        if (status === "online") {
            if (labelEl) labelEl.textContent = "Online (Live)";
            if (tempValEl && data.temperature !== null) tempValEl.textContent = Number(data.temperature).toFixed(1);
            if (humValEl && data.humidity !== null) humValEl.textContent = Number(data.humidity).toFixed(1);

            // Contextual comfort evaluation
            if (tempSubEl) {
                const t = Number(data.temperature);
                if (t > 28) tempSubEl.textContent = "Elevated clinical room temp — may increase pruritus.";
                else if (t < 18) tempSubEl.textContent = "Cool environment — monitor skin barrier xerosis.";
                else tempSubEl.textContent = "Optimal clinical examination range (19°C – 26°C).";
            }

            if (humSubEl) {
                const h = Number(data.humidity);
                if (h < 35) humSubEl.textContent = "Low humidity — promotes trans-epidermal water loss (TEWL).";
                else if (h > 70) humSubEl.textContent = "High humidity — may promote microbial proliferation.";
                else humSubEl.textContent = "Balanced ambient relative humidity (40% – 60%).";
            }

            if (lastSeenEl) lastSeenEl.textContent = formatRelativeTime(data.age_seconds);
        } else if (status === "stale") {
            if (labelEl) labelEl.textContent = `Stale (${data.age_seconds}s)`;
            if (tempValEl && data.temperature !== null) tempValEl.textContent = Number(data.temperature).toFixed(1);
            if (humValEl && data.humidity !== null) humValEl.textContent = Number(data.humidity).toFixed(1);
            if (tempSubEl) tempSubEl.textContent = "Telemetry paused (>60s old). Awaiting transmission.";
            if (humSubEl) humSubEl.textContent = "Previous reading held for environmental reference.";
            if (lastSeenEl) lastSeenEl.textContent = formatRelativeTime(data.age_seconds);
        } else if (status === "offline") {
            if (labelEl) labelEl.textContent = "Pi Sensor Offline";
            if (tempValEl) tempValEl.textContent = "--";
            if (humValEl) humValEl.textContent = "--";
            if (tempSubEl) tempSubEl.textContent = "Raspberry Pi not transmitting.";
            if (humSubEl) humSubEl.textContent = "Check Wi-Fi and power on Raspberry Pi 3.";
            if (lastSeenEl) lastSeenEl.textContent = data.age_seconds ? formatRelativeTime(data.age_seconds) : "Offline";
        } else if (status === "waiting_for_sensor") {
            if (labelEl) labelEl.textContent = "Waiting for Sensor";
            if (tempValEl) tempValEl.textContent = "--";
            if (humValEl) humValEl.textContent = "--";
            if (tempSubEl) tempSubEl.textContent = "Run raspberry_pi/send_sensor.py on your Pi 3.";
            if (humSubEl) humSubEl.textContent = "Awaiting initial DHT11 transmission.";
            if (lastSeenEl) lastSeenEl.textContent = "Awaiting 1st packet";
        } else if (status === "unconfigured") {
            if (labelEl) labelEl.textContent = "Supabase Unconfigured";
            if (tempValEl) tempValEl.textContent = "--";
            if (humValEl) humValEl.textContent = "--";
            if (tempSubEl) tempSubEl.textContent = "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.";
            if (humSubEl) humSubEl.textContent = "See README for Supabase configuration steps.";
            if (lastSeenEl) lastSeenEl.textContent = "Not configured";
        }
    }

    // Initial fetch immediately
    fetchSensorTelemetry();

    // Auto-poll every 15 seconds
    setInterval(fetchSensorTelemetry, 15000);

    // Manual refresh button listener
    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            fetchSensorTelemetry();
        });
    }
}

