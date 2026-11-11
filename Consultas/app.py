import os
import json
import re
import subprocess
import py_compile
import time
import threading
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS
import pypdf
import numpy as np
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama

app = Flask(__name__)
CORS(app)

DB_PATH = "memorie.json"
MODEL_PATH = "sinddi_brain.gguf"
VECTOR_DB_PATH = "vectores_memoria.npy"
GODOT_PATH = r"C:\Program Files\Godot\Godot_v4.4_win64.exe"  # Ajusta si tu ruta difiere

# --- CARGA DEL CEREBRO NATIVO EN MEMORIA (AUTONOMÍA TOTAL) ---
print("🧠 S.I.N.D.D.I. Core: Cargando el modelo GGUF directamente en RAM (CPU Ryzen)...")
try:
    llm_brain = Llama(
        model_path=MODEL_PATH,
        n_ctx=4096,
        n_threads=4,
        n_batch=512,
        verbose=False
    )
    print("✨ S.I.N.D.D.I. Core: Modelo de lenguaje nativo inicializado con éxito.")
except Exception as e:
    llm_brain = None
    print(f"⚠️ S.I.N.D.D.I. Core: No se pudo cargar '{MODEL_PATH}'. Asegúrate de tener el archivo en la carpeta madre. Error: {e}")

# --- INICIALIZACIÓN DEL MOTOR RAG VECORIAL (NUMPY) ---
print("🧬 S.I.N.D.D.I. RAG: Cargando modelo de vectores local en CPU...")
try:
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    print("✨ S.I.N.D.D.I. RAG: Motor vectorial inicializado con éxito.")
except Exception as e:
    embedder = None
    print(f"⚠️ S.I.N.D.D.I. RAG Error: No se pudo cargar el modelo vectorial: {e}")


def init_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({
                "documentos": [], 
                "internet": [], 
                "historial": [], 
                "errores_registrados": [],
                "parches_pendientes": [],
                "biblioteca_optimizada": {"3D_Assets": [], "Logica_Sistema": [], "Investigacion_Web": [], "General": []},
                "vector_store_meta": [],
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


# --- SUBSISTEMA RAG MATEMÁTICO (NUMPY & COSINE SIMILARITY) ---
def guardar_vector_memoria(texto, metadata):
    if not embedder:
        return
    
    vector = embedder.encode(texto).astype(np.float32)
    
    db = read_db()
    if "vector_store_meta" not in db:
        db["vector_store_meta"] = []
    
    db["vector_store_meta"].append({
        "metadata": metadata,
        "extracto": texto[:400],
        "index": len(db["vector_store_meta"])
    })
    actualizar_db_completa(db)
    
    if os.path.exists(VECTOR_DB_PATH):
        matriz_actual = np.load(VECTOR_DB_PATH)
        matriz_nueva = np.vstack([matriz_actual, vector])
    else:
        matriz_nueva = np.array([vector], dtype=np.float32)
        
    np.save(VECTOR_DB_PATH, matriz_nueva)

def buscar_contexto_semantico(query, top_k=2):
    if not embedder or not os.path.exists(VECTOR_DB_PATH):
        return "Sin registros vectoriales previos."
        
    db = read_db()
    metadatos = db.get("vector_store_meta", [])
    if not metadatos:
        return "Sin registros vectoriales previos."
        
    vector_query = embedder.encode(query).astype(np.float32)
    matriz_vectores = np.load(VECTOR_DB_PATH)
    
    dot_product = np.dot(matriz_vectores, vector_query)
    norm_matriz = np.linalg.norm(matriz_vectores, axis=1)
    norm_query = np.linalg.norm(vector_query)
    
    norm_matriz[norm_matriz == 0] = 1e-10
    if norm_query == 0:
        norm_query = 1e-10
        
    similitudes = dot_product / (norm_matriz * norm_query)
    mejores_indices = np.argsort(similitudes)[::-1][:top_k]
    
    resultados = []
    for idx in mejores_indices:
        score = similitudes[idx]
        if score > 0.20:
            item = metadatos[idx]
            resultados.append(f"📖 **[Similitud Semántica: {score:.2f} - {item['metadata']}]**:\n{item['extracto']}")
            
    return "\n---\n".join(resultados) if resultados else "Sin coincidencias semánticas relevantes."


# --- BUCLE COGNITIVO (ReAct: REASON + ACT) ---
def bucle_cognitivo_sinddi(query_usuario, llm_engine):
    """
    Ejecuta el Bucle Cognitivo de 4 Fases antes de actuar:
    1. Verificación de Memoria (RAG)
    2. Detección de Vacío
    3. Adquisición de Conocimiento (Investigación sintética)
    4. Consolidación en base vectorial
    """
    print(f"🧠 [Bucle Cognitivo ReAct] Evaluando orden: '{query_usuario}'")
    
    # Fase 1: Verificación de Memoria
    contexto_previo = buscar_contexto_semantico(query_usuario, top_k=2)
    
    # Fase 2: Detección de Vacío
    necesita_investigacion = "Sin coincidencias semánticas relevantes" in contexto_previo or len(contexto_previo) < 40
    
    conocimiento_externo = ""
    if necesita_investigacion and llm_engine:
        print("🔍 [Bucle Cognitivo] Vacío detectado en memoria. Iniciando investigación y adquisición de conocimiento...")
        # Fase 3: Adquisición de Conocimiento
        prompt_inv = (
            f"Eres S.I.N.D.D.I. Core. El usuario solicita: '{query_usuario}'. "
            "No posees este conocimiento específico registrado en tu RAG. "
            "Genera una referencia técnica precisa, pasos lógicos o estructura de código necesaria para resolver esta tarea:"
        )
        try:
            resp_inv = llm_engine.create_chat_completion(
                messages=[{"role": "user", "content": prompt_inv}],
                max_tokens=500,
                temperature=0.3
            )
            conocimiento_externo = resp_inv['choices'][0]['message']['content'].strip()
            
            # Fase 4: Consolidación Inmediata
            guardar_vector_memoria(conocimiento_externo, f"Investigación Autónoma: {query_usuario}")
            clasificar_y_organizar_memoria(f"Investigacion_{query_usuario[:15]}", conocimiento_externo)
            print("✨ [Bucle Cognitivo] Conocimiento adquirido, vectorizado y consolidado en disco.")
        except Exception as e:
            conocimiento_externo = f"Error en adquisición de conocimiento: {e}"
    else:
        print("✨ [Bucle Cognitivo] Conocimiento validado en memoria RAG local.")

    return f"--- MEMORIA RAG ---\n{contexto_previo}\n\n--- ADQUISICIÓN / INVESTIGACIÓN ---\n{conocimiento_externo if necesita_investigacion else 'Base de conocimientos consolidada.'}"


# --- NÚCLEO DE ACCIÓN FÍSICA, TERMINAL, BLENDER Y GODOT AUTÓNOMO ---
def ejecutar_comando_terminal(comando):
    try:
        if any(c in comando.lower() for c in ["rm -rf", "format", "del /f"]):
            return "⚠️ Comando bloqueado por protocolos de seguridad de S.I.N.D.D.I."
        
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=45)
        salida = resultado.stdout if resultado.returncode == 0 else resultado.stderr
        save_to_db("historial", {"evento": "Ejecución de terminal", "cmd": comando, "estado": "Éxito" if resultado.returncode == 0 else "Error"})
        return salida.strip() or "Proceso ejecutado sin salida de texto."
    except Exception as e:
        return f"Error en la ejecución del proceso: {str(e)}"

def ejecutar_script_blender_autonomo(query_usuario, llm_engine):
    blender_path = r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
    if not os.path.exists(blender_path):
        return f"⚠️ No se encontró Blender en la ruta especificada: {blender_path}"

    prompt_sistema = (
        "Eres S.I.N.D.D.I., motor de IA especializado en desarrollo 3D y Python con Blender (bpy).\n"
        "1. Limpia la escena actual.\n"
        "2. Construye geométricamente lo pedido.\n"
        "3. Exporte obligatoriamente a GLB con:\n"
        "   bpy.ops.export_scene.gltf(filepath='asset_sinddi.glb', export_format='GLB')\n"
        "DEVUELVE ÚNICAMENTE CÓDIGO PYTHON EN MARKDOWN ```python ... ```."
    )
    messages = [{"role": "system", "content": prompt_sistema}, {"role": "user", "content": query_usuario}]
    script_path = "blender_script.py"

    for intento in range(3):
        if not llm_engine:
            return "⚠️ Cerebro GGUF no inicializado."
        try:
            resp = llm_engine.create_chat_completion(messages=messages, temperature=0.3, max_tokens=2048)
            contenido = resp['choices'][0]['message']['content']
        except Exception as e:
            return f"Error en Blender: {e}"

        match = re.search(r"```python(.*?)```", contenido, re.DOTALL)
        codigo = match.group(1).strip() if match else contenido.strip()

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(codigo)

        res = subprocess.run(f'"{blender_path}" --background --python {script_path}', shell=True, capture_output=True, text=True, timeout=60)
        if res.returncode == 0:
            save_to_db("historial", {"evento": "Blender Éxito", "query": query_usuario})
            return f"🎬 [Blender Studio - Éxito]\nAsset exportado como 'asset_sinddi.glb'.\n```python\n{codigo}\n```"
        else:
            err = res.stderr.strip()
            if intento == 2:
                return f"❌ [Blender Studio] Fallo crítico:\n{err}"
            messages.append({"role": "assistant", "content": contenido})
            messages.append({"role": "user", "content": f"Error:\n{err}\nCorrige el script."})

def ejecutar_script_godot_autonomo(query_usuario, llm_engine):
    if not os.path.exists(GODOT_PATH):
        return f"⚠️ No se encontró Godot 4.4 en: {GODOT_PATH}"

    prompt_sistema = "Eres S.I.N.D.D.I. Core, experto en Godot 4.4 y GDScript. Devuelve ÚNICAMENTE código GDScript en ```gdscript ... ```."
    messages = [{"role": "system", "content": prompt_sistema}, {"role": "user", "content": query_usuario}]
    script_path = "godot_script.gd"

    for intento in range(3):
        if not llm_engine:
            return "⚠️ Cerebro GGUF no disponible."
        try:
            resp = llm_engine.create_chat_completion(messages=messages, temperature=0.3, max_tokens=2048)
            contenido = resp['choices'][0]['message']['content']
        except Exception as e:
            return f"Error Godot: {e}"

        match = re.search(r"```(?:gdscript)?(.*?)```", contenido, re.DOTALL)
        codigo = match.group(1).strip() if match else contenido.strip()

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(codigo)

        res = subprocess.run(f'"{GODOT_PATH}" --headless --script {script_path}', shell=True, capture_output=True, text=True, timeout=45)
        if res.returncode == 0:
            save_to_db("historial", {"evento": "Godot Éxito", "query": query_usuario})
            return f"🎮 [Godot 4.4 - Éxito]\nScript ejecutado en headless.\n```gdscript\n{codigo}\n```"
        else:
            err = res.stderr.strip() or res.stdout.strip()
            if intento == 2:
                return f"❌ [Godot 4.4] Fallo:\n{err}"
            messages.append({"role": "assistant", "content": contenido})
            messages.append({"role": "user", "content": f"Error:\n{err}\nCorrige el script."})


# --- TASK PLANNER ---
def desglosar_orden_masiva(query_usuario, llm_engine):
    prompt = (
        "Desglosa la orden compleja en JSON válido:\n"
        '{"proyecto": "Nombre", "subtareas": [\n'
        '  {"paso": 1, "tipo": "guion", "descripcion": "..."},\n'
        '  {"paso": 2, "tipo": "blender_modelado", "descripcion": "..."},\n'
        '  {"paso": 3, "tipo": "godot_desarrollo", "descripcion": "..."}\n'
        ']}\nDevuelve solo JSON.'
    )
    try:
        if not llm_engine:
            return None
        resp = llm_engine.create_chat_completion(messages=[{"role": "system", "content": prompt}, {"role": "user", "content": query_usuario}], temperature=0.2, max_tokens=1024)
        contenido = resp['choices'][0]['message']['content'].strip()
        match = re.search(r"```(?:json)?(.*?)```", contenido, re.DOTALL)
        return json.loads(match.group(1).strip() if match else contenido)
    except Exception as e:
        print(f"⚠️ Error Task Planner: {e}")
        return {"proyecto": "Directo", "subtareas": [{"paso": 1, "tipo": "blender_modelado", "descripcion": query_usuario}]}

def ejecutar_plan_maestro(plan, llm_engine):
    proyecto = plan.get("proyecto", "Proyecto")
    subtareas = plan.get("subtareas", [])
    resultados = []
    
    db = read_db()
    db.setdefault("escenas_activas", {})[proyecto] = {"estado": "en curso"}
    actualizar_db_completa(db)

    for tarea in subtareas:
        paso, tipo, desc = tarea.get("paso"), tarea.get("tipo"), tarea.get("descripcion")
        print(f"⚙️ [Task Planner] Paso {paso} [{tipo}]: {desc}")
        
        if tipo in ["guion", "texto"]:
            resp = llm_engine.create_chat_completion(messages=[{"role": "user", "content": f"Escribe guion técnico para: {desc}"}], max_tokens=500)
            fname = f"guion_{paso}.txt"
            with open(fname, "w", encoding="utf-8") as f:
                f.write(resp['choices'][0]['message']['content'].strip())
            resultados.append(f"Paso {paso} [Guion]: Guardado en '{fname}'.")
        elif tipo in ["blender_modelado", "3d"]:
            resultados.append(f"Paso {paso} [Blender]: {ejecutar_script_blender_autonomo(desc, llm_engine)}")
        elif tipo in ["godot_desarrollo", "juego"]:
            resultados.append(f"Paso {paso} [Godot]: {ejecutar_script_godot_autonomo(desc, llm_engine)}")

    save_to_db("historial", {"evento": "Task Planner Ejecutado", "proyecto": proyecto, "detalles": resultados})
    return f"🎯 **[Task Planner - {proyecto}]**\n" + "\n".join([f"- {r}" for r in resultados])


# --- EDICIÓN QUIRÚRGICA (CANVAS 8) ---
def evolucionar_porcion_codigo(filepath, instruccion_cambio, llm_engine):
    if not os.path.exists(filepath) or not llm_engine:
        return "⚠️ Archivo no encontrado o cerebro no disponible."

    shutil.copy(filepath, f"{filepath}.bak")
    with open(filepath, "r", encoding="utf-8") as f:
        codigo_actual = f.read()

    prompt = (
        "Eres experto en edición quirúrgica de código Python.\n"
        "Devuelve ÚNICAMENTE un JSON con dos claves:\n"
        '{"buscar": "código exacto actual", "reemplazar": "código nuevo"}'
    )
    try:
        resp = llm_engine.create_chat_completion(
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": f"CÓDIGO:\n{codigo_actual}\n\nCAMBIO:\n{instruccion_cambio}"}],
            temperature=0.1, max_tokens=1024
        )
        match = re.search(r"```(?:json)?(.*?)```", resp['choices'][0]['message']['content'], re.DOTALL)
        parche = json.loads(match.group(1).strip() if match else resp['choices'][0]['message']['content'].strip())

        viejo, nuevo = parche.get("buscar", ""), parche.get("reemplazar", "")
        if not viejo or viejo not in codigo_actual:
            return "❌ [Cirugía] No se localizó el bloque exacto en el código."

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(codigo_actual.replace(viejo, nuevo, 1))

        py_compile.compile(filepath, doraise=True)
        return f"🧬 [Cirugía Exitosa] Código actualizado en `{filepath}`."
    except Exception as e:
        shutil.copy(f"{filepath}.bak", filepath)
        return f"⚠️ Error en cirugía ({e}). Respaldo restaurado."

def auto_reparar_codigo_fuente(filepath, error_trace, query_context, llm_engine):
    return evolucionar_porcion_codigo(filepath, f"Corrige el error: {error_trace} - Contexto: {query_context}", llm_engine)


# --- HILO CENTINELA ---
def background_autonomous_sentinel():
    print("👁️ S.I.N.D.D.I. Sentinel: Activado.")
    time.sleep(15)
    while True:
        try:
            if os.path.exists("app.py"):
                py_compile.compile("app.py", doraise=True)
        except Exception as e:
            if llm_brain:
                auto_reparar_codigo_fuente("app.py", str(e), "Sentinel check", llm_brain)
        time.sleep(60)

def iniciar_hilo_centinela():
    threading.Thread(target=background_autonomous_sentinel, daemon=True).start()


# --- CLASIFICACIÓN DE CONOCIMIENTO (CANVAS 3) ---
def clasificar_y_organizar_memoria(titulo, contenido):
    db = read_db()
    db.setdefault("biblioteca_optimizada", {"3D_Assets": [], "Logica_Sistema": [], "Investigacion_Web": [], "General": []})
    
    cat = "General"
    tl, cl = titulo.lower(), contenido.lower()
    if any(k in tl or k in cl for k in ["3d", "modelo", "blender", "shader", "glb"]): cat = "3D_Assets"
    elif any(k in tl or k in cl for k in ["godot", "gdscript", "juego", "nodo"]): cat = "3D_Assets"
    elif any(k in tl or k in cl for k in ["app", "error", "codigo", "flask"]): cat = "Logica_Sistema"
    elif any(k in tl or k in cl for k in ["web", "busqueda", "investigacion"]): cat = "Investigacion_Web"

    db["biblioteca_optimizada"][cat].append({"titulo": titulo, "extracto": contenido[:400], "timestamp": "2026-11-10"})
    actualizar_db_completa(db)


# --- PROCESAMIENTO AUTÓNOMO PRINCIPAL (CON BUCLE COGNITIVO) ---
def procesar_respuesta_autonoma(query, memoria):
    query_lower = query.lower()

    if any(k in query_lower for k in ["modifica tu codigo", "cambia tu codigo", "evoluciona", "actualiza app.py", "auto-repara"]):
        return evolucionar_porcion_codigo("app.py", query, llm_brain), "", "canvas-8"

    if any(k in query_lower for k in ["pelicula", "escena animada", "proyecto completo", "crea un mundo", "videojuego completo"]):
        return ejecutar_plan_maestro(desglosar_orden_masiva(query, llm_brain), llm_brain), "", "canvas-4"

    if any(k in query_lower for k in ["blender", "esculpe", "modela", "genera modelo", "crea un 3d", "objeto 3d"]):
        return ejecutar_script_blender_autonomo(query, llm_brain), "", "canvas-4"

    if any(k in query_lower for k in ["godot", "gdscript", "juego", "escena godot", "nodo"]):
        return ejecutar_script_godot_autonomo(query, llm_brain), "", "canvas-4"

    # APLICACIÓN DEL BUCLE COGNITIVO ReAct
    contexto_cognitivo = bucle_cognitivo_sinddi(query, llm_brain)

    if llm_brain:
        messages = [
            {"role": "system", "content": f"Eres S.I.N.D.D.I., asistente autónomo local experto en programación y motores 3D.\n\n{contexto_cognitivo}"},
            {"role": "user", "content": query}
        ]
        try:
            output = llm_brain.create_chat_completion(messages=messages, max_tokens=800, temperature=0.7)
            respuesta = output['choices'][0]['message']['content'].strip()
            guardar_vector_memoria(query, "Interacción Usuario")
            clasificar_y_organizar_memoria(f"Interaccion_{query[:15]}", query)
            return respuesta, "", ""
        except Exception as e:
            print(f"Error en inferencia LLM: {e}")

    return f"🧠 [S.I.N.D.D.I.]: Consulta asimilada localmente.", "", ""


# --- ENDPOINTS HTTP ---
@app.route('/api/chat', methods=['POST'])
def handle_chat():
    data = request.get_json(silent=True) or {}
    msg = (data.get('query') or data.get('message') or '').strip()
    if not msg:
        return jsonify({"error": "Mensaje vacío"}), 400

    memoria = read_db()
    resp, code_3d, canvas = procesar_respuesta_autonoma(msg, memoria)
    save_to_db("historial", {"user": msg, "bot": resp})
    return jsonify({"response": resp, "code_3d": code_3d, "target_canvas": canvas}), 200

@app.route('/api/upload', methods=['POST'])
def handle_pdf():
    if 'pdf' not in request.files:
        return jsonify({"error": "No hay archivo PDF"}), 400
    file = request.files['pdf']
    try:
        reader = pypdf.PdfReader(file)
        text = "".join([p.extract_text() for p in reader.pages])
        guardar_vector_memoria(text, f"PDF: {file.filename}")
        clasificar_y_organizar_memoria(file.filename, text)
        return jsonify({"message": f"Documento '{file.filename}' asimilado y vectorizado."}), 200
    except Exception as e:
        return jsonify({"error": f"Error: {e}"}), 500

@app.route('/api/memories', methods=['GET'])
def get_memories():
    memoria = read_db()
    lib = memoria.get("biblioteca_optimizada", {})
    formatted = []
    if isinstance(lib, dict):
        for cat, items in lib.items():
            if isinstance(items, list):
                for item in items:
                    formatted.append({"concept": item.get("titulo", "Concepto"), "topic": cat, "details": item.get("extracto", "")})
    return jsonify(formatted), 200

@app.route('/api/canvas8/fix-error', methods=['POST'])
def handle_canvas8_fix():
    data = request.get_json(silent=True) or {}
    fp = data.get('filepath', 'app.py')
    trace = data.get('error_trace', '')
    query = data.get('query', 'Corrección desde Canvas 8')
    if not trace:
        return jsonify({"error": "Falta el rastro del error"}), 400
    res = auto_reparar_codigo_fuente(fp, trace, query, llm_brain)
    return jsonify({"response": res, "target_canvas": "canvas-8"}), 200


if __name__ == '__main__':
    init_db()
    iniciar_hilo_centinela()
    app.run(port=3000, debug=True)
