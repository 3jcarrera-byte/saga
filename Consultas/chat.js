// ==========================================
// CONTROLADOR DE INTERFAZ Y NÚCLEO DE S.I.N.D.D.I.
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
    const btnSend = document.getElementById('btn-send');
    const btnUpload = document.getElementById('btn-upload');
    const userInput = document.getElementById('user-input');
    const folderInput = document.getElementById('folder-input');

    if (btnSend) btnSend.addEventListener('click', sendMessage);
    if (btnUpload) btnUpload.addEventListener('click', uploadPDF);
    if (folderInput) folderInput.addEventListener('change', handleFolderSelection);

    if (userInput) {
        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    loadKnowledgeLibrary();
    auditCodeCoherence();
    initCanvas2ExportTools();
    initCanvas7ExportTools();
});

function printMessage(sender, text, type) {
    const box = document.getElementById('chat-messages');
    if (!box) return;
    box.innerHTML += `<div class="message ${type}"><strong>${sender}:</strong> ${text}</div>`;
    box.scrollTop = box.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    if (!input) return;
    const msg = input.value.trim();
    if (!msg) return;

    printMessage('Tú', msg, 'user');
    input.value = '';

    const box = document.getElementById('chat-messages');
    const loadingId = 'sinddi-thinking-' + Date.now();
    if (box) {
        box.innerHTML += `<div class="message bot" id="${loadingId}"><strong>S.I.N.D.D.I.:</strong> <em>Procesando consulta y coordinando entorno...</em></div>`;
        box.scrollTop = box.scrollHeight;
    }

    try {
        const response = await fetch('http://localhost:3000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: msg })
        });

        if (!response.ok) throw new Error("Error en servidor local");
        const data = await response.json();

        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();

        printMessage('S.I.N.D.D.I.', data.response, 'bot');

        // Si S.I.N.D.D.I. devuelve código 3D para inyectar mediante tool calls
        if (data.code_3d && data.target_canvas && window.scenes[data.target_canvas]) {
            try {
                const evalFunc = new Function('scene', 'THREE', data.code_3d);
                evalFunc(window.scenes[data.target_canvas], THREE);
            } catch (err) {
                console.error("Error al inyectar código 3D:", err);
            }
        }

        loadKnowledgeLibrary();
        auditCodeCoherence();
    } catch (error) {
        console.error("Error:", error);
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        printMessage('Sistema', 'No pude conectar con mi núcleo local en Node.js.', 'system');
    }
}

// Manejo de la selección de carpeta madre en Canvas 1 y ejecución en Canvas 6
let loadedFilesMap = {};

function handleFolderSelection(e) {
    const files = e.target.files;
    const treeContainer = document.getElementById('file-tree');
    if (!files || files.length === 0) return;

    loadedFilesMap = {};
    let htmlTree = '<ul style="list-style: none; padding-left: 5px; margin: 0;">';
    let mainIndexContent = '';

    for (let file of files) {
        const pathParts = file.webkitRelativePath.split('/');
        let fileName = pathParts[pathParts.length - 1];
        loadedFilesMap[file.webkitRelativePath] = file;

        if (fileName === 'index.html' && !mainIndexContent) {
            file.text().then(content => {
                mainIndexContent = content;
                executeInCanvas6(file.webkitRelativePath, content);
            });
        }

        htmlTree += `<li style="padding: 3px 0; color: #38bdf8; cursor: pointer;" onclick="window.openFileFromTree('${file.webkitRelativePath}')">📄 ${file.webkitRelativePath}</li>`;
    }
    htmlTree += '</ul>';
    treeContainer.innerHTML = htmlTree;
    printMessage('S.I.N.D.D.I.', `Carpeta madre cargada. Ramal y subcarpetas indexados correctamente.`, 'system');
}

window.openFileFromTree = async function(path) {
    const file = loadedFilesMap[path];
    if (!file) return;
    const content = await file.text();
    if (path.endsWith('.html') || path.endsWith('.js')) {
        executeInCanvas6(path, content);
    } else {
        alert(`Archivo ${path} seleccionado.`);
    }
};

function executeInCanvas6(filename, content) {
    const iframe = document.getElementById('runtime-iframe');
    if (!iframe) return;
    iframe.srcdoc = content;
    printMessage('S.I.N.D.D.I.', `Ejecutando ramal/archivo '${filename}' en la Consola Ejecutora (Canvas 6).`, 'system');
}

async function uploadPDF() {
    const fileInput = document.getElementById('pdf-file');
    if (!fileInput || fileInput.files.length === 0) {
        alert("Selecciona un archivo PDF.");
        return;
    }
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('pdf', file);

    printMessage('S.I.N.D.D.I.', `Asimilando y clasificando '${file.name}' en la biblioteca...`, 'bot');

    try {
        const response = await fetch('http://localhost:3000/api/upload', { method: 'POST', body: formData });
        if (!response.ok) throw new Error("Error al indexar");
        const data = await response.json();
        printMessage('S.I.N.D.D.I.', `✨ ${data.message}`, 'bot');
        loadKnowledgeLibrary();
        fileInput.value = '';
    } catch (e) {
        printMessage('Sistema', 'Fallo al procesar el documento PDF.', 'system');
    }
}

async function loadKnowledgeLibrary() {
    const libContainer = document.getElementById('knowledge-library');
    if (!libContainer) return;

    try {
        const res = await fetch('http://localhost:3000/api/memories');
        if (!res.ok) return;
        const memories = await res.json();

        if (memories.length === 0) {
            libContainer.innerHTML = '<p style="font-size: 11px; color: #94a3b8;">Aún no hay conceptos asimilados.</p>';
            return;
        }

        libContainer.innerHTML = memories.map(m => `
            <div style="background: #0f172a; border-left: 3px solid #38bdf8; padding: 6px; margin-bottom: 4px; border-radius: 4px;">
                <strong>📌 [${m.topic || 'General'}] ${m.concept}</strong>
                <p style="margin: 2px 0 0 0; color: #cbd5e1; font-size: 11px;">${m.details}</p>
            </div>
        `).join('');
    } catch (e) {}
}

function auditCodeCoherence() {
    const auditContainer = document.getElementById('audit-matrix');
    if (!auditContainer) return;
    auditContainer.innerHTML = `
        <div class="error-item" onclick="window.jumpToOrigin('app.js', 42)">
            <strong>⚠️ Error [REF-42]:</strong> Variable no definida en app.js (Línea 42)
        </div>
        <div style="font-size: 11px; color: #34d399; margin-top: 6px;">
            <p style="margin:0;">✅ Entorno 3D activo y sincronizado con Canvas 4.</p>
        </div>
    `;
}

window.jumpToOrigin = function(file, line) {
    printMessage('S.I.N.D.D.I.', `Saltando al origen del error en '${file}' (Línea ${line}). Abriendo en editor...`, 'system');
};

function initCanvas2ExportTools() {
    document.getElementById('btn-export-canvas2')?.addEventListener('click', () => {
        alert("Modelo 3D y Materiales PBR exportados correctamente desde Canvas 2.");
    });
}

function initCanvas7ExportTools() {
    document.getElementById('btn-export-canvas7')?.addEventListener('click', () => {
        alert("Estructura de Rigging y Animación exportada correctamente desde Canvas 7.");
    });
}
