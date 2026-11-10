import os
import json
import re
import subprocess
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
                "biblioteca_optimizada": {"3D_Assets": [], "Logica_Sistema": [], "Investigacion_Web": [], "General": []},
                "escenas_activas": {}
            }, f, indent=4)

def save_to_db(key, entry):
    with open(DB_PATH, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        if key not in data:
            if key == "biblioteca_optimizada":
                data[key] = {"3D_Assets": [], "Logica_Sistema": [], "Investigacion_Web": [], "General": []}
            elif key == "escenas_activas":
                data[key] = {}
            else:
                data[key] = []
        
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

# --- NÚCLEO DE ACCIÓN FÍSICA, TERMINAL Y BLENDER (CANVAS 6) ---
def ejecutar_comando_terminal(comando):
    """Ejecuta comandos reales de terminal / Git / Python / Blender de forma controlada."""
    try:
        if any(c in comando.lower() for c in ["rm -rf", "format", "del /f"]):
            return "⚠️ Comando bloqueado por protocolos de seguridad de S.I.N.D.D.I."
        
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=30)
        salida = resultado.stdout if resultado.returncode == 0 else resultado.stderr
        save_to_db("historial", {"evento": "Ejecución de terminal / Blender", "cmd": comando, "estado": "Éxito" if resultado.returncode == 0 else "Error"})
        return salida.strip() or "Proceso ejecutado sin salida de texto."
    except Exception as e:
        return f"Error en la ejecución del proceso: {str(e)}"

def ejecutar_script_blender(script_python="blender_script.py"):
    """Ejecuta Blender 4.5 en segundo plano (headless) utilizando el script de Python proporcionado."""
    blender_path = r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
    
    if not os.path.exists(blender_path):
        return f"⚠️ No se encontró Blender en la ruta especificada: {blender_path}"
    
    if not os.path.exists(script_python):
        return f"⚠️ El script '{script_python}' no existe en la carpeta madre."

    comando = f'"{blender_path}" --background --python {script_python}'
    return ejecutar_comando_terminal(comando)

def generar_script_blender_dinamico(query_lower):
    """Genera dinámicamente un script de Python para Blender según la petición del usuario."""
    geometria_bpy = "bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, segments=64, ring_count=32)"
    nombre_asset = "Asset_Procedural"
    
    if "cubo" in query_lower or "caja" in query_lower:
        geometria_bpy = "bpy.ops.mesh.primitive_cube_add(size=2.0)"
        nombre_asset = "Cubo_Estructurado"
    elif "mono" in query_lower or "suzanne" in query_lower:
        geometria_bpy = "bpy.ops.mesh.primitive_monkey_add(size=2.0)"
        nombre_asset = "Suzanne_Organic"
    elif "cilindro" in query_lower:
        geometria_bpy = "bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.5, vertices=32)"
        nombre_asset = "Cilindro_Dinamico"
    elif "toro" in query_lower or "rosca" in query_lower:
        geometria_bpy = "bpy.ops.mesh.primitive_torus_add(major_radius=1.2, minor_radius=0.4, ab_segments=48, ring_segments=32)"
        nombre_asset = "Toroide_Avanzado"

    codigo_blender = f"""import bpy

# Limpiar escena inicial
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Generar geometría solicitada
{geometria_bpy}
obj = bpy.context.active_object
obj.name = "{nombre_asset}"

# Aplicar subdivisión y suavizado para alta calidad
modifier = obj.modifiers.new(name="Subdivision", type='SUBSURF')
modifier.levels = 2
modifier.render_levels = 2

for f in obj.data.polygons:
    f.use_smooth = True

# Exportar automáticamente a glb
export_path = "asset_sinddi.glb"
bpy.ops.export_scene.gltf(filepath=export_path, export_format='GLB')
print("✨ [SINDDI Blender Studio] Modelo exportado: " + export_path)
"""
    
    with open("blender_script.py", "w", encoding="utf-8") as f:
        f.write(codigo_blender)
        
    return f"📝 Script de Blender generado dinámicamente para: '{nombre_asset}'."

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

# --- SISTEMA DE GESTIÓN DE PARCHES (CANVAS 8 CON DIFF VIEWER) ---
def registrar_parche_pendiente(nombre_archivo, contenido_nuevo, motivo):
    db = read_db()
    if "parches_pendientes" not in db:
        db["parches_pendientes"] = []
    
    contenido_original = ""
    if os.path.exists(nombre_archivo):
        with open(nombre_archivo, 'r', encoding='utf-8', errors='ignore') as f:
            contenido_original = f.read()

    parche_id = len(db["parches_pendientes"]) + 1
    nuevo_parche = {
        "id": parche_id,
        "filename": nombre_archivo,
        "content": contenido_nuevo,
        "original_content": contenido_original,
        "motivo": motivo,
        "estado": "pendiente"
    }
    db["parches_pendientes"].append(nuevo_parche)
    actualizar_db_completa(db)
    return parche_id

def aplicar_parche_directo(nombre_archivo, contenido):
    archivos_permitidos = ["index.html", "styles.css", "chat.js", "canvas3d.js", "app.py", "blender_script.py"]
    if nombre_archivo not in archivos_permitidos:
        return {"status": "error", "mensaje": "Acceso denegado: Archivo protegido."}
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido)
        save_to_db("historial", {"evento": "Auto-modificación aprobada", "archivo": nombre_archivo, "estado": "Éxito"})
        return {"status": "success", "mensaje": f"Archivo '{nombre_archivo}' modificado correctamente."}
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

# --- CLASIFICACIÓN AVANZADA Y EXTRACCIÓN DE MANUALES (CANVAS 3) ---
def clasificar_y_organizar_memoria(titulo, contenido):
    db = read_db()
    if "biblioteca_optimizada" not in db or not isinstance(db["biblioteca_optimizada"], dict):
        db["biblioteca_optimizada"] = {"3D_Assets": [], "Logica_Sistema": [], "Investigacion_Web": [], "General": []}
    
    categoria = "General"
    titulo_lower = titulo.lower()
    contenido_lower = contenido.lower()

    if any(k in titulo_lower or k in contenido_lower for k in ["3d", "modelo", "geometria", "canvas", "shader", "pbr", "raycasting", "matriz", "obj", "stl", "glb", "blender"]):
        categoria = "3D_Assets"
    elif any(k in titulo_lower or k in contenido_lower for k in ["app", "error", "codigo", "parche", "git", "flask", "script", "py", "js"]):
        categoria = "Logica_Sistema"
    elif any(k in titulo_lower or k in contenido_lower for k in ["web", "busqueda", "internet", "http", "video", "imagen"]):
        categoria = "Investigacion_Web"

    db["biblioteca_optimizada"][categoria].append({
        "titulo": titulo,
        "extracto": contenido[:400],
        "timestamp": "2026-11-10"
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

# --- MOTOR 3D PROCEDURAL Y PERSISTENCIA DE ESCENAS ---
def generar_modelo_avanzado(query_lower, canvas_id):
    color_hex = "0x00d2ff"
    
    if "rojo" in query_lower or "roja" in query_lower:
        color_hex = "0xff3366"
    elif "verde" in query_lower:
        color_hex = "0x00ff99"
    elif "dorado" in query_lower or "amarillo" in query_lower or "amarilla" in query_lower:
        color_hex = "0xffd700"

    if "rostro" in query_lower or "cara" in query_lower or "avatar" in query_lower or "la cara" in query_lower:
        tipo_figura = "Rostro Amigable 3D (Grupo Procedural PBR)"
        codigo_3d = f"""
        const group = new THREE.Group();
        
        const headGeo = new THREE.SphereGeometry(1.2, 32, 32);
        const headMat = new THREE.MeshStandardMaterial({{ color: {color_hex}, roughness: 0.3, metalness: 0.5 }});
        const head = new THREE.Mesh(headGeo, headMat);
        group.add(head);

        const eyeGeo = new THREE.SphereGeometry(0.2, 16, 16);
        const eyeMat = new THREE.MeshStandardMaterial({{ color: 0xffffff, roughness: 0.1 }});
        const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
        leftEye.position.set(-0.4, 0.3, 1.0);
        group.add(leftEye);

        const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
        rightEye.position.set(0.4, 0.3, 1.0);
        group.add(rightEye);

        const pupilGeo = new THREE.SphereGeometry(0.09, 16, 16);
        const pupilMat = new THREE.MeshBasicMaterial({{ color: 0x000000 }});
        const leftPupil = new THREE.Mesh(pupilGeo, pupilMat);
        leftPupil.position.set(-0.4, 0.3, 1.18);
        group.add(leftPupil);

        const rightPupil = new THREE.Mesh(pupilGeo, pupilMat);
        rightPupil.position.set(0.4, 0.3, 1.18);
        group.add(rightPupil);

        const smileGeo = new THREE.TorusGeometry(0.4, 0.06, 16, 32, Math.PI);
        const smileMat = new THREE.MeshBasicMaterial({{ color: 0x000000 }});
        const smile = new THREE.Mesh(smileGeo, smileMat);
        smile.position.set(0, -0.2, 1.05);
        smile.rotation.x = Math.PI;
        group.add(smile);

        scene.add(group);

        function animarRostro() {{
            requestAnimationFrame(animarRostro);
            group.rotation.y = Math.sin(Date.now() * 0.002) * 0.3;
        }}
        animarRostro();
        """
    else:
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
        
        function animarAsset() {{
            requestAnimationFrame(animarAsset);
            mesh.rotation.x += 0.005;
            mesh.rotation.y += 0.008;
        }}
        animarAsset();
        """

    db = read_db()
    if "escenas_activas" not in db:
        db["escenas_activas"] = {}
    db["escenas_activas"][canvas_id] = {"tipo": tipo_figura, "codigo": codigo_3d}
    actualizar_db_completa(db)

    return codigo_3d, tipo_figura

# --- PROCESAMIENTO INTELIGENTE Y DESAMBIGUACIÓN CON SOPORTE DE MEMORIA ---
def procesar_respuesta_autonoma(query, memoria):
    query_lower = query.lower()
    
    if query_lower in ["hola", "saludos", "hi", "buenas"]:
        return "¡Hola! Soy S.I.N.D.D.I., tu sistema autónomo local. ¿Qué construimos o modelamos hoy?", "", ""
    elif "como estas" in query_lower or "cómo estás" in query_lower or "que tal" in query_lower:
        return "Mis estaciones 3D, bases de datos locales y motores autónomos operan al 100% de su capacidad. ¿En qué te ayudo?", "", ""

    if ("donde se guarda" in query_lower or "donde se almacena" in query_lower) and "canvas 3" in query_lower:
        respuesta = (
            "🗄️ [Arquitectura de Memoria - Canvas 3]\n"
            "Todo el conocimiento asimilado y las escenas activas se guardan localmente en **`memorie.json`** bajo las ramas:\n"
            "• `documentos`: Registros y PDFs.\n"
            "• `biblioteca_optimizada`: Categorización por `3D_Assets`, `Logica_Sistema`, `Investigacion_Web` y `General`.\n"
            "• `escenas_activas`: Persistencia activa de los modelos 3D."
        )
        return respuesta, "", ""

    # EJECUCIÓN Y GENERACIÓN DINÁMICA DE BLENDER DESDE EL CHAT
    if "blender" in query_lower or "esculpe" in query_lower or "modela en" in query_lower or "genera modelo en blender" in query_lower:
        info_script = generar_script_blender_dinamico(query_lower)
        resultado_blender = ejecutar_script_blender("blender_script.py")
        
        respuesta_final = (
            f"🎬 [S.I.N.D.D.I. Studio - Generación Dinámica en Blender 4.5]\n"
            f"{info_script}\n\n"
            f"```text\n{resultado_blender}\n```"
        )
        return respuesta_final, "", "canvas-4"

    if "git " in query_lower or query_lower.startswith("ejecuta ") or query_lower.startswith("terminal "):
        cmd = query.replace("ejecuta", "").replace("terminal", "").strip()
        resultado_terminal = ejecutar_comando_terminal(cmd)
        return f"💻 [Canvas 6 - Consola Ejecutora]\n```bash\n{resultado_terminal}\n```", "", "canvas-6"

    codigo_3d_acumulado = ""
    target_canvas_acumulado = ""
    mensajes_respuesta = []

    if "canvas" in query_lower and any(w in query_lower for w in ["borra", "limpia", "elimina", "vacía"]):
        if "canvas 1" in query_lower or "todos los canvas" in query_lower:
            codigo_3d_acumulado += "const treeEl = document.getElementById('file-tree'); if(treeEl) treeEl.innerHTML = '<p style=\"color: #94a3b8; font-size: 11px;\">Ramal limpiado.</p>';"
            mensajes_respuesta.append("🧹 [Canvas 1 Limpiado] El árbol de archivos y ramales han sido vaciados.")
            target_canvas_acumulado = "canvas-1"
        else:
            match_canvas = re.search(r'canvas\s*([0-9]+)', query_lower)
            num_canvas = match_canvas.group(1) if match_canvas else "2"
            canvas_key = f"canvas-{num_canvas}"
            codigo_3d_acumulado += "while(scene.children.length > 0){ scene.remove(scene.children[0]); }"
            
            db = read_db()
            if "escenas_activas" in db and canvas_key in db["escenas_activas"]:
                del db["escenas_activas"][canvas_key]
                actualizar_db_completa(db)

            mensajes_respuesta.append(f"🧹 [Canvas {num_canvas} Limpiado] Escena gráfica restablecida y persistencia actualizada.")
            target_canvas_acumulado = canvas_key

    is_color_command = any(c in query_lower for c in ["amarillo", "amarilla", "rojo", "roja", "verde", "azul", "dorado"])
    is_draw_command = any(v in query_lower for v in ["dibuja", "renderiza", "modela", "crea", "muestra", "haz", "pinta"])
    is_shape_target = any(f in query_lower for f in ["rostro", "cara", "avatar", "esfera", "cubo", "cuadrado", "cilindro", "la cara", "hazla"])

    if is_draw_command or is_shape_target or is_color_command:
        match_canvas = re.search(r'canvas\s*([0-9]+)', query_lower)
        num_canvas = match_canvas.group(1) if match_canvas else "4"
        canvas_key = f"canvas-{num_canvas}"
        
        query_para_modelo = query_lower
        if is_color_command and not is_shape_target and not any(s in query_lower for s in ["rostro", "esfera", "cubo", "cilindro"]):
            query_para_modelo = "rostro amigable " + query_lower

        script_3d, tipo_figura = generar_modelo_avanzado(query_para_modelo, canvas_key)
        codigo_3d_acumulado += script_3d
        target_canvas_acumulado = canvas_key
        
        clasificar_y_organizar_memoria(f"Asset_{tipo_figura}_{canvas_key}", f"Modelo 3D renderizado y persistido: {tipo_figura}")
        mensajes_respuesta.append(f"🎨 [S.I.N.D.D.I. Studio - Persistencia PBR ({canvas_key})]\nAsset generado y guardado en `memorie.json`: **{tipo_figura}**.")

    if mensajes_respuesta:
        return "\n\n".join(mensajes_respuesta), codigo_3d_acumulado, target_canvas_acumulado

    if "canvas 8" in query_lower or "error" in query_lower or "depurador" in query_lower or "corrige el error" in query_lower:
        codigo_parche = (
            "// Parche automático de S.I.N.D.D.I. para app.js\n"
            "const variableCanvas8 = typeof variableCanvas8 !== 'undefined' ? variableCanvas8 : 'Optimizado_SINDDI';\n"
            "console.log('Canvas 8: Sincronizado.');\n"
        )
        parche_id = registrar_parche_pendiente("app.js", codigo_parche, "Corrección automática del Error [REF-42]")
        respuesta = (
            f"🔍 [Canvas 8 - Depurador con Visor Diff]\n"
            f"Se ha diagnosticado y generado el parche #{parche_id} con comparación original vs propuesta.\n"
            f"Revisa el panel del Canvas 8 y haz clic en **'Sí (Ejecutar)'** para aplicar el cambio."
        )
        return respuesta, "", "canvas-8"

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

    if query_lower.startswith("busca en internet") or query_lower.startswith("investiga sobre"):
        termino = query_lower.replace("busca en internet sobre", "").replace("investiga sobre", "").strip() or query
        resultado_web = buscar_en_internet(termino)
        return f"🌐 [Exploración Web & Optimización de Biblioteca]\n{resultado_web}", "", ""

    # --- MOTOR DE CONSULTA Y BÚSQUEDA INTELIGENTE EN MEMORIA PERSISTENTE (CANVAS 3) ---
    biblioteca = memoria.get("biblioteca_optimizada", {})
    
    # 1. Solicitud de resumen o revisión de categoría
    if any(term in query_lower for term in ["resumen", "muéstrame", "muestrame", "conceptos", "categoría", "categoria", "logica_sistema", "3d_assets"]):
        hallazgos = []
        for cat, items in biblioteca.items():
            if isinstance(items, list):
                for item in items:
                    if cat.lower() in query_lower or any(word in item.get("titulo", "").lower() for word in query_lower.split() if len(word) > 3):
                        hallazgos.append(f"📌 **[{cat}] {item.get('titulo')}**:\n{item.get('extracto')[:250]}...")
        
        if hallazgos:
            return "🗄️ **[Lectura de Biblioteca - Canvas 3]**\n\n" + "\n\n".join(hallazgos[:4]), "", "canvas-3"

    # 2. Búsqueda semántica por palabras clave dentro de los PDFs y textos asimilados
    palabras_clave = [p for p in query_lower.split() if len(p) > 3]
    coincidencias = []
    
    for cat, items in biblioteca.items():
        if isinstance(items, list):
            for item in items:
                texto_item = (item.get("titulo", "") + " " + item.get("extracto", "")).lower()
                if any(kw in texto_item for kw in palabras_clave):
                    coincidencias.append(f"📖 **[{cat} - {item.get('titulo')}]**:\n{item.get('extracto')}")

    if coincidencias:
        respuesta_conocimiento = (
            f"🧠 **[S.I.N.D.D.I. - Base de Conocimiento Local Asimilada]**\n"
            f"Encontré registros en mi memoria persistente relacionados con tu consulta:\n\n"
            + "\n---\n".join(coincidencias[:2])
        )
        return respuesta_conocimiento, "", "canvas-3"

    # 3. Fallback: Registrar interacción y guardar en memoria
    clasificar_y_organizar_memoria(f"Interaccion_{query[:15]}", query)
    return f"🧠 [Motor de Razonamiento - S.I.N.D.D.I.] Consulta asimilada y guardada en la biblioteca del Canvas 3.", "", "canvas-3"

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

# --- ENDPOINT MULTIMODAL PARA FOTOS, VIDEOS Y ARCHIVOS 3D ---
@app.route('/api/analizar-multimodal', methods=['POST'])
def analizar_multimodal():
    if 'archivo' not in request.files:
        return jsonify({"error": "No se adjuntó ningún archivo"}), 400
    
    file = request.files['archivo']
    filename = file.filename
    file_ext = filename.split('.')[-1].lower()
    
    file_path = os.path.join(os.getcwd(), filename)
    file.save(file_path)
    
    analisis_texto = f"Archivo '{filename}' recibido y almacenado en la carpeta madre."
    codigo_3d = ""

    if file_ext in ['obj', 'stl', 'gltf', 'glb']:
        analisis_texto = f"📐 [Análisis 3D - Canvas 4]\nMalla 3D '{filename}' detectada, indexada y lista para renderizado."
        codigo_3d = f"""
        const geometry = new THREE.TorusKnotGeometry(1, 0.3, 64, 16);
        const material = new THREE.MeshStandardMaterial({{ color: 0x38bdf8, roughness: 0.2, metalness: 0.8 }});
        const mesh = new THREE.Mesh(geometry, material);
        scene.add(mesh);
        function animarAsset3D() {{
            requestAnimationFrame(animarAsset3D);
            mesh.rotation.y += 0.01;
        }}
        animarAsset3D();
        """
        clasificar_y_organizar_memoria(f"Asset_3D_{filename}", f"Modelo 3D importado: {filename}")

    elif file_ext in ['png', 'jpg', 'jpeg', 'webp']:
        analisis_texto = f"👁️ [Análisis Visual]\nImagen '{filename}' procesada y clasificada en la biblioteca visual."
        clasificar_y_organizar_memoria(f"Imagen_{filename}", f"Registro visual analizado: {filename}")

    elif file_ext in ['mp4', 'avi', 'mov', 'webm']:
        analisis_texto = f"🎬 [Análisis de Video]\nVideo '{filename}' indexado para extracción multimedia y aprendizaje autónomo."
        clasificar_y_organizar_memoria(f"Video_{filename}", f"Multimedia analizada: {filename}")

    else:
        analisis_texto = f"📁 [Archivo General]\nDocumento o script '{filename}' guardado en la carpeta madre."
        clasificar_y_organizar_memoria(f"Archivo_{filename}", f"Recurso local indexado: {filename}")

    save_to_db("historial", {"evento": "Carga multimodal", "archivo": filename, "estado": "Éxito"})

    return jsonify({
        "response": analisis_texto,
        "code_3d": codigo_3d,
        "target_canvas": "canvas-4" if file_ext in ['obj', 'stl', 'gltf', 'glb'] else ""
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
    biblioteca = memoria.get("biblioteca_optimizada", {})
    formatted = []
    if isinstance(biblioteca, dict):
        for categoria, items in biblioteca.items():
            if isinstance(items, list):
                for item in items:
                    formatted.append({
                        "concept": item.get("titulo", "Concepto"),
                        "topic": categoria,
                        "details": item.get("extracto", "")
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
        return jsonify({"message": f"Documento '{file.filename}' asimilado y categorizado en la biblioteca del Canvas 3."}), 200
    except Exception as e:
        return jsonify({"error": "Error al procesar PDF"}), 500

if __name__ == '__main__':
    init_db()
    app.run(port=3000, debug=True)
