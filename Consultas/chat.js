// --- CONFIGURACIÓN DE ESCUCHAS DE EVENTOS ---
document.addEventListener("DOMContentLoaded", () => {
    // Vinculamos funciones a los clics de los botones
    document.getElementById('btn-send').addEventListener('click', sendMessage);
    document.getElementById('btn-upload').addEventListener('click', uploadPDF);

    // Permitir enviar el mensaje presionando la tecla "Enter"
    document.getElementById('user-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});

/**
 * Imprime los mensajes en la caja de texto central con formato limpio.
 */
function printMessage(sender, text, type) {
    const box = document.getElementById('chat-messages');
    if (!box) return;

    box.innerHTML += `<div class="message ${type}"><strong>${sender}:</strong> ${text}</div>`;
    // Auto-scroll hacia abajo para ver siempre el último mensaje
    box.scrollTop = box.scrollHeight;
}

/**
 * Envía el mensaje del usuario al backend de Python y procesa la respuesta e inyección 3D.
 */
async function sendMessage() {
    const input = document.getElementById('user-input');
    const msg = input.value.trim();
    if (!msg) return; // No hacer nada si el campo está vacío

    // 1. Mostrar el mensaje del usuario en pantalla
    printMessage('Tú', msg, 'user');
    input.value = ''; // Limpiar barra de escritura

    try {
        // 2. Conectar con el backend de Flask
        const response = await fetch('http://localhost:5000/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });

        if (!response.ok) throw new Error("Error en la respuesta del servidor");
        
        const data = await response.json();
        
        // 3. Mostrar la respuesta analítica de la IA
        printMessage('Asistente', data.response, 'bot');

        // 4. OTORGAMIENTO DE PERMISOS: Si la IA generó código 3D dinámico, lo ejecutamos
        if (data.code_3d) {
            try {
                // Encapsulamos el script en una función dándole acceso controlado a las escenas de canvas3d.js
                const executeCode = new Function('scenes', 'updateRegistries', data.code_3d);
                executeCode(scenes, updateRegistries);
            } catch (threeError) {
                console.error("Fallo al renderizar la inyección 3D de la IA:", threeError);
                printMessage('Sistema', 'El código 3D de la IA tiene un error de sintaxis gráfica.', 'system');
            }
        }
    } catch (error) {
        console.error("Error de comunicación:", error);
        printMessage('Sistema', 'Imposible conectar con el cerebro de Python. ¿Encendiste app.py?', 'system');
    }
}

/**
 * Toma el archivo PDF seleccionado, extrae su texto en el servidor y lo almacena en memorie.json
 */
async function uploadPDF() {
    const fileInput = document.getElementById('pdf-file');
    if (!fileInput || fileInput.files.length === 0) {
        alert("Por favor, selecciona un archivo PDF primero usando el botón 📂.");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    printMessage('Sistema', `Analizando y asimilando '${file.name}' en la memoria JSON...`, 'system');

    try {
        const response = await fetch('http://localhost:5000/upload-pdf', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error("Error al subir archivo");

        const data = await response.json();
        printMessage('Asistente', data.response, 'bot');
        
        // Limpiar el selector de archivos una vez completado
        fileInput.value = '';
    } catch (error) {
        console.error("Error al procesar PDF:", error);
        printMessage('Sistema', 'Fallo al intentar cargar e indexar el documento PDF.', 'system');
    }
}
