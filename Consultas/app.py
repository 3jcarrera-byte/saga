import os
import json
import re
import subprocess
import py_compile
import time
import threading
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
        "Eres S.I.N.D.D.I., un motor de inteligencia artificial especializado en desarrollo 3D y programación Python con Blender (bpy).\n"
        "Debes escribir un script de Python ejecutable usando 'bpy' que:\n"
        "1. Limpie la escena actual.\n"
        "2. Construya geométricamente lo que pide el usuario.\n"
        "3. Exporte obligatoriamente el resultado a un archivo GLB usando exactamente:\n"
        "   bpy.ops.export_scene.gltf(filepath='asset_sinddi.glb', export_format='GLB')\n"
        "DEVUELVE ÚNICAMENTE EL CÓDIGO PYTHON ENCERRADO EN UN BLOQUE MARKDOWN ```python ... ```."
    )

    messages = [
        {"role": "system", "content": prompt_sistema},
        {"role": "user", "content": query_usuario}
    ]

    script_path = "blender_script.py"
    max_intentos = 3

    for intento in range(max_intentos):
        if not llm_engine:
            return "⚠️ Cerebro GGUF no inicializado."
        try:
            resp = llm_engine.create_chat_completion(messages=messages, temperature=0.3, max_tokens=2048)
            contenido = resp['choices'][0]['message']['content']
        except Exception as e:
            return f"Error en inferencia para Blender: {e}"

        match = re.search(r"```python(.*?)```", contenido, re.DOTALL)
        codigo_generado = match.group(1).strip() if match else contenido.strip()

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(codigo_generado)

        comando = f'"{blender_path}" --background --python {script_path}'
        resultado_proceso = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=60)

        if resultado_proceso.returncode == 0:
            save_to_db("historial", {"evento": "Blender Autónomo Éxito", "query": query_usuario})
            return f"🎬 [Blender Studio - Éxito]\nAsset exportado como 'asset_sinddi.glb'.\n```python\n{codigo_generado}\n```"
        else:
            error_traceback = resultado_proceso.stderr.strip()
            if intento == max_intentos - 1:
                return f"❌ [Blender Studio] Fallo crítico:\n{error_traceback}"
            messages.append({"role": "assistant", "content": contenido})
            messages.append({"role": "user", "content": f"Error en Blender:\n{error_traceback}\nCorrige el script bpy."})

def ejecutar_script_godot_autonomo(query_usuario, llm_engine):
    if not os.path.exists(GODOT_PATH):
        return f"⚠️ No se encontró Godot 4.4 en la ruta especificada: {GODOT_PATH}"

    prompt_sistema = (
        "Eres S.I.N.D.D.I. Core, experto en Godot 4.4 y GDScript.\n"
        "Escribe un script GDScript ejecutable en modo headless que configure nodos y valide la lógica del juego.\n"
        "DEVUELVE ÚNICAMENTE EL CÓDIGO GDSCRIPT EN UN BLOQUE MARKDOWN ```gdscript ... ```."
    )

    messages = [
        {"role": "system", "content": prompt_sistema},
        {"role": "user", "content": query_usuario}
    ]

    script_path = "godot_script.gd"
    max_intentos = 3

    for intento in range(max_intentos):
        if not llm_engine:
            return "⚠️ Cerebro GGUF no disponible para Godot."
        try:
            resp = llm_engine.create_chat_completion(messages=messages, temperature=0.3, max_tokens=2048)
            contenido = resp['choices'][0]['message']['content']
        except Exception as e:
            return f"Error en inferencia para Godot: {e}"

        match = re.search(r"```(?:gdscript)?(.*?)```", contenido, re.DOTALL)
        codigo_generado = match.group(1).strip() if match else contenido.strip()

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(codigo_generado)

        comando = f'"{GODOT_PATH}" --headless --script {script_path}'
        resultado_proceso = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=45)

        if resultado_proceso.returncode == 0:
            save_to_db("historial", {"evento": "Godot 4.4 Autónomo Éxito", "query": query_usuario})
            return f"🎮 [Godot 4.4 - Éxito Autónomo]\nScript GDScript ejecutado en modo headless.\n```gdscript\n{codigo_generado}\n```"
        else:
            error_traceback = resultado_proceso.stderr.strip() or resultado_proceso.stdout.strip()
            if intento == max_intentos - 1:
                return f"❌ [Godot 4.4] Fallo tras {max_intentos} intentos:\n{error_traceback}"
            messages.append({"role": "assistant", "content": contenido})
            messages.append({"role": "user", "content": f"Error en Godot 4.4:\n{error_traceback}\nCorrige el script GDScript."})


# --- MÓDULO TASK PLANNER (ORQUESTADOR DE PROYECTOS COMPLETOS) ---
def desglosar_orden_masiva(query_usuario, llm_engine):
    prompt_sistema = (
        "Eres el Task Planner principal de S.I.N.D.D.I.\n"
        "Desglosa la orden compleja del usuario en un plan de subtareas secuenciales en JSON válido:\n"
        "{\n"
        '  "proyecto": "Nombre del proyecto",\n'
        '  "subtareas": [\n'
        '    {"paso": 1, "tipo": "guion", "descripcion": "Redacción o concepto"},\n'
        '    {"paso": 2, "tipo": "blender_modelado", "descripcion": "Modelado 3D de assets"},\n'
        '    {"paso": 3, "tipo": "godot_desarrollo", "descripcion": "Integración y lógica en Godot 4.4"}\n'
        "  ]\n"
        "}\n"
        "Devuelve únicamente el JSON."
    )
    try:
        if not llm_engine:
            return None
        resp = llm_engine.create_chat_completion(
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": query_usuario}],
            temperature=0.2,
            max_tokens=1024
        )
        contenido = resp['choices'][0]['message']['content'].strip()
        match = re.search(r"```(?:json)?(.*?)```", contenido, re.DOTALL)
        json_str = match.group(1).strip() if match else contenido
        return json.loads(json_str)
    except Exception as e:
        print(f"⚠️ Error en Task Planner: {e}")
        return {
            "proyecto": "Proyecto Directo",
            "subtareas": [{"paso": 1, "tipo": "blender_modelado", "descripcion": query_usuario}]
        }

def ejecutar_plan_maestro(plan_maestro, llm_engine):
    proyecto_nombre = plan_maestro.get("proyecto", "Proyecto_Sin_Nombre")
    subtareas = plan_maestro.get("subtareas", [])
    resultados_ejecucion = []
    
    db = read_db()
    if "escenas_activas" not in db:
        db["escenas_activas"] = {}
    db["escenas_activas"][proyecto_nombre] = {"estado": "en curso", "timestamp": "2026-11-10"}
    actualizar_db_completa(db)

    for tarea in subtareas:
        paso = tarea.get("paso")
        tipo = tarea.get("tipo")
        desc = tarea.get("descripcion")
        
        print(f"⚙️ [Task Planner] Paso {paso} [{tipo}]: {desc}")
        
        if tipo == "guion" or tipo == "texto":
            try:
                resp = llm_engine.create_chat_completion(messages=[{"role": "user", "content": f"Escribe el guion técnico para: {desc}"}], max_tokens=500)
                texto = resp['choices'][0]['message']['content'].strip()
                fname = f"guion_{paso}.txt"
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(texto)
                resultados_ejecucion.append(f"Paso {paso} [Guion]: Guardado en '{fname}'.")
            except Exception as e:
                resultados_ejecucion.append(f"Paso {paso} [Guion]: Error -> {e}")

        elif tipo == "blender_modelado" or tipo == "3d":
            res_b = ejecutar_script_blender_autonomo(desc, llm_engine)
            resultados_ejecucion.append(f"Paso {paso} [Blender]: {res_b}")

        elif tipo == "godot_desarrollo" or tipo == "juego":
            res_g = ejecutar_script_godot_autonomo(desc, llm_engine)
            resultados_ejecucion.append(f"Paso {paso} [Godot 4.4]: {res_g}")

    save_to_db("historial", {"evento": "Task Planner Ejecutado", "proyecto": proyecto_nombre, "detalles": resultados_ejecucion})
    return f"🎯 **[S.I.N.D.D.I. Task Planner - {proyecto_nombre}]**\n" + "\n".join([f"- {r}" for r in resultados_ejecucion])


# --- MÓDULO DE APRENDIZAJE PERSISTENTE Y RAG (CANVAS 1) ---
def forzar_aprendizaje_y_persistencia(query_usuario, llm_engine):
    prompt_sistema = "Eres S.I.N.D.D.I. Core. Sintetiza una guía técnica estructurada en formato Markdown."
    try:
        resp = llm_engine.create_chat_completion(
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": f"Genera guía sobre: {query_usuario}"}],
            max_tokens=1000,
            temperature=0.3
        )
        contenido_guia = resp['choices'][0]['message']['content'].strip()
        nombre_base = re.sub(r'[^a-zA-Z0-9_-]', '_', query_usuario[:25])
        filename = f"estudio_{nombre_base}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# S.I.N.D.D.I. - Aprendizaje Persistente\n\n{contenido_guia}")
            
        guardar_vector_memoria(contenido_guia, f"Estudio Autónomo: {query_usuario}")
        clasificar_y_organizar_memoria(f"Estudio Autónomo: {query_usuario}", contenido_guia)
        
        return f"🧠 [Aprendizaje Persistente Éxito]\nDocumento escrito en `{filename}` y vectorizado en RAG matricial."
    except Exception as e:
        return f"⚠️ Error en auto-aprendizaje: {e}"


# --- MÓDULO DE AUTO-EVOLUCIÓN Y REPARACIÓN DE CÓDIGO (CANVAS 8) ---
def auto_reparar_codigo_fuente(filepath, error_trace, query_context, llm_engine):
    if not os.path.exists(filepath):
        return f"⚠️ Archivo no encontrado: {filepath}"

    with open(filepath, "r", encoding="utf-8") as f:
        codigo_actual = f.read()

    prompt_sistema = (
        "Eres S.I.N.D.D.I. Core, experto en auto-refactorización de código.\n"
        "Corrige el error del archivo y devuelve ÚNICAMENTE el código corregido dentro de un bloque markdown ```python ... ```."
    )
    prompt_usuario = f"--- ARCHIVO: {filepath} ---\n```python\n{codigo_actual}\n```\n\n--- ERROR ---\n{error_trace}\nContexto: {query_context}"

    messages = [{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}]
    max_intentos = 3

    for intento in range(max_intentos):
        if not llm_engine:
            return "⚠️ Cerebro GGUF no disponible."
        try:
            resp = llm_engine.create_chat_completion(messages=messages, temperature=0.2, max_tokens=2048)
            contenido = resp['choices'][0]['message']['content']
        except Exception as e:
            return f"Error en inferencia de auto-evolución: {e}"

        match = re.search(r"```(?:python|javascript|js)?(.*?)```", contenido, re.DOTALL)
        codigo_corregido = match.group(1).strip() if match else contenido.strip()

        test_file = f"temp_patch_{filepath}"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(codigo_corregido)

        sintaxis_valida = True
        err_sintaxis = ""
        if filepath.endswith(".py"):
            try:
                py_compile.compile(test_file, doraise=True)
            except Exception as syntax_err:
                sintaxis_valida = False
                err_sintaxis = str(syntax_err)

        if sintaxis_valida:
            os.replace(test_file, filepath)
            save_to_db("parches_pendientes", {"archivo": filepath, "estado": "Aplicado y Verificado"})
            return f"🧬 [Auto-Evolución - Éxito]\nEl archivo `{filepath}` fue auto-reparado tras {intento + 1} intento(s)."
        else:
            if os.path.exists(test_file):
                os.remove(test_file)
            if intento == max_intentos - 1:
                return f"❌ Fallo al auto-reparar `{filepath}`. Error: {err_sintaxis}"
            messages.append({"role": "assistant", "content": contenido})
            messages.append({"role": "user", "content": f"Error de sintaxis:\n{err_sintaxis}\nCorrige nuevamente."})


# --- HILO CENTINELA EN SEGUNDO PLANO ---
def background_autonomous_sentinel():
    print("👁️ S.I.N.D.D.I. Sentinel: Hilo de vigilancia autónoma activado.")
    time.sleep(15)
    while True:
        try:
            if os.path.exists("app.py"):
                try:
                    py_compile.compile("app.py", doraise=True)
                except Exception as compile_err:
                    if llm_brain:
                        auto_reparar_codigo_fuente("app.py", str(compile_err), "Sentinel background check", llm_brain)
        except Exception as e:
            print(f"⚠️ Error en Sentinel: {e}")
        time.sleep(60)

def iniciar_hilo_centinela():
    threading.Thread(target=background_autonomous_sentinel, daemon=True).start()


# --- CLASIFICACIÓN DE CONOCIMIENTO (CANVAS 3) ---
def clasificar_y_organizar_memoria(titulo, contenido):
    db = read_db()
    if "biblioteca_optimizada" not in db or not isinstance(db["biblioteca_optimizada"], dict):
        db["biblioteca_optimizada"] = {"3D_Assets": [], "Logica_Sistema": [], "Investigacion_Web": [], "General": []}
    
    categoria = "General"
    tl, cl = titulo.lower(), contenido.lower()
    if any(k in tl or k in cl for k in ["3d", "modelo", "blender", "shader", "glb"]):
        categoria = "3D_Assets"
    elif any(k in tl or k in cl for k in ["godot", "gdscript", "juego", "nodo"]):
        categoria = "3D_Assets"
    elif any(k in tl or k in cl for k in ["app", "error", "codigo", "flask", "script"]):
        categoria = "Logica_Sistema"
    elif any(k in tl or k in cl for k in ["web", "busqueda", "internet"]):
        categoria = "Investigacion_Web"

    db["biblioteca_optimizada"][categoria].append({"titulo": titulo, "extracto": contenido[:400], "timestamp": "2026-11-10"})
    actualizar_db_completa(db)


# --- PROCESAMIENTO AUTÓNOMO PRINCIPAL ---
def procesar_respuesta_autonoma(query, memoria):
    query_lower = query.lower()

    if query_lower.startswith("aprende ") or "aprende todo lo necesario" in query_lower:
        return forzar_aprendizaje_y_persistencia(query, llm_brain), "", "canvas-1"

    if any(k in query_lower for k in ["pelicula", "escena animada", "proyecto completo", "crea un mundo", "videojuego completo"]):
        plan = desglosar_orden_masiva(query, llm_brain)
        return ejecutar_plan_maestro(plan, llm_brain), "", "canvas-4"

    if any(k in query_lower for k in ["blender", "esculpe", "modela", "genera modelo", "crea un 3d", "objeto 3d"]):
        return ejecutar_script_blender_autonomo(query, llm_brain), "", "canvas-4"

    if any(k in query_lower for k in ["godot", "gdscript", "juego", "escena godot", "nodo"]):
        return ejecutar_script_godot_autonomo(query, llm_brain), "", "canvas-4"

    contexto_memoria = buscar_contexto_semantico(query, top_k=2)

    if llm_brain:
        messages = [
            {
                "role": "system", 
                "content": (
                    "Eres S.I.N.D.D.I., asistente autónomo local experto en programación, desarrollo 3D (Blender) y motores de juego (Godot 4.4).\n\n"
                    f"Contexto semántico de la memoria vectorial:\n{contexto_memoria}"
                )
            },
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


# --- ENDPOINTS HTTP PARA ENLAZAR EL FRONTEND (CHAT.JS) ---
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


@app.route('/api/upload', methods=['POST'])
def handle_pdf():
    if 'pdf' not in request.files:
        return jsonify({"error": "No hay archivo PDF"}), 400
    file = request.files['pdf']
    try:
        reader = pypdf.PdfReader(file)
        extracted_text = "".join([page.extract_text() for page in reader.pages])
        guardar_vector_memoria(extracted_text, f"PDF: {file.filename}")
        clasificar_y_organizar_memoria(file.filename, extracted_text)
        return jsonify({"message": f"Documento '{file.filename}' asimilado, vectorizado y categorizado en la biblioteca del Canvas 3."}), 200
    except Exception as e:
        return jsonify({"error": f"Error al procesar PDF: {e}"}), 500


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


@app.route('/api/canvas8/fix-error', methods=['POST'])
def handle_canvas8_fix():
    req_data = request.get_json(silent=True) or {}
    filepath = req_data.get('filepath', 'app.py')
    error_trace = req_data.get('error_trace', '')
    user_query = req_data.get('query', 'Corrige este error detectado en el sistema.')

    if not error_trace:
        return jsonify({"error": "No se proporcionó el rastro del error (traceback)"}), 400

    resultado_evolucion = auto_reparar_codigo_fuente(filepath, error_trace, user_query, llm_brain)

    return jsonify({
        "response": resultado_evolucion,
        "target_canvas": "canvas-8"
    }), 200


if __name__ == '__main__':
    init_db()
    iniciar_hilo_centinela()
    app.run(port=3000, debug=True)
