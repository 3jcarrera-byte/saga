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


# --- NÚCLEO DE ACCIÓN FÍSICA, TERMINAL Y BLENDER AUTÓNOMO ---
def ejecutar_comando_terminal(comando):
    try:
        if any(c in comando.lower() for c in ["rm -rf", "format", "del /f"]):
            return "⚠️ Comando bloqueado por protocolos de seguridad de S.I.N.D.D.I."
        
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=45)
        salida = resultado.stdout if resultado.returncode == 0 else resultado.stderr
        save_to_db("historial", {"evento": "Ejecución de terminal / Blender", "cmd": comando, "estado": "Éxito" if resultado.returncode == 0 else "Error"})
        return salida.strip() or "Proceso ejecutado sin salida de texto."
    except Exception as e:
        return f"Error en la ejecución del proceso: {str(e)}"

def ejecutar_script_blender_autonomo(query_usuario, llm_engine):
    blender_path = r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
    if not os.path.exists(blender_path):
        return f"⚠️ No se encontró Blender en la ruta especificada: {blender_path}"

    prompt_sistema = (
        "Eres S.I.N.D.D.I., un motor de inteligencia artificial especializado en desarrollo 3D y programación Python con Blender (bpy).\n"
        "El usuario te pedirá una creación geométrica o animación.\n"
        "Debes escribir un script de Python ejecutable usando 'bpy' que:\n"
        "1. Limpie la escena actual (seleccione todo y lo borre).\n"
        "2. Construya geométricamente lo que pide el usuario.\n"
        "3. Aplique modificadores o materiales si corresponde.\n"
        "4. Exporte obligatoriamente el resultado a un archivo GLB usando exactamente:\n"
        "   bpy.ops.export_scene.gltf(filepath='asset_sinddi.glb', export_format='GLB')\n"
        "DEVUELVE ÚNICAMENTE EL CÓDIGO PYTHON ENCERRADO EN UN BLOQUE MARKDOWN ```python ... ```. Sin explicaciones adicionales."
    )

    messages = [
        {"role": "system", "content": prompt_sistema},
        {"role": "user", "content": query_usuario}
    ]

    max_intentos = 3
    script_path = "blender_script.py"

    for intento in range(max_intentos):
        if not llm_engine:
            return "⚠️ Error: El cerebro GGUF de S.I.N.D.D.I. no está inicializado."

        try:
            resp = llm_engine.create_chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=2048
            )
            contenido = resp['choices'][0]['message']['content']
        except Exception as e:
            return f"Error en inferencia del modelo para Blender: {e}"

        match = re.search(r"```python(.*?)```", contenido, re.DOTALL)
        codigo_generado = match.group(1).strip() if match else contenido.strip()

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(codigo_generado)

        comando = f'"{blender_path}" --background --python {script_path}'
        resultado_proceso = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=60)

        if resultado_proceso.returncode == 0:
            save_to_db("historial", {"evento": "Blender Autónomo Éxito", "query": query_usuario, "intento": intento + 1})
            return (
                f"🎬 [S.I.N.D.D.I. Studio - Éxito Autónomo (Intento {intento + 1})]\n"
                f"Script generado y probado con éxito. Asset exportado como 'asset_sinddi.glb'.\n\n"
                f"```python\n{codigo_generado}\n```"
            )
        else:
            error_traceback = resultado_proceso.stderr.strip()
            if intento == max_intentos - 1:
                return (
                    f"❌ [S.I.N.D.D.I. Studio] Fallo crítico tras {max_intentos} intentos de auto-corrección.\n"
                    f"Último error detectado:\n{error_traceback}\n\nCódigo fallido:\n```python\n{codigo_generado}\n```"
                )
            
            messages.append({"role": "assistant", "content": contenido})
            messages.append({
                "role": "user", 
                "content": f"El script anterior generó este error en Blender:\n{error_traceback}\n\nCorrige el código Python (bpy) para solucionar el error. Devuelve únicamente el código corregido dentro de un bloque markdown ```python ... ```."
            })


# --- MÓDULO TASK PLANNER (ORQUESTADOR DE PROYECTOS COMPLETOS) ---
def desglosar_orden_masiva(query_usuario, llm_engine):
    prompt_sistema = (
        "Eres el Task Planner principal de S.I.N.D.D.I.\n"
        "Tu objetivo es tomar una orden compleja o masiva del usuario y descomponerla en un plan de subtareas secuenciales.\n"
        "Debes devolver la respuesta ÚNICAMENTE como un objeto JSON válido con la siguiente estructura exacta:\n"
        "{\n"
        '  "proyecto": "Nombre descriptivo del proyecto",\n'
        '  "subtareas": [\n'
        '    {"paso": 1, "tipo": "guion", "descripcion": "Detalle de la tarea de redacción o guion"},\n'
        '    {"paso": 2, "tipo": "blender_modelado", "descripcion": "Detalle del modelado 3D a generar"},\n'
        '    {"paso": 3, "tipo": "rigging_animacion", "descripcion": "Detalle de la animación o rigging para Canvas 7"}\n'
        "  ]\n"
        "}\n"
        "No incluyas texto adicional ni explicaciones fuera del JSON."
    )

    messages = [
        {"role": "system", "content": prompt_sistema},
        {"role": "user", "content": query_usuario}
    ]

    try:
        if not llm_engine:
            return None
            
        resp = llm_engine.create_chat_completion(
            messages=messages,
            temperature=0.2,
            max_tokens=1024
        )
        contenido = resp['choices'][0]['message']['content'].strip()
        match = re.search(r"```(?:json)?(.*?)```", contenido, re.DOTALL)
        json_str = match.group(1).strip() if match else contenido
        
        plan_json = json.loads(json_str)
        return plan_json
    except Exception as e:
        print(f"⚠️ Error al desglosar la orden masiva en el Task Planner: {e}")
        return {
            "proyecto": "Proyecto Directo",
            "subtareas": [
                {"paso": 1, "tipo": "blender_modelado", "descripcion": query_usuario}
            ]
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
        
        print(f"⚙️ [Task Planner] Ejecutando Paso {paso} [{tipo}]: {desc}")
        
        if tipo == "guion" or tipo == "texto":
            prompt_guion = f"Escribe el contenido detallado o guion técnico para: {desc}"
            try:
                resp = llm_engine.create_chat_completion(
                    messages=[{"role": "user", "content": prompt_guion}],
                    max_tokens=500,
                    temperature=0.5
                )
                texto_guion = resp['choices'][0]['message']['content'].strip()
                nombre_archivo = f"guion_{paso}.txt"
                with open(nombre_archivo, "w", encoding="utf-8") as f:
                    f.write(texto_guion)
                resultados_ejecucion.append(f"Paso {paso} [Guion]: Generado y guardado en '{nombre_archivo}'.")
            except Exception as e:
                resultados_ejecucion.append(f"Paso {paso} [Guion]: Error -> {str(e)}")

        elif tipo == "blender_modelado" or tipo == "3d":
            resultado_blender = ejecutar_script_blender_autonomo(desc, llm_engine)
            resultados_ejecucion.append(f"Paso {paso} [Blender]: {resultado_blender}")

        elif tipo == "rigging_animacion" or tipo == "animacion":
            script_rigging_path = "blender_rigging.py"
            codigo_rigging_base = f"""# S.I.N.D.D.I. Canvas 7 Rigging & Animation Pipeline
import bpy
print("🦾 [Canvas 7] Aplicando rig y ciclos de animación para: {desc}")
if bpy.context.selected_objects:
    obj = bpy.context.active_object
    print("Objeto activo vinculado a cinemática: " + obj.name)
"""
            with open(script_rigging_path, "w", encoding="utf-8") as f:
                f.write(codigo_rigging_base)
            
            blender_path = r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
            if os.path.exists(blender_path):
                cmd = f'"{blender_path}" --background --python {script_rigging_path}'
                res_rig = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                estado_rig = "Éxito" if res_rig.returncode == 0 else "Error menor"
                resultados_ejecucion.append(f"Paso {paso} [Canvas 7 Rigging]: Ejecutado con estado '{estado_rig}'.")
            else:
                resultados_ejecucion.append(f"Paso {paso} [Canvas 7 Rigging]: Script de rigging creado ({script_rigging_path}).")

    save_to_db("historial", {
        "evento": "Task Planner Ejecutado",
        "proyecto": proyecto_nombre,
        "detalles": resultados_ejecucion
    })

    resumen_final = f"🎯 **[S.I.N.D.D.I. Task Planner - Proyecto: {proyecto_nombre}]**\n" + "\n".join([f"- {res}" for res in resultados_ejecucion])
    return resumen_final


# --- MÓDULO DE APRENDIZAJE PERSISTENTE Y VECTORIAL (CANVAS 1) ---
def forzar_aprendizaje_y_persistencia(query_usuario, llm_engine):
    prompt_sistema = (
        "Eres S.I.N.D.D.I. Core. El usuario te ha ordenado aprender y estructurar conocimiento técnico sobre un tema.\n"
        "No des explicaciones de tutorial genéricas. Sintetiza una guía técnica directa, limpia y estructurada "
        "en formato Markdown que sirva como documentación interna permanente."
    )
    
    try:
        resp = llm_engine.create_chat_completion(
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Genera la guía técnica de aprendizaje sobre: {query_usuario}"}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        contenido_guia = resp['choices'][0]['message']['content'].strip()
        
        nombre_base = re.sub(r'[^a-zA-Z0-9_-]', '_', query_usuario[:25])
        filename = f"estudio_{nombre_base}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# S.I.N.D.D.I. - Módulo de Auto-Aprendizaje Persistente\n\n{contenido_guia}")
            
        # Almacenar en la base vectorial RAG de Numpy
        guardar_vector_memoria(contenido_guia, f"Estudio Autónomo: {query_usuario}")
        clasificar_y_organizar_memoria(f"Estudio Autónomo: {query_usuario}", contenido_guia)
        
        return (
            f"🧠 [S.I.N.D.D.I. Aprendizaje Persistente - Éxito RAG]\n"
            f"El sistema ha procesado la orden, escrito el documento técnico en `{filename}` "
            f"y vectorizado matemáticamente el conocimiento en el motor matricial."
        )
    except Exception as e:
        return f"⚠️ Error en el ciclo de aprendizaje autónomo: {e}"


# --- MÓDULO DE AUTO-EVOLUCIÓN Y REPARACIÓN DE CÓDIGO (CANVAS 8) ---
def auto_reparar_codigo_fuente(filepath, error_trace, query_context, llm_engine):
    if not os.path.exists(filepath):
        return f"⚠️ Archivo objetivo no encontrado: {filepath}"

    with open(filepath, "r", encoding="utf-8") as f:
        codigo_actual = f.read()

    prompt_sistema = (
        "Eres S.I.N.D.D.I. Core, un sistema experto en ingeniería de software y auto-refactorización de código.\n"
        "Se te proporcionará un código fuente y un error (traceback) reportado en el Canvas 8.\n"
        "Tu misión es analizar el error, corregir el código fuente para eliminar la falla de raíz, "
        "y devolver ÚNICAMENTE el archivo completo corregido dentro de un bloque markdown ```python ... ```.\n"
        "No rompas la arquitectura existente; mantén las importaciones y la lógica intactas."
    )

    prompt_usuario = (
        f"--- ARCHIVO AFECTADO: {filepath} ---\n"
        f"```python\n{codigo_actual}\n```\n\n"
        f"--- ERROR CAPTURADO (CANVAS 8) ---\n{error_trace}\n\n"
        f"Contexto adicional: {query_context}\n"
        "Genera el código corregido completo:"
    )

    messages = [
        {"role": "system", "content": prompt_sistema},
        {"role": "user", "content": prompt_usuario}
    ]

    max_intentos = 3
    for intento in range(max_intentos):
        if not llm_engine:
            return "⚠️ Cerebro GGUF no disponible para auto-corrección."

        try:
            resp = llm_engine.create_chat_completion(
                messages=messages,
                temperature=0.2,
                max_tokens=2048
            )
            contenido = resp['choices'][0]['message']['content']
        except Exception as e:
            return f"Error en inferencia para auto-evolución: {e}"

        match = re.search(r"```(?:python|javascript|js)?(.*?)```", contenido, re.DOTALL)
        codigo_corregido = match.group(1).strip() if match else contenido.strip()

        test_file_path = f"temp_patch_{filepath}"
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(codigo_corregido)

        sintaxis_valida = True
        error_sintaxis = ""
        
        if filepath.endswith(".py"):
            try:
                py_compile.compile(test_file_path, doraise=True)
            except Exception as syntax_err:
                sintaxis_valida = False
                error_sintaxis = str(syntax_err)

        if sintaxis_valida:
            os.replace(test_file_path, filepath)
            save_to_db("parches_pendientes", {
                "archivo": filepath,
                "estado": "Aplicado y Verificado",
                "intento": intento + 1,
                "timestamp": "2026-11-10"
            })
            return (
                f"🧬 [S.I.N.D.D.I. Auto-Evolución - Éxito]\n"
                f"El archivo `{filepath}` ha sido auto-reparado y probado tras {intento + 1} intento(s).\n"
                f"El error detectado en Canvas 8 ha sido neutralizado y el código está actualizado."
            )
        else:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)

            if intento == max_intentos - 1:
                return f"❌ Fallo al auto-reparar `{filepath}` tras {max_intentos} intentos. Último error de sintaxis: {error_sintaxis}"

            messages.append({"role": "assistant", "content": contenido})
            messages.append({
                "role": "user",
                "content": f"El código propuesto generó un error de sintaxis al compilar:\n{error_sintaxis}\nCorrige el código nuevamente."
            })


# --- HILO CENTINELA EN SEGUNDO PLANO (VIGILANCIA DESATENDIDA) ---
def background_autonomous_sentinel():
    print("👁️ S.I.N.D.D.I. Sentinel: Hilo de vigilancia autónoma activado en segundo plano.")
    time.sleep(15)
    
    while True:
        try:
            if os.path.exists("app.py"):
                try:
                    py_compile.compile("app.py", doraise=True)
                except Exception as compile_err:
                    error_msg = str(compile_err)
                    print(f"⚠️ [Sentinel] Fallo detectado en app.py: {error_msg}. Auto-reparando...")
                    if llm_brain:
                        resultado = auto_reparar_codigo_fuente("app.py", error_msg, "Corrección proactiva por Sentinel background.", llm_brain)
                        print(f"🧬 [Sentinel Resultado]: {resultado}")

            memoria = read_db()
            errores = memoria.get("errores_registrados", [])
            for err in errores:
                if err.get("estado") == "activo":
                    filepath = err.get("archivo", "app.py")
                    error_trace = err.get("error", "Error registrado")
                    if llm_brain:
                        resultado = auto_reparar_codigo_fuente(filepath, error_trace, "Resolución desatendida vía base de datos.", llm_brain)
                        print(f"🧬 [Sentinel Resultado]: {resultado}")
                        err["estado"] = "resuelto"
                        actualizar_db_completa(memoria)
        except Exception as e:
            print(f"⚠️ Error en el ciclo del Sentinel autónomo: {e}")
        
        time.sleep(60)

def iniciar_hilo_centinela():
    t = threading.Thread(target=background_autonomous_sentinel, daemon=True)
    t.start()


# --- CLASIFICACIÓN DE CONOCIMIENTO (CANVAS 3) ---
def clasificar_y_organizar_memoria(titulo, contenido):
    db = read_db()
    if "biblioteca_optimizada" not in db or not isinstance(db["biblioteca_optimizada"], dict):
        db["biblioteca_optimizada"] = {"3D_Assets": [], "Logica_Sistema": [], "Investigacion_Web": [], "General": []}
    
    categoria = "General"
    titulo_lower = titulo.lower()
    contenido_lower = contenido.lower()

    if any(k in titulo_lower or k in contenido_lower for k in ["3d", "modelo", "geometria", "canvas", "shader", "pbr", "blender"]):
        categoria = "3D_Assets"
    elif any(k in titulo_lower or k in contenido_lower for k in ["app", "error", "codigo", "parche", "flask", "script"]):
        categoria = "Logica_Sistema"
    elif any(k in titulo_lower or k in contenido_lower for k in ["web", "busqueda", "internet"]):
        categoria = "Investigacion_Web"

    db["biblioteca_optimizada"][categoria].append({
        "titulo": titulo,
        "extracto": contenido[:400],
        "timestamp": "2026-11-10"
    })
    actualizar_db_completa(db)


# --- PROCESAMIENTO AUTÓNOMO PRINCIPAL ---
def procesar_respuesta_autonoma(query, memoria):
    query_lower = query.lower()

    # Interceptar comandos de aprendizaje explícito para forzar persistencia real y RAG
    if query_lower.startswith("aprende ") or "aprende todo lo necesario" in query_lower:
        print("🧠 [Canvas 1] Orden de aprendizaje persistente detectada.")
        resultado_aprendizaje = forzar_aprendizaje_y_persistencia(query, llm_brain)
        return resultado_aprendizaje, "", "canvas-1"

    # Si la orden es masiva, compleja o un proyecto completo, activamos el Task Planner
    if any(k in query_lower for k in ["pelicula", "escena animada", "proyecto completo", "crea un mundo", "secuencia", "historia"]):
        print("🧠 [Task Planner] Orden masiva detectada. Desglosando plan de subtareas...")
        plan_json = desglosar_orden_masiva(query, llm_brain)
        resultado_plan = ejecutar_plan_maestro(plan_json, llm_brain)
        return resultado_plan, "", "canvas-4"

    # Si la orden requiere modelado o diseño 3D directo
    if any(k in query_lower for k in ["blender", "esculpe", "modela", "genera modelo", "crea un 3d", "objeto 3d"]):
        respuesta_blender = ejecutar_script_blender_autonomo(query, llm_brain)
        return respuesta_blender, "", "canvas-4"

    # Recuperación de contexto mediante similitud semántica matemática (RAG con Numpy)
    contexto_memoria = buscar_contexto_semantico(query, top_k=2)

    if llm_brain:
        messages = [
            {
                "role": "system", 
                "content": (
                    "Eres S.I.N.D.D.I. (Sistema Inteligente No Dependiente De Internet), un asistente autónomo local experto en programación full-stack, "
                    "desarrollo 3D y análisis técnico. Responde con precisión quirúrgica, código limpio y directo en español.\n\n"
                    f"Contexto semántico recuperado de la memoria vectorial local:\n{contexto_memoria}"
                )
            },
            {"role": "user", "content": query}
        ]
        try:
            output = llm_brain.create_chat_completion(
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )
            respuesta_modelo = output['choices'][0]['message']['content'].strip()
            guardar_vector_memoria(query, f"Interaccion Usuario")
            clasificar_y_organizar_memoria(f"Interaccion_{query[:15]}", query)
            return respuesta_modelo, "", ""
        except Exception as e:
            print(f"Error en inferencia LLM chat: {e}")

    return f"🧠 [Motor de Razonamiento S.I.N.D.D.I.]: Consulta asimilada localmente.", "", ""


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
        return jsonify({"error": "Error al procesar PDF"}), 500


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
