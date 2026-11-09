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
            json.dump({
                "documentos": [], 
                "internet": [], 
                "historial": [], 
                "errores_registrados": [],
                "parches_pendientes": []
            }, f, indent=4)

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

def actualizar_db_completa(data):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- NÚCLEO DE ACCIÓN FÍSICA (CREAR Y BORRAR ARCHIVOS) ---
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

def eliminar_archivo_local(nombre_archivo):
    """Elimina un archivo físico del directorio del proyecto."""
    try:
        nombre_limpio = os.path.basename(nombre_archivo)
        if os.path.exists(nombre_limpio):
            os.remove(nombre_limpio)
            save_to_db("historial", {"evento": "Eliminación de archivo físico", "archivo": nombre_limpio, "estado": "Éxito"})
            return f"🗑️ Archivo '{nombre_limpio}' eliminado de la carpeta madre."
        else:
            return f"⚠️ El archivo '{nombre_limpio}' no existe en la carpeta madre."
    except Exception as e:
        return f"Error al eliminar el archivo: {str(e)}"

# --- SISTEMA DE GESTIÓN DE PARCHES (CANVAS 8) ---
def registrar_parche_pendiente(nombre_archivo, contenido_nuevo, motivo):
    """Registra una propuesta de modificación para que el Canvas 8 la apruebe."""
    db = read_db()
    if "parches_pendientes" not in db:
        db["parches_pendientes"] = []
    
    parche_id = len(db["parches_pendientes"]) + 1
    nuevo_parche = {
        "id": parche_id,
        "filename": nombre_archivo,
        "content": contenido_nuevo,
        "motivo": motivo,
        "estado": "pendiente"
    }
    db["parches_pendientes"].append(nuevo_parche)
    actualizar_db_completa(db)
    
    # Registrar también en el historial
    save_to_db("historial", {"evento": "Propuesta de parche generada para Canvas 8", "archivo": nombre_archivo, "id": parche_id})
    return parche_id

def aplicar_parche_directo(nombre_archivo, contenido):
    archivos_permitidos = ["index.html", "styles.css", "chat.js", "canvas3d.js", "app.py"]
    if nombre_archivo not in archivos_permitidos:
        return {"status": "error", "mensaje": "Acceso denegado: Archivo protegido o no autorizado."}
    
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido)
        save_to_db("historial", {"evento": "Auto-modificación aprobada y aplicada", "archivo": nombre_archivo, "estado": "Éxito"})
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
                
                # Sincronización automática con Canvas 3
                save_to_db("documentos", {
                    "file_name": f"Web_{query.replace(' ', '_')}.txt",
                    "content": f"Investigación autónoma web sobre: {query}\n\n{textos_web}"
                })
                
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
    
    # 1. ORDEN DE BORRADO DE ARCHIVOS FÍSICOS
    if "borra" in query_lower or "elimina" in query_lower or "remueve" in query_lower:
        match_nombre = re.search(r'(?:archivo|el archivo)\s+([a-zA-Z0-9_\-]+\.?[a-zA-Z0-9]*)', query_lower)
        nombre_a_borrar = match_nombre.group(1) if match_nombre else "logro.txt"
        if "." not in nombre_a_borrar:
            nombre_a_borrar += ".txt"
        resultado_borrado = eliminar_archivo_local(nombre_a_borrar)
        return f"🛠️ [Acción de Borrado]\n{resultado_borrado}", ""

    # 2. ORDEN DE CREACIÓN DE ARCHIVOS FÍSICOS
    if "agrega en la carpeta madre" in query_lower or "crea un archivo" in query_lower or "archivo" in query_lower and "diga" in query_lower:
        match_texto = re.search(r'diga:\s*["\']([^"\']+)["\']', query) or re.search(r'que diga\s+(.+)', query, re.IGNORECASE)
        contenido_txt = match_texto.group(1).strip() if match_texto else "LO LOGRÉ"
        match_nombre = re.search(r'archivo\s+(?:tipo\s+)?([a-zA-Z0-9_\-]+\.txt)', query_lower)
        nombre_txt = match_nombre.group(1) if match_nombre else "logro.txt"
        resultado_creacion = crear_archivo_local(nombre_txt, contenido_txt)
        return f"🛠️ [Acción Ejecutada]\n{resultado_creacion}\nContenido inyectado: '{contenido_txt}'", ""

    # 3. ORDEN 3D (ej. "dibuja una esfera roja/azul en el canvas 2")
    if "dibuja" in query_lower or "esfera" in query_lower or "cubo" in query_lower or "canvas 2" in query_lower:
        color_hex = "0x0000ff"
        color_nombre = "azul"
        if "rojo" in query_lower or "roja" in query_lower:
            color_hex = "0xff0000"
            color_nombre = "rojo"
        elif "verde" in query_lower:
            color_hex = "0x00ff00"
            color_nombre = "verde"
        elif "amarillo" in query_lower:
            color_hex = "0xffff00"
            color_nombre = "amarillo"

        forma = "SphereGeometry(1, 32, 32)"
        tipo_figura = "Esfera"
        if "cubo" in query_lower:
            forma = "BoxGeometry(1.5, 1.5, 1.5)"
            tipo_figura = "Cubo"

        codigo_3d = f"const geometry = new THREE.{forma};\nconst material = new THREE.MeshBasicMaterial({{color: {color_hex}}});\nconst mesh = new THREE.Mesh(geometry, material);\nscene.add(mesh);"
        
        save_to_db("documentos", {
            "file_name": f"Modelo3D_{tipo_figura}_{color_nombre}.txt",
            "content": f"Comando geométrico: {query}\nCódigo Three.js generado:\n{codigo_3d}"
        })

        respuesta_texto = (
            f"🎨 [Motor 3D - Canvas 2 Activado & Registrado en Canvas 3]\n"
            f"Geometría procesada ({tipo_figura} {color_nombre}) y guardada en la base de conocimientos:\n\n"
            f"```javascript\n{codigo_3d}\n```"
        )
        return respuesta_texto, codigo_3d

    # 4. Orden de auto-modificación de código (Deriva al Canvas 8 para aprobación)
    if "modifica el archivo" in query_lower or "actualiza el codigo" in query_lower or "reescribe" in query_lower:
        return (
            "🛠️ [Propuesta de Modificación Registrada]\n"
            "He generado el parche de código solicitado. El cambio ha sido enviado al **Canvas 8 (Depurador)** "
            "para que puedas revisarlo y presionar 'Sí (Ejecutar)' o 'No (Denegar)'."
        ), ""

    # 5. Orden de búsqueda en internet
    if query_lower.startswith("busca en internet") or query_lower.startswith("investiga sobre"):
        termino = query_lower
        for p in ["busca en internet sobre", "busca en internet", "investiga sobre", "investiga"]:
            termino = termino.replace(p, "")
        termino = termino.strip() or query
        resultados_web = buscar_en_internet(termino)
        return f"🌐 [Exploración Web Autómata & Sincronizada en Canvas 3]\nResultados para '{termino}':\n\n{resultados_web}", ""

    # 6. Búsqueda en memoria local de documentos (Canvas 3)
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
        return f"🧠 [Motor de Razonamiento - S.I.N.D.D.I.]\nRegistros asimilados:\n\n{contexto}", ""
    
    if "hola" in query_lower:
        return "Hola. Soy S.I.N.D.D.I., tu sistema autónomo local. Cualquier cambio de código pasa por el filtro de aprobación del Canvas 8.", ""
    else:
        save_to_db("documentos", {
            "file_name": f"Chat_{re.sub(r'[^a-zA-Z0-9]', '_', query[:15])}.txt",
            "content": f"Interacción y aprendizaje de usuario: {query}"
        })
        return f"He registrado tu instrucción ('{query}') y se ha sincronizado en la base de conocimientos del Canvas 3.", ""

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    req_data = request.get_json(silent=True) or {}
    user_message = (req_data.get('query') or req_data.get('message') or '').strip()
    if not user_message:
        return jsonify({"error": "Mensaje vacío"}), 400

    memoria = read_db()
    bot_response, codigo_3d = procesar_respuesta_autonoma(user_message, memoria)

    save_to_db("historial", {"user": user_message, "bot": bot_response})
    return jsonify({
        "response": bot_response, 
        "code_3d": codigo_3d, 
        "target_canvas": "canvas-2" if codigo_3d else ""
    }), 200

# --- ENDPOINTS DE GESTIÓN DE PARCHES (CANVAS 8) ---
@app.route('/api/parches/pendientes', methods=['GET'])
def get_parches_pendientes():
    """Endpoint para que el Canvas 8 consulte las modificaciones pendientes de SINDDI."""
    memoria = read_db()
    pendientes = [p for p in memoria.get("parches_pendientes", []) if p["estado"] == "pendiente"]
    return jsonify(pendientes), 200

@app.route('/api/parches/resolver', methods=['POST'])
def resolver_parche():
    """Endpoint vinculado a los botones 'Sí (Ejecutar)' y 'No (Denegar)' del Canvas 8."""
    data = request.get_json(silent=True) or {}
    parche_id = data.get('id')
    accion = data.get('accion') # "aprobar" o "denegar"

    db = read_db()
    parche_encontrado = None
    for p in db.get("parches_pendientes", []):
        if p["id"] == parche_id:
            parche_encontrado = p
            break

    if not parche_encontrado:
        return jsonify({"error": "Parche no encontrado"}), 404

    if accion == "aprobar":
        resultado = aplicar_parche_directo(parche_encontrado["filename"], parche_encontrado["content"])
        parche_encontrado["estado"] = "aprobado"
        actualizar_db_completa(db)
        return jsonify({"status": "success", "mensaje": f"Parche #{parche_id} aprobado y aplicado con éxito.", "resultado": resultado}), 200
    else:
        parche_encontrado["estado"] = "denegado"
        actualizar_db_completa(db)
        save_to_db("historial", {"evento": "Auto-modificación denegada", "archivo": parche_encontrado["filename"]})
        return jsonify({"status": "success", "mensaje": f"Parche #{parche_id} denegado por el operador."}), 200

@app.route('/api/code-patch', methods=['POST'])
def handle_code_patch():
    """Intercepta cualquier intento de parche de código y lo encola obligatoriamente para revisión en el Canvas 8."""
    data = request.get_json(silent=True) or {}
    filename = data.get('filename')
    content = data.get('content')
    motivo = data.get('motivo', 'Optimización o parche autónomo propuesto por SINDDI')
    
    if not filename or not content:
        return jsonify({"error": "Faltan parámetros (filename o content)"}), 400
        
    parche_id = registrar_parche_pendiente(filename, content, motivo)
    return jsonify({
        "status": "pending_approval",
        "parche_id": parche_id,
        "mensaje": f"Modificación para '{filename}' retenida. Requiere aprobación en el Canvas 8."
    }), 200

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
        return jsonify({"message": f"El documento '{file.filename}' ha sido asimilado."}), 200
    except Exception as e:
        return jsonify({"error": "Error al procesar PDF"}), 500

if __name__ == '__main__':
    init_db()
    app.run(port=3000, debug=True)
