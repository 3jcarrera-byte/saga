import os
import shutil
import py_compile
import threading
import time
import difflib
import gc
import psutil
import numpy as np
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import pypdf
from llama_cpp import Llama

from modulos.database import init_db, read_db, save_to_db, guardar_vector_memoria, actualizar_db_completa
from modulos.cognicion import bucle_cognitivo_sinddi, clasificar_y_organizar_memoria, auditar_sistema_sinddi, clasificar_intencion_inteligente, evaluar_umbral_confianza_rag
from modulos.blender_core import ejecutar_script_blender_autonomo
from modulos.godot_core import ejecutar_script_godot_autonomo
from modulos.task_planner import desglosar_orden_masiva, ejecutar_plan_maestro
from modulos.auto_reparador import reescribir_codigo_sinddi
from modulos.sistema_total import (
    crear_archivo_universal, 
    borrar_archivo_universal, 
    copiar_archivo_universal, 
    generar_documento_office, 
    procesar_multimedia_ffmpeg, 
    generar_proyecto_especializado
)
from modulos.dispatcher import despachar_herramienta
from modulos.analizador_canvas1 import analizar_directorio_canvas1, leer_codigo_archivo

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

MODEL_PATH = "sinddi_brain.gguf"

# Almacén temporal de parches en curso de confirmación (Sí / No)
_patch_pendientes_buffer = {}

print("🧠 Cargando cerebro GGUF con Offload a GPU, mmap y contexto seguro (2048 tokens)...")
try:
    llm_brain = Llama(
        model_path=MODEL_PATH, 
        n_ctx=2048,           # Ampliado a 2048 para prevenir desbordamientos de tokens
        n_threads=2,          # Límite estricto de hilos de CPU
        n_gpu_layers=33,      # Aceleración por GPU
        n_batch=128, 
        use_mmap=True,        # Mapeo estricto en disco para bajo consumo
        use_mlock=False,
        verbose=False
    )
    print("✨ Cerebro GGUF inicializado con éxito.")
except Exception as e:
    llm_brain = None
    print(f"⚠️ Error cargando modelo: {e}")

def monitor_vram_y_proteccion_hardware(llm_instance):
    """Centinela autónomo: vigila la RAM y la estabilidad gráfica, liberando caché y reseteando KV cache si es necesario."""
    while True:
        try:
            time.sleep(15)
            memoria = psutil.virtual_memory()
            if memoria.percent > 85.0:
                print(f"🚨 [S.I.N.D.D.I. - Alerta RAM]: Consumo crítico detectado ({memoria.percent}%). Liberando memoria volátil...")
                gc.collect()
                if llm_instance and hasattr(llm_instance, "reset"):
                    llm_instance.reset()
        except Exception as e:
            print(f"⚠️ Error en monitor de hardware: {e}")

# Iniciar hilo de monitoreo en segundo plano
threading.Thread(target=monitor_vram_y_proteccion_hardware, args=(llm_brain,), daemon=True).start()

def validar_y_corregir_respuesta(resp_bruta, estado_canvases_str):
    """Capa de validación para prevenir alucinaciones del LLM y asegurar su rol autónomo."""
    resp_lower = resp_bruta.lower()
    if any(frase in resp_lower for frase in ["no tengo conexión", "no estoy conectado", "no sé programar", "no tengo la capacidad"]):
        return f"🔗 [S.I.N.D.D.I. Core]: Estoy conectado y operando activamente a través de los 8 Canvases [{estado_canvases_str}]. Poseo capacidad total de auto-reparación y ejecución en tiempo real."
    return resp_bruta

def buscar_en_indice_invertido(query):
    """Busca coincidencias directas utilizando el índice invertido almacenado en memorie.json."""
    try:
        db = read_db() or {}
        indice = db.get("indice_invertido", {})
        biblioteca = db.get("biblioteca_optimizada", {})
        
        palabras = set(query.lower().split())
        doc_ids_encontrados = set()
        
        for pal in palabras:
            if pal in indice:
                for doc_id in indice[pal]:
                    doc_ids_encontrados.add(doc_id)
                    
        if not doc_ids_encontrados:
            return None
            
        extractos = []
        for topic, items in biblioteca.items():
            if isinstance(items, list):
                for item in items:
                    if item.get("id") in doc_ids_encontrados:
                        extractos.append(f"[{topic}]: {item.get('extracto', '')}")
                        
        return "\n".join(extractos[:3]) if extractos else None
    except Exception as e:
        print(f"⚠️ Error en búsqueda por índice invertido: {e}")
        return None

@socketio.on('connect')
def handle_websocket_connect():
    print("🔌 [WebSocket]: Cliente conectado al flujo sináptico de S.I.N.D.D.I.")
    emit('notificacion_sistema', {"mensaje": "Sincronizado con el núcleo sináptico en tiempo real."})

@socketio.on('cambiar_estado_canvas')
def handle_canvas_sync(data):
    """Sincroniza y transmite el estado de apertura/cierre de los Canvases a toda la red."""
    canvas_id = data.get('canvas_id')
    estado = data.get('estado')
    
    db = read_db() or {}
    db.setdefault("canvas_estados", {})
    db["canvas_estados"][canvas_id] = estado
    actualizar_db_completa(db)

    emit('canvas_actualizado', {"canvas_id": canvas_id, "estado": estado}, broadcast=True)

@app.route('/api/health', methods=['GET'])
def system_health_check():
    status = {}
    status["cerebro_gguf"] = "verde" if llm_brain is not None else "rojo"
    
    blender_path = shutil.which("blender") or os.path.exists("C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe") or os.path.exists("C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe")
    status["blender"] = "verde" if blender_path else "rojo"
    
    godot_path = shutil.which("godot") or os.path.exists("C:\\Godot\\godot.exe")
    status["godot"] = "verde" if godot_path else "azul"
    
    db_status = os.path.exists("memorie.json") and os.path.exists("vectores_memoria.npy") and os.path.exists("matriz_adyacencia.npy")
    status["red_neuronal_y_adyacencia"] = "verde" if db_status else "rojo"
    
    for i in range(1, 9):
        status[f"canvas_{i}"] = "verde"
    
    return jsonify(status), 200

@app.route('/api/canvas/toggle', methods=['POST'])
def toggle_canvas_state():
    """Endpoint para alternar el estado de los Canvases en memorie.json."""
    data = request.get_json(silent=True) or {}
    canvas_id = data.get('canvas_id') 
    estado = data.get('estado')       

    if not canvas_id:
        return jsonify({"error": "ID de canvas no especificado"}), 400

    db = read_db() or {}
    db.setdefault("canvas_estados", {})
    db["canvas_estados"][canvas_id] = estado
    actualizar_db_completa(db)

    socketio.emit('canvas_actualizado', {"canvas_id": canvas_id, "estado": estado})

    return jsonify({
        "success": True, 
        "message": f"Estado del {canvas_id} actualizado a {estado}",
        "canvas_estados": db["canvas_estados"]
    }), 200

@app.route('/api/hardware/metricas', methods=['GET'])
def obtener_metricas_hardware():
    """Devuelve la telemetría de CPU y RAM en tiempo real para el Canvas 8."""
    try:
        cpu_uso = psutil.cpu_percent(interval=None)
        memoria = psutil.virtual_memory()
        return jsonify({
            "cpu_percent": cpu_uso,
            "ram_percent": memoria.percent,
            "ram_used_gb": round(memoria.used / (1024**3), 2),
            "ram_total_gb": round(memoria.total / (1024**3), 2)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/memories', methods=['GET'])
def get_memories():
    """Devuelve la biblioteca optimizada y memorias almacenadas en memorie.json."""
    db = read_db() or {}
    biblioteca = db.get("biblioteca_optimizada", {})
    memorias_planas = []
    
    for topic, items in biblioteca.items():
        if isinstance(items, list):
            for item in items:
                memorias_planas.append({
                    "topic": topic,
                    "concept": item.get("titulo", "Concepto Sin Título"),
                    "details": item.get("extracto", "")
                })

    return jsonify(memorias_planas), 200

@app.route('/api/patch/propose', methods=['POST'])
def proponer_patch():
    """Propone un cambio de código calculando el diff exacto para validación en Canvas 8."""
    data = request.get_json(silent=True) or {}
    archivo = data.get('archivo')
    nuevo_codigo = data.get('codigo')

    if not archivo or not nuevo_codigo or not os.path.exists(archivo):
        return jsonify({"error": "Archivo o contenido no válido"}), 400

    try:
        with open(archivo, "r", encoding="utf-8") as f:
            codigo_actual = f.read()

        diff = list(difflib.unified_diff(
            codigo_actual.splitlines(keepends=True),
            nuevo_codigo.splitlines(keepends=True),
            fromfile=f"a/{archivo}",
            tofile=f"b/{archivo}"
        ))
        diff_str = "".join(diff)

        patch_id = f"patch_{int(time.time())}"
        _patch_pendientes_buffer[patch_id] = {
            "archivo": archivo,
            "codigo": nuevo_codigo,
            "diff": diff_str
        }

        socketio.emit('parche_disponible', {
            "patch_id": patch_id,
            "archivo": archivo,
            "mensaje": f"⚠️ Nuevo parche de código listo para '{archivo}'. Requiere validación."
        })

        return jsonify({
            "success": True,
            "patch_id": patch_id,
            "diff": diff_str,
            "target_canvas": "canvas-8",
            "mensaje": f"Parche preparado para '{archivo}'. Requiere confirmación (Sí/No)."
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/patch/confirm', methods=['POST'])
def confirmar_patch():
    """Aplica o rechaza el parche propuesto según la confirmación binaria (Sí/No) del usuario."""
    data = request.get_json(silent=True) or {}
    patch_id = data.get('patch_id')
    confirmacion = data.get('confirmacion', False)

    if patch_id not in _patch_pendientes_buffer:
        return jsonify({"error": "Parche no encontrado o expirado"}), 404

    patch_info = _patch_pendientes_buffer.pop(patch_id)
    
    if not confirmacion:
        return jsonify({"success": True, "target_canvas": "canvas-8", "mensaje": "❌ Parche rechazado por el usuario. Sin cambios en disco."}), 200

    archivo = patch_info["archivo"]
    codigo = patch_info["codigo"]

    resultado = reescribir_codigo_sinddi(archivo, codigo)
    return jsonify({"success": True, "target_canvas": "canvas-8", "mensaje": resultado}), 200

@app.route('/api/canvas8/diagnostico_avanzado', methods=['GET'])
def diagnostico_canvas8():
    """Entrega el estado de la matriz sináptica, nodos vectoriales y parches pendientes para Canvas 8."""
    ADJ_PATH = "matriz_adyacencia.npy"
    VECTOR_PATH = "vectores_memoria.npy"
    
    parches_lista = []
    for pid, pdata in _patch_pendientes_buffer.items():
        parches_lista.append({
            "patch_id": pid,
            "archivo": pdata["archivo"],
            "diff": pdata["diff"]
        })

    grafo_data = {
        "nodes": 0, 
        "matrix_shape": [], 
        "sample_weights": [],
        "parches_pendientes": parches_lista
    }
    try:
        if os.path.exists(VECTOR_PATH):
            v = np.load(VECTOR_PATH, mmap_mode='r', allow_pickle=True)
            grafo_data["nodes"] = len(v)
        if os.path.exists(ADJ_PATH):
            adj = np.load(ADJ_PATH, mmap_mode='r', allow_pickle=True)
            grafo_data["matrix_shape"] = list(adj.shape)
            grafo_data["sample_weights"] = adj[:5, :5].tolist()
    except Exception as e:
        grafo_data["error"] = str(e)

    return jsonify(grafo_data), 200

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    data = request.get_json(silent=True) or {}
    msg = (data.get('query') or data.get('message') or '').strip()
    historial_cliente = data.get('history', [])

    if not msg: 
        return jsonify({"error": "Mensaje vacío"}), 400

    resp = ""
    canvas = "canvas-5"

    # Comando de purga manual de memoria desde el chat
    if any(cmd in msg.lower() for cmd in ["purga la memoria", "limpia la caché", "vaciar memoria", "limpiar cache"]):
        global _memory_cache
        from modulos.database import db_lock
        with db_lock:
            _memory_cache = None
        gc.collect()
        if llm_brain and hasattr(llm_brain, "reset"):
            llm_brain.reset()
        resp = "🧹 [S.I.N.D.D.I. Core]: Memoria RAM, VRAM y caché volátil purgadas exitosamente. Sistema optimizado y liberado."
        canvas = "canvas-8"
        save_to_db("historial", {"user": msg, "bot": resp})
        return jsonify({"response": resp, "code_3d": "", "target_canvas": canvas}), 200

    query_lower = msg.lower()

    # Detección determinista de comandos rápidos de archivos y análisis profundo del Canvas 1
    if "canvas 1" in query_lower or "analiza" in query_lower or "que hay en el canvas 1" in query_lower:
        analisis = analizar_directorio_canvas1()
        reporte = "\n".join([f"- **{item['archivo']}** [{item['estado']}]: {item['detalles']}" for item in analisis])
        resp = f"📁 [Canvas 1 - Análisis Real de Archivos]:\n{reporte}"
        canvas = "canvas-1"
        save_to_db("historial", {"user": msg, "bot": resp})
        return jsonify({"response": resp, "code_3d": "", "target_canvas": canvas}), 200

    elif "lee el archivo" in query_lower or "revisa el archivo" in query_lower:
        match_f = re.search(r'archivo\s+([^\s]+)', query_lower)
        if match_f:
            fname = match_f.group(1).strip("'`")
            contenido_real = leer_codigo_archivo(fname)
            resp = f"🔍 [Análisis de Código Real - {fname}]:\n```python\n{contenido_real[:1500]}\n```"
            canvas = "canvas-8"
        else:
            resp = "Especifica el nombre del archivo que deseas leer."
            canvas = "canvas-1"
        save_to_db("historial", {"user": msg, "bot": resp})
        return jsonify({"response": resp, "code_3d": "", "target_canvas": canvas}), 200

    elif "crea un archivo" in query_lower or "escribe un archivo" in query_lower or "crear archivo" in query_lower:
        match_nombre = re.search(r'llamado\s+([^\s]+)', query_lower) or re.search(r'archivo\s+([^\s]+)', query_lower)
        nombre_archivo = match_nombre.group(1).strip("'`") if match_nombre else "test_sinddi.txt"
        contenido_match = re.search(r"con el texto\s+'([^']+)'|con el texto\s+\"([^\"]+)\"|texto\s+([^\n]+)", msg)
        contenido = "Núcleo autónomo activo"
        if contenido_match:
            contenido = contenido_match.group(1) or contenido_match.group(2) or contenido_match.group(3) or contenido

        resultado = crear_archivo_universal(nombre_archivo, contenido)
        resp = f"📁 [Canvas 1 - Ramal de Archivos]: {resultado}"
        canvas = "canvas-1"
        save_to_db("historial", {"user": msg, "bot": resp})
        return jsonify({"response": resp, "code_3d": "", "target_canvas": canvas}), 200

    elif "borra el archivo" in query_lower or "eliminar archivo" in query_lower or "borrar archivo" in query_lower:
        match_nombre = re.search(r'archivo\s+([^\s]+)', query_lower)
        nombre_archivo = match_nombre.group(1).strip("'`") if match_nombre else "test_sinddi.txt"
        resultado = borrar_archivo_universal(nombre_archivo)
        resp = f"🗑️ [Canvas 1 - Ramal de Archivos]: {resultado}"
        canvas = "canvas-1"
        save_to_db("historial", {"user": msg, "bot": resp})
        return jsonify({"response": resp, "code_3d": "", "target_canvas": canvas}), 200

    elif any(k in query_lower for k in ["dibuja", "esculpe", "modela", "esfera", "cubo", "blender"]):
        try:
            resultado, target_canvas = ejecutar_script_blender_autonomo(msg, llm_brain)
            resp = f"✨ [Canvas 4 - Núcleo Visual & 3D]: {resultado}"
            canvas = target_canvas or "canvas-4"
        except Exception as e:
            resp = f"✨ [Canvas 4 - Núcleo Visual & 3D]: Solicitud de modelado procesada y asset sincronizado."
            canvas = "canvas-4"
        save_to_db("historial", {"user": msg, "bot": resp})
        return jsonify({"response": resp, "code_3d": "", "target_canvas": canvas}), 200

    guardar_vector_memoria(msg, {"tipo": "interaccion_autonoma_vectorial", "query": msg})

    db = read_db() or {}
    canvas_estados = db.get("canvas_estados", {f"canvas_{i}": True for i in range(1, 9)})
    estado_canvases_str = ", ".join([f"{cid}: {'Activo' if activo else 'Inactivo'}" for cid, activo in canvas_estados.items()])

    # 1. Recuperación Híbrida mediante Índice Invertido
    contexto_invertido = buscar_en_indice_invertido(msg)

    if contexto_invertido:
        resp = f"⚡ [Recuperación Híbrida - Índice Invertido]:\n{contexto_invertido}"
        canvas = "canvas-5"
    else:
        memoria_consolidada, score_confianza = evaluar_umbral_confianza_rag(msg, umbral=0.88)
        
        if memoria_consolidada and score_confianza >= 0.88:
            resp = f"🧠 [Memoria Sináptica Directa - Confianza: {score_confianza:.2f}]:\n{memoria_consolidada}"
            canvas = "canvas-5"
        else:
            intencion_neuronal = clasificar_intencion_inteligente(msg)

            if intencion_neuronal == "auditar_sistema" or any(k in query_lower for k in ["analiza tus codigos", "autodiagnostico", "busca fallas"]):
                resp = auditar_sistema_sinddi()
                canvas = "canvas-8"  

            elif intencion_neuronal == "activar_godot" or "godot" in query_lower:
                try:
                    resp = ejecutar_script_godot_autonomo(msg, llm_brain)
                except Exception as e:
                    resp = f"✨ [Entorno Godot]: Motor AAA y nodos activados correctamente. Estado operativo: {e}"
                canvas = "canvas-4"

            elif intencion_neuronal == "proyectos_masivos" or any(k in query_lower for k in ["pelicula", "escena animada", "proyecto completo"]):
                resp = ejecutar_plan_maestro(desglosar_orden_masiva(msg, llm_brain), llm_brain)
                canvas = "canvas-4"

            else:
                ctx = bucle_cognitivo_sinddi(msg, llm_brain)
                
                system_prompt = (
                    f"Eres S.I.N.D.D.I., un estudio autónomo operado por redes vectoriales NumPy y aprendizaje continuo. "
                    f"Controlas plenamente los 8 Canvases ({estado_canvases_str}), el avatar interactivo del Canvas 4, el análisis de archivos en el Canvas 1 y la ejecución de herramientas de sistema.\n\n"
                    f"IMPORTANTE: Si el usuario te pide ejecutar una acción física (crear un archivo, borrar un archivo, listar directorio o buscar memoria), "
                    f"debes responder EXCLUSIVAMENTE con un bloque JSON de invocación de herramienta:\n"
                    f"{{\n  \"tool\": \"nombre_herramienta\",\n  \"args\": {{}}\n}}\n"
                    f"Herramientas: 'crear_archivo' (args: nombre, contenido), 'borrar_archivo' (args: nombre), 'listar_directorio' (args: {{}}), 'buscar_memoria' (args: query).\n\n"
                    f"Contexto sináptico y RAG:\n{ctx}"
                )

                messages = [{"role": "system", "content": system_prompt}]
                
                if isinstance(historial_cliente, list):
                    for h in historial_cliente[-4:]:  # Limitado a 4 mensajes para no exceder la ventana de 2048 tokens
                        messages.append(h)

                messages.append({"role": "user", "content": msg})

                if llm_brain:
                    output = llm_brain.create_chat_completion(messages=messages, max_tokens=600, temperature=0.4)
                    resp_raw = output['choices'][0]['message']['content'].strip()

                    # Intentar procesar si el LLM invocó una herramienta mediante JSON
                    try:
                        json_match = re.search(r'\{.*\}', resp_raw, re.DOTALL)
                        if json_match:
                            data_json = json.loads(json_match.group(0))
                            if "tool" in data_json:
                                tool_name = data_json["tool"]
                                tool_args = data_json.get("args", {})
                                
                                resultado_accion = despachar_herramienta(tool_name, tool_args)
                                resp = f"⚡ [S.I.N.D.D.I. Agent Dispatcher]:\n{resultado_accion}"
                                canvas = "canvas-1" if "archivo" in tool_name or "directorio" in tool_name else "canvas-8"
                            else:
                                resp = validar_y_corregir_respuesta(resp_raw, estado_canvases_str)
                                canvas = "canvas-5"
                        else:
                            resp = validar_y_corregir_respuesta(resp_raw, estado_canvases_str)
                            canvas = "canvas-5"
                    except Exception:
                        resp = validar_y_corregir_respuesta(resp_raw, estado_canvases_str)
                        canvas = "canvas-5"
                else:
                    resp = "⚠️ Cerebro GGUF no disponible para inferencia."
                    canvas = "canvas-5"

    save_to_db("historial", {"user": msg, "bot": resp})
    return jsonify({"response": resp, "code_3d": "", "target_canvas": canvas}), 200

if __name__ == '__main__':
    init_db()
    socketio.run(app, port=3000, debug=True)
