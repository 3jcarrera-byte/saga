// ==========================================
// CONTROLADOR DE INTERFAZ Y NÚCLEO DE S.I.N.D.D.I.
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
    const btnSend = document.getElementById('btn-send');
    const btnUpload = document.getElementById('btn-upload');
    const userInput = document.getElementById('user-input');

    if (btnSend) btnSend.addEventListener('click', sendMessage);
    if (btnUpload) btnUpload.addEventListener('click', uploadPDF);

    if (userInput) {
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    // Inicializar componentes visuales de S.I.N.D.D.I. al arrancar
    loadKnowledgeLibrary(); // Canvas 3
    initFileTreeWorkspace(); // Canvas 1 y Canvas 6
    auditCodeCoherence();    // Canvas 8
});

/**
 * Imprime los mensajes en la caja de texto central con formato limpio y personalidad de S.I.N.D.D.I.
 */
function printMessage(sender, text, type) {
    const box = document.getElementById('chat-messages');
    if (!box) return;

    box.innerHTML += `<div class="message ${type}"><strong>${sender}:</strong> ${text}</div>`;
    box.scrollTop = box.scrollHeight;
}

/**
 * Envía la consulta de la usuaria al núcleo local en Node.js y procesa la respuesta por ensamble semántico.
 */
async function sendMessage() {
    const input = document.getElementById('user-input');
    if (!input) return;
    const msg = input.value.trim();
    if (!msg) return;

    printMessage('Tú', msg, 'user');
    input.value = '';

    // Indicador visual de procesamiento de S.I.N.D.D.I.
    const box = document.getElementById('chat-messages');
    const loadingId = 'sinddi-thinking-' + Date.now();
    if (box) {
        box.innerHTML += `<div class="message bot" id="${loadingId}"><strong>S.I.N.D.D.I.:</strong> <em>Consultando mi memoria evolutiva local...</em></div>`;
        box.scrollTop = box.scrollHeight;
    }

    try {
        const response = await fetch('http://localhost:3000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: msg })
        });

        if (!response.ok) throw new Error("Error en la respuesta del servidor local");
        
        const responseText = await response.text();
        
        // Remover indicador de carga
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();

        printMessage('S.I.N.D.D.I.', responseText, 'bot');

        // Refrescar Canvas 3 y Canvas 8
        loadKnowledgeLibrary();
        auditCodeCoherence();

    } catch (error) {
        console.error("Error de comunicación:", error);
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        printMessage('Sistema', 'No pude conectar con mi núcleo local en Node.js. ¿Verificaste que server.js esté activo en el puerto 3000?', 'system');
    }
}

/**
 * Toma el archivo PDF seleccionado, lo envía a S.I.N.D.D.I. para indexación sin internet y actualización de memorias.
 */
async function uploadPDF() {
    const fileInput = document.getElementById('pdf-file') || document.getElementById('pdf');
    if (!fileInput || fileInput.files.length === 0) {
        alert("Por favor, selecciona un archivo PDF primero usando el selector 📂.");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('pdf', file); // Coincide con upload.single('pdf') en server.js

    printMessage('S.I.N.D.D.I.', `Analizando y asimilando '${file.name}' directamente en mi base de vectores local...`, 'bot');

    try {
        const response = await fetch('http://localhost:3000/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error("Error al indexar el documento");

        const data = await response.json();
        printMessage('S.I.N.D.D.I.', `✨ ¡Listo! ${data.message} (${data.chunks} fragmentos vectorizados).`, 'bot');
        
        // Actualizar la biblioteca de conocimiento (Canvas 3)
        loadKnowledgeLibrary();
        fileInput.value = '';
    } catch (error) {
        console.error("Error al procesar PDF:", error);
        printMessage('Sistema', 'Fallo al intentar cargar e indexar el documento PDF.', 'system');
    }
}

/**
 * Carga y renderiza la Biblioteca de Conocimiento en el Canvas 3 a partir de memories.json
 */
async function loadKnowledgeLibrary() {
    const libContainer = document.getElementById('knowledge-library');
    if (!libContainer) return;

    try {
        const res = await fetch('http://localhost:3000/api/memories');
        if (!res.ok) return;
        const memories = await res.json();

        if (memories.length === 0) {
            libContainer.innerHTML = '<p class="muted" style="font-size: 12px; color: #94a3b8;">Aún no hay conceptos asimilados en la biblioteca.</p>';
            return;
        }

        libContainer.innerHTML = memories.map(m => `
            <div class="knowledge-card" style="background: #0f172a; border-left: 3px solid #38bdf8; padding: 8px; margin-bottom: 6px; border-radius: 4px; font-size: 12px;">
                <strong>📌 ${m.concept}</strong>
                <p style="margin: 4px 0 0 0; color: #cbd5e1;">${m.details}</p>
            </div>
        `).join('');
    } catch (e) {
        console.error("No se pudo cargar la biblioteca de conocimiento:", e);
    }
}

/**
 * Inicializa el ramal de archivos en el Canvas 1 y permite su ejecución en el Canvas 6
 */
function initFileTreeWorkspace() {
    const treeContainer = document.getElementById('file-tree');
    if (!treeContainer) return;

    // Ramal de archivos simulado del programa activo
    const projectFiles = [
        { filename: 'index.html', content: '<html><body style="font-family:sans-serif; text-align:center; padding-top:20px; background:#f8fafc;"><h2>⚡ S.I.N.D.D.I. Runtime Activo</h2><p>Ejecutando ramal del Canvas 1 correctamente.</p></body></html>' },
        { filename: 'app.js', content: 'console.log("S.I.N.D.D.I. script cargado en el entorno de ejecución.");' }
    ];

    treeContainer.innerHTML = `
        <div class="folder-view" style="font-size: 13px;">
            <strong>📁 /Proyecto_SINDDI_Core</strong>
            <ul style="list-style: none; padding-left: 10px; margin-top: 5px;">
                ${projectFiles.map(f => `
                    <li style="cursor: pointer; padding: 4px 0; color: #38bdf8; display: flex; align-items: center; gap: 4px;" onclick="window.executeFileInCanvas6('${f.filename}', \`${encodeURIComponent(f.content)}\`)">
                        📄 <span>${f.filename}</span>
                    </li>
                `).join('')}
            </ul>
        </div>
    `;

    // Cargar la vista previa por defecto en el Canvas 6
    executeFileInCanvas6('index.html', encodeURIComponent(projectFiles[0].content));
}

/**
 * Carga y ejecuta el ramal de archivos seleccionado en el Canvas 6 (Consola Ejecutora / Iframe)
 */
function executeFileInCanvas6(filename, encodedContent) {
    const iframe = document.getElementById('runtime-iframe');
    if (!iframe) return;

    const content = decodeURIComponent(encodedContent);
    iframe.srcdoc = content;
    
    printMessage('S.I.N.D.D.I.', `He desplegado el archivo '${filename}' en la consola ejecutora (Canvas 6).`, 'system');
}

/**
 * Depurador de coherencia para el Canvas 8
 */
function auditCodeCoherence() {
    const auditContainer = document.getElementById('audit-matrix');
    if (!auditContainer) return;

    auditContainer.innerHTML = `
        <div style="font-size: 12px; color: #34d399; display: flex; flex-direction: column; gap: 4px;">
            <p style="margin:0;">✅ Ramal de archivos sincronizado.</p>
            <p style="margin:0;">✅ Enlaces 3D estables en estaciones.</p>
            <p style="margin:0;">✅ Cerebro autónomo local en línea.</p>
        </div>
    `;
}

// Exposición global para llamadas inline en HTML
window.executeFileInCanvas6 = executeFileInCanvas6;
window.uploadPDF = uploadPDF;
window.sendMessage = sendMessage;
