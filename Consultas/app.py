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
                "errores_registrados": [{"id": 42, "error": "Variable no definida en app.js", "estado": "activo"}],
                "parches_pendientes": [],
                "biblioteca_optimizada": {}
            }, f, indent=4)

def save_to_db(key, entry):
    with open(DB_PATH, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        if key not in data:
            data[key] = [] if not isinstance(data.get(key), dict) else {}
        
        if isinstance(data[key], list):
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

# --- NÚCLEO DE ACCIÓN FÍSICA (ARCHIVOS) ---
def crear_archivo_local(nombre_archivo, contenido):
    try:
        nombre_limpio = os.path.basename(nombre_archivo)
        with open(nombre_limpio, 'w', encoding='utf-8') as f:
            f.write(contenido)
        save_to_db("historial", {"evento": "Creación de archivo físico", "archivo": nombre_limpio, "estado": "Éxito"})
        return f"📁 Archivo '{nombre_limpio}' creado exitosamente en la carpeta madre."
    except Exception as e:
        return f"Error al crear el archivo físico: {str(e)}"

def eliminar_archivo_local(nombre_archivo):
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
    return parche_id

def aplicar_parche_directo(nombre_archivo, contenido):
    archivos_permitidos = ["index.html", "styles.css", "chat.js", "canvas3d.js", "app.py"]
    if nombre_archivo not in archivos_permitidos:
        return {"status": "error", "mensaje": "Acceso denegado: Archivo protegido."}
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido)
        save_to_db("historial", {"evento": "Auto-modificación aprobada", "archivo": nombre_archivo, "estado": "Éxito"})
        return {"status": "success", "mensaje": f"Archivo '{nombre_archivo}' modificado correctamente."}
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

# --- BIBLIOTECA INTELIGENTE Y ORGANIZACIÓN DEL CANVAS 3 ---
def clasificar_y_organizar_memoria(titulo, contenido):
    """Organiza automáticamente los aprendizajes en categorías para optimizar la lectura de SINDDI."""
    db = read_db()
    if "biblioteca_optimizada" not in db:
        db["biblioteca_optimizada"] = {"3D_Assets": [], "Logica_Sistema": [], "Investigacion_Web": [], "General": []}
    
    categoria = "General"
    titulo_lower = titulo.lower()
    if "3d" in titulo_lower or "modelo" in titulo_lower or "geometria" in titulo_lower or "canvas" in titulo_lower:
        categoria = "3D_Assets"
    elif "app" in titulo_lower or "error" in titulo_lower or "codigo" in titulo_lower:
        categoria = "Logica_Sistema"
    elif "web" in titulo_lower or "busqueda" in titulo_lower:
        categoria = "Investigacion_Web"

    db["biblioteca_optimizada"][categoria].append({
        "titulo": titulo,
        "extracto": contenido[:300],
        "timestamp": "2026-11-09"
    })
    actualizar_db_completa(db)

# --- BÚSQUEDA WEB AUTÓNOMA ---
def buscar_en_internet(query):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            if results:
                textos_web = "\n".join([f"• Fuente: {r['href']}\n  Dato: {r['body']}" for r in results])
                clasificar_y_organizar_memoria(f"Web_{query}", textos_web)
                save_to_db("internet", {"query": query, "resultado": textos_web})
                return textos_web
            return "No se encontraron resultados web recientes."
    except Exception as e:
        return "No se pudo conectar a internet."

# --- MOTOR DE DIBUJO AVANZADO Y ANIMACIÓN 3D PBR ---
def generar_modelo_avanzado(query_lower):
    """Genera mallas 3D complejas con animaciones suaves y texturas estructuradas."""
    color_hex = "0x00d2ff"
    tipo_figura = "Modelo Avanzado PBR"
    
    if "rojo" in query_lower or "roja" in query_lower:
        color_hex = "0xff3366"
    elif "verde" in query_lower:
        color_hex = "0x00ff99"
    elif "dorado" in query_lower or "amarillo" in query_lower:
        color_hex = "0xffd700"

    if "esfera" in query_lower:
        geometria = "SphereGeometry(1.2, 64, 64)"
        tipo_figura = "Esfera Orgánica PBR"
    elif "cubo" in query_lower or "cuadrado" in query_lower:
        geometria = "BoxGeometry(1.5, 1.5, 1.5)"
        tipo_figura = "Cubo Arquitectónico"
    elif "cilindro" in query_lower:
        geometria = "CylinderGeometry(0.8, 0.8, 2, 32)"
        tipo_figura = "Cilindro Dinámico"
    else:
        geometria = "IcosahedronGeometry(1.2, 2)"
        tipo_figura = "Icosaedro Poligonal Avanzado"

    codigo_3d = f"""
    const geometry = new THREE.{geometria};
    const material = new THREE.MeshStandardMaterial({{
        color: {color_hex},
        roughness: 0.2,
        metalness: 0.8,
        wireframe: false
    }});
    const mesh = new THREE.Mesh(geometry, material);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    scene.add(mesh);
    
    // Animación de rotación fluida autónoma sincronizada
    function animarAsset() {{
        requestAnimationFrame(animarAsset);
        mesh.rotation.x += 0.005;
        mesh.rotation.y += 0.008;
    }}
    animarAsset();
    """
    return codigo_3d, tipo_figura

# --- PROCESAMIENTO INTELIGENTE ---
def procesar_respuesta_autonoma(query, memoria):
    query_lower = query.lower()
    documentos = memoria.get("documentos", [])
    
    # 1. LIMPIEZA DE CANVAS (2, 4, 7)
    if "canvas" in query_lower and ("borra" in query_lower or "limpia" in query_lower or "elimina" in query_lower):
        match_canvas = re.search(r'canvas\s*([0-9]+)', query_lower)
        num_canvas = match_canvas.group(1) if match_canvas else "2"
        codigo_limpieza = "while(scene.children.length > 0){ scene.remove(scene.children[0]); }"
        return f"🧹 [Canvas {num_canvas} Limpiado]\nEscena gráfica restablecida.", codigo_limpieza, f"canvas-{num_canvas}"

    # 2. CONSULTAS DEL CANVAS 8 / DEPURADOR DE ERRORES Y AUTOCORRECCIÓN
    if "canvas 8" in query_lower or "error" in query_lower or "depurador" in query_lower or "corrige el error" in query_lower:
        codigo_parche = (
            "// Parche automático de S.I.N.D.D.I. para app.js\n"
            "const variableCanvas8 = typeof variableCanvas8 !== 'undefined' ? variableCanvas8 : 'Optimizado_SINDDI';\n"
            "console.log('Canvas 8: Sistema depurado y sincronizado.');\n"
        )
        parche_id = registrar_parche_pendiente("app.js", codigo_parche, "Corrección automática del Error [REF-42]")
        respuesta = (
            f"🔍 [Canvas 8 - Depurador y Corrección Autónoma]\n"
            f"Se ha diagnosticado y generado el parche #{parche_id} para solucionar la incidencia en `app.js`.\n"
            f"Revisa el panel del Canvas 8 y haz clic en **'Sí (Ejecutar)'** para aplicar el cambio."
        )
        return respuesta, "", "canvas-8"

    # 3. GESTIÓN DE ARCHIVOS FÍSICOS
    if "archivo" in query_lower and ("borra" in query_lower or "elimina" in query_lower):
        match_nombre = re.search(r'(?:archivo|el archivo)\s+([a-zA-Z0-9_\-]+\.?[a-zA-Z0-9]*)', query_lower)
        nombre_a_borrar = match_nombre.group(1) if match_nombre else "logro.txt"
        if "." not in nombre_a_borrar:
            nombre_a_borrar += ".txt"
        return f"🛠️ [Acción de Borrado]\n{eliminar_archivo_local(nombre_a_borrar)}", "", ""

    if "agrega en la carpeta madre" in query_lower or ("crea" in query_lower and "archivo" in query_lower):
        match_texto = re.search(r'diga:\s*["\']([^"\']+)["\']', query) or re.search(r'que diga\s+(.+)', query, re.IGNORECASE)
        contenido_txt = match_texto.group(1).strip() if match_texto else "LO LOGRÉ"
        match_nombre = re.search(r'archivo\s+(?:tipo\s+)?([a-zA-Z0-9_\-]+\.txt)', query_lower)
        nombre_txt = match_nombre.group(1) if match_nombre else "logro.txt"
        return f"🛠️ [Acción Ejecutada]\n{crear_archivo_local(nombre_txt, contenido_txt)}", "", ""

    # 4. MOTOR DE DIBUJO 3D AVANZADO (Canvas 2, 4 o 7)
    if any(verbo in query_lower for verbo in ["dibuja", "renderiza", "modela", "crea", "muestra"]) or ("canvas" in query_lower and any(fig in query_lower for fig in ["esfera", "cubo", "cuadrado", "cilindro", "objeto", "figura"])):
        match_canvas = re.search(r'canvas\s*([0-9]+)', query_lower)
        num_canvas = match_canvas.group(1) if match_canvas else "2"
        
        codigo_3d, tipo_figura = generar_modelo_avanzado(query_lower)
        
        clasificar_y_organizar_memoria(f"Asset_{tipo_figura}_Canvas{num_canvas}", f"Modelo 3D renderizado: {tipo_figura} con animación PBR.")

        respuesta_texto = (
            f"🎨 [S.I.N.D.D.I. Studio - Render PBR Avanzado (Canvas {num_canvas})]\n"
            f"Asset generado: **{tipo_figura}** con iluminación y rotación sincronizada para el **Canvas {num_canvas}**:\n\n"
            f"```javascript\n{codigo_3d}\n```"
        )
        return respuesta_texto, codigo_3d, f"canvas-{num_canvas}"

    # 5. BÚSQUEDA WEB
    if query_lower.startswith("busca en internet") or query_lower.startswith("investiga sobre"):
        termino = query_lower.replace("busca en internet sobre", "").replace("investiga sobre", "").strip() or query
        resultado_web = buscar_en_internet(termino)
        return f"🌐 [Exploración Web & Optimización de Biblioteca]\n{resultado_web}", "", ""

    # 6. RAZONAMIENTO GENERAL CON CANVAS 3 OPTIMIZADO
    clasificar_y_organizar_memoria(f"Interaccion_{query[:15]}", query)
    return f"🧠 [Motor de Razonamiento - S.I.N.D.D.I.]\nProceso completado. Datos organizados y optimizados en la biblioteca del Canvas 3.", "", ""

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    req_data = request.get_json(silent=True) or {}
    user_message = (req_data.get('query') or req_data.get('message') or '').strip()
    if not user_message:
        return jsonify({"error": "Mensaje vacío"}), 400

    memoria = read_db()
    bot_response, codigo_3d, target_canvas = procesar_respuesta_autonoma(user_message, memoria)

    save_to_db("historial", {"user": user_message, "bot": bot_response})
    return jsonify({
        "response": bot_response, 
        "code_3d": codigo_3d, 
        "target_canvas": target_canvas
    }), 200

# --- ENDPOINTS DE GESTIÓN DE PARCHES (CANVAS 8) ---
@app.route('/api/parches/pendientes', methods=['GET'])
def get_parches_pendientes():
    memoria = read_db()
    pendientes = [p for p in memoria.get("parches_pendientes", []) if p["estado"] == "pendiente"]
    return jsonify(pendientes), 200

@app.route('/api/parches/resolver', methods=['POST'])
def resolver_parche():
    data = request.get_json(silent=True) or {}
    parche_id = data.get('id')
    accion = data.get('accion')

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
    data = request.get_json(silent=True) or {}
    filename = data.get('filename')
    content = data.get('content')
    motivo = data.get('motivo', 'Optimización propuesta por SINDDI')
    
    if not filename or not content:
        return jsonify({"error": "Faltan parámetros"}), 400
        
    parche_id = registrar_parche_pendiente(filename, content, motivo)
    return jsonify({
        "status": "pending_approval",
        "parche_id": parche_id,
        "mensaje": f"Modificación retenida. Requiere aprobación en el Canvas 8."
    }), 200

@app.route('/api/memories', methods=['GET'])
def get_memories():
    memoria = read_db()
    # Devolver biblioteca categorizada para el Canvas 3
    biblioteca = memoria.get("biblioteca_optimizada", {})
    formatted = []
    for categoria, items in biblioteca.items():
        for item in items:
            formatted.append({
                "concept": item["titulo"],
                "topic": categoria,
                "details": item["extracto"]
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
        clasificar_y_organizar_memoria(file.filename, extracted_text)
        return jsonify({"message": f"Documento '{file.filename}' asimilado y categorizado en Canvas 3."}), 200
    except Exception as e:
        return jsonify({"error": "Error al procesar PDF"}), 500

if __name__ == '__main__':
    init_db()
    app.run(port=3000, debug=True)
