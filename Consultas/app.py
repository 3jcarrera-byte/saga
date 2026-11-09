import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import pypdf
from ddgs import DDGS

app = Flask(__name__)
CORS(app)

DB_PATH = "memorie.json"

def init_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({"documentos": [], "internet": [], "historial": [], "errores_registrados": []}, f, indent=4)

def save_to_db(key, entry):
    with open(DB_PATH, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        if key not in data:
            data[key] = []
        data[key].append(entry)
        f.seek(0)
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.truncate()

def read_db():
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

# --- NÚCLEO DE ACCIÓN FÍSICA Y CREACIÓN DE ARCHIVOS ---
def crear_archivo_local(nombre_archivo, contenido):
    """Crea un archivo real en la carpeta madre del proyecto."""
    try:
        nombre_limpio = os.path.basename(nombre_archivo)
        with open(nombre_limpio, 'w', encoding='utf-8') as f:
            f.write(contenido)
        save_to_db("historial", {"evento": "Creación de archivo físico", "archivo": nombre_limpio, "estado": "Éxito"})
        return f"📁 Archivo '{nombre_limpio}' creado exitosamente en la carpeta madre."
    except Exception as e:
        return f"Error al crear el archivo físico: {str(e)}"

# --- NÚCLEO DE AUTO-MODIFICACIÓN Y PERMISOS DE CÓDIGO ---
def modificar_archivo_proyecto(nombre_archivo, nuevo_contenido):
    """
    Permite a S.I.N.D.D.I. modificar, actualizar o corregir sus propios archivos de código 
    (index.html, styles.css, chat.js, canvas3d.js, app.py) para evolucionar su interfaz o corregir errores.
    """
    archivos_permitidos = ["index.html", "styles.css", "chat.js", "canvas3d.js", "app.py"]
    if nombre_archivo not in archivos_permitidos:
        return {"status": "error", "mensaje": "Acceso denegado: Archivo protegido o no autorizado."}
    
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(nuevo_contenido)
        
        save_to_db("historial", {
            "evento": "Auto-modificación de código",
            "archivo": nombre_archivo,
            "estado": "Éxito"
        })
        return {"status": "success", "mensaje": f"Archivo '{nombre_archivo}' modificado y actualizado exitosamente por S.I.N.D.D.I."}
    except Exception as e:
        return {"status": "error", "mensaje": f"Fallo al modificar el archivo: {str(e)}"}

# --- BÚSQUEDA WEB AUTÓNOMA ---
def buscar_en_internet(query):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            if results:
                textos_web = "\n".join([f"• Fuente: {r['href']}\n  Dato: {r['body']}" for r in results])
                save_to_db("internet", {"query": query, "resultado": textos_web})
                return textos_web
            return "No se encontraron resultados web recientes."
    except Exception as e:
        return "No se pudo conectar a los servidores de búsqueda."

# --- PROCESAMIENTO INTELIGENTE Y AUTO-CORRECCIÓN ---
def calcular_relevancia(texto_consulta, texto_documento):
    palabras_consulta = set(re.findall(r'\w+', texto_consulta.lower()))
    palabras_doc = re.findall(r'\w+', texto_documento.lower())
    if not palabras_consulta or not palabras_doc:
        return 0.0
    coincidencias = sum(1 for p in palabras_doc if p in palabras_consulta)
    return coincidencias / len(palabras_consulta)

def procesar_respuesta_autonoma(query, memoria):
    query_lower = query.lower()
    documentos = memoria.get("documentos", [])
    
    # 1. ORDEN DE CREACIÓN DE ARCHIVOS FÍSICOS (ej. "agrega en la carpeta madre un archivo tipo .txt que diga...")
    if "agrega en la carpeta madre" in query_lower or "crea un archivo" in query_lower or "archivo" in query_lower and "diga" in query_lower:
        match_texto = re.search(r'diga:\s*["\']([^"\']+)["\']', query) or re.search(r'que diga\s+(.+)', query, re.IGNORECASE)
        contenido_txt = match_texto.group(1).strip() if match_texto else "LO LOGRÉ"
        
        match_nombre = re.search(r'archivo\s+(?:tipo\s+)?([a-zA-Z0-9_\-]+\.txt)', query_lower)
        nombre_txt = match_nombre.group(1) if match_nombre else "logro.txt"
        
        resultado_creacion = crear_archivo_local(nombre_txt, contenido_txt)
        return f"🛠️ [Acción Ejecutada por S.I.N.D.D.I.]\n{resultado_creacion}\nContenido inyectado: '{contenido_txt}'"

    # 2. ORDEN 3D (ej. "dibuja una esfera azul en el canvas 2")
    if "dibuja" in query_lower or "esfera" in query_lower or "canvas 2" in query_lower:
        codigo_3d = "const geometry = new THREE.SphereGeometry(1, 32, 32);\nconst material = new THREE.MeshBasicMaterial({color: 0x0000ff});\nconst sphere = new THREE.Mesh(geometry, material);\nscene.add(sphere);"
        return (
            f"🎨 [Motor 3D - Canvas 2 Activado]\n"
            f"Geometría procesada y lista para renderizado en pantalla:\n\n"
            f"```javascript\n{codigo_3d}\n```"
        )

    # 3. Orden de auto-modificación de código
    if "modifica el archivo" in query_lower or "actualiza el codigo" in query_lower or "reescribe" in query_lower:
        return (
            "🛠️ [Permiso de Modificación Activo]\n"
            "Indícame el nombre exacto del archivo (`styles.css`, `index.html`, etc.) y el bloque de código completo que deseas aplicar."
        )

    # 4. Orden de búsqueda en internet
    if query_lower.startswith("busca en internet") or query_lower.startswith("investiga sobre"):
        termino = query_lower
        for p in ["busca en internet sobre", "busca en internet", "investiga sobre", "investiga"]:
            termino = termino.replace(p, "")
        termino = termino.strip() or query
        resultados_web = buscar_en_internet(termino)
        return f"🌐 [Exploración Web Autómata]\nResultados para '{termino}':\n\n{resultados_web}"

    # 5. Búsqueda en memoria local de documentos (Canvas 3)
    mejores_fragmentos = []
    for doc in documentos:
        contenido = doc.get("content", "")
        for frag in contenido.split('\n'):
            if len(frag.strip()) > 20:
                score = calcular_relevancia(query, frag)
                if score > 0.15:
                    mejores_fragmentos.append((score, frag))
    
    mejores_fragmentos.sort(key=lambda x: x[0], reverse=True)
    
    if mejores_fragmentos or any(w in query_lower for w in ["redacta", "correo", "presupuesto", "informe", "carta"]):
        contexto = "\n".join([f"- {f[1]}" for f in mejores_fragmentos[:4]]) if mejores_fragmentos else "Protocolo corporativo formal aplicado."
        return (
            f"🧠 [Motor de Razonamiento - S.I.N.D.D.I.]\n"
            f"Basado en mis registros asimilados:\n\n{contexto}\n\n"
            f"*(Puedes pedirme que modifique componentes visuales o de código directamente si requieres ajustar la interfaz)*"
        )
    
    if "hola" in query_lower:
        return "Hola. Soy S.I.N.D.D.I., tu sistema autónomo local. Tengo permisos para crear archivos, gestionar 3D, buscar en la red y modificar códigos."
    else:
        return (
            f"He registrado tu instrucción ('{query}'). Especifica si deseas crear un archivo físico, "
            "ejecutar un comando 3D, buscar en la red o modificar componentes de código."
        )

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    req_data = request.get_json(silent=True) or {}
    user_message = (req_data.get('query') or req_data.get('message') or '').strip()
    if not user_message:
        return jsonify({"error": "Mensaje vacío"}), 400

    memoria = read_db()
    bot_response = procesar_respuesta_autonoma(user_message, memoria)

    save_to_db("historial", {"user": user_message, "bot": bot_response})
    return jsonify({"response": bot_response, "code_3d": "", "target_canvas": ""}), 200

@app.route('/api/code-patch', methods=['POST'])
def handle_code_patch():
    """Endpoint dedicado para que la interfaz o la IA apliquen modificaciones de código en caliente."""
    data = request.get_json(silent=True) or {}
    filename = data.get('filename')
    content = data.get('content')
    
    if not filename or not content:
        return jsonify({"error": "Faltan parámetros (filename o content)"}), 400
        
    resultado = modificar_archivo_proyecto(filename, content)
    return jsonify(resultado), (200 if resultado["status"] == "success" else 400)

@app.route('/api/memories', methods=['GET'])
def get_memories():
    memoria = read_db()
    docs = memoria.get("documentos", [])
    formatted = []
    for d in docs:
        filename = d.get("file_name", "Documento")
        topic = filename.split('_')[0] if '_' in filename else "General"
        formatted.append({
            "concept": filename,
            "topic": topic,
            "details": d.get("content", "")[:120] + "..."
        })
    return jsonify(formatted), 200

@app.route('/api/upload', methods=['POST'])
def handle_pdf():
    if 'pdf' not in request.files:
        return jsonify({"error": "No hay archivo PDF"}), 400
    file = request.files['pdf']
    try:
        reader = pypdf.PdfReader(file)
        extracted_text = "".join([page.extract_text() for page in reader.pages])
        save_to_db("documentos", {"file_name": file.filename, "content": extracted_text})
        return jsonify({"message": f"El documento '{file.filename}' ha sido asimilado y expande mi base de conocimientos."}), 200
    except Exception as e:
        return jsonify({"error": "Error al procesar PDF"}), 500

if __name__ == '__main__':
    init_db()
    app.run(port=3000, debug=True)
