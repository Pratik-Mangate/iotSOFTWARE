/* ================================================================
   app.js — Skin Monitor Dashboard client-side logic
   ================================================================ */

document.addEventListener("DOMContentLoaded", () => {
    initNavToggle();
    initDropZone();
    initAnalyzeForm();
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
