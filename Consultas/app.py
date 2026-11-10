import os
import json
import re
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
import pypdf
from ddgs import DDGS
from llama_cpp import Llama

app = Flask(__name__)
CORS(app)

DB_PATH = "memorie.json"
MODEL_PATH = "sinddi_brain.gguf"

# --- CARGA DEL CEREBRO NATIVO EN MEMORIA (AUTONOMÍA TOTAL) ---
print("🧠 S.I.N.D.D.I. Core: Cargando el modelo GGUF directamente en RAM (CPU Ryzen)...")
try:
    # n_ctx optimizado para bajo consumo de RAM, n_threads ajustado para CPU multi-núcleo
    llm_brain = Llama(
        model_path=MODEL_PATH,
        n_ctx=2048,
        n_threads=4,
        n_batch=512,
        verbose=False
    )
    print("✨ S.I.N.D.D.I. Core: Modelo de lenguaje nativo inicializado con éxito.")
except Exception as e:
    llm_brain = None
    print(f"⚠️ S.I.N.D.D.I. Core: No se pudo cargar '{MODEL_PATH}'. Asegúrate de tener el archivo en la carpeta madre. Error: {e}")


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


# --- NÚCLEO DE ACCIÓN FÍSICA, TERMINAL Y BLENDER ---
def ejecutar_comando_terminal(comando):
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
    blender_path = r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
    if not os.path.exists(blender_path):
        return f"⚠️ No se encontró Blender en la ruta especificada: {blender_path}"
    if not os.path.exists(script_python):
        return f"⚠️ El script '{script_python}' no existe en la carpeta madre."

    comando = f'"{blender_path}" --background --python {script_python}'
    return ejecutar_comando_terminal(comando)

def generar_script_blender_dinamico(query_lower):
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
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
{geometria_bpy}
obj = bpy.context.active_object
obj.name = "{nombre_asset}"
modifier = obj.modifiers.new(name="Subdivision", type='SUBSURF')
modifier.levels = 2
modifier.render_levels = 2
for f in obj.data.polygons:
    f.use_smooth = True
export_path = "asset_sinddi.glb"
bpy.ops.export_scene.gltf(filepath=export_path, export_format='GLB')
print("✨ [SINDDI Blender Studio] Modelo exportado: " + export_path)
"""
    with open("blender_script.py", "w", encoding="utf-8") as f:
        f.write(codigo_blender)
    return f"📝 Script de Blender generado dinámicamente para: '{nombre_asset}'."


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


# --- PROCESAMIENTO AUTÓNOMO CON LLAMA.CPP Y MEMORIA ---
def procesar_respuesta_autonoma(query, memoria):
    query_lower = query.lower()

    # Comandos directos de control estructural o Blender
    if "blender" in query_lower or "esculpe" in query_lower or "modela en" in query_lower or "genera modelo en blender" in query_lower:
        info_script = generar_script_blender_dinamico(query_lower)
        resultado_blender = ejecutar_script_blender("blender_script.py")
        respuesta_final = (
            f"🎬 [S.I.N.D.D.I. Studio - Generación Nativa con Blender 4.5]\n"
            f"{info_script}\n\n```text\n{resultado_blender}\n```"
        )
        return respuesta_final, "", "canvas-4"

    # Consulta en la biblioteca local de conocimiento (Canvas 3)
    biblioteca = memoria.get("biblioteca_optimizada", {})
    palabras_clave = [p for p in query_lower.split() if len(p) > 3]
    coincidencias = []
    
    for cat, items in biblioteca.items():
        if isinstance(items, list):
            for item in items:
                texto_item = (item.get("titulo", "") + " " + item.get("extracto", "")).lower()
                if any(kw in texto_item for kw in palabras_clave):
                    coincidencias.append(f"📖 **[{cat} - {item.get('titulo')}]**:\n{item.get('extracto')}")

    contexto_memoria = "\n---\n".join(coincidencias[:2]) if coincidencias else "Sin registros previos específicos."

    # INFERENCIA NATIVA USANDO EL CEREBRO GGUF DE S.I.N.D.D.I.
    if llm_brain:
        prompt_sistema = (
            "Eres S.I.N.D.D.I., un sistema autónomo local avanzado especializado en programación, "
            "desarrollo 3D y análisis técnico. Responde de forma precisa, técnica y directa en español.\n\n"
            f"Contexto recuperado de la memoria local (memorie.json):\n{contexto_memoria}\n\n"
            f"Usuario: {query}\nS.I.N.D.D.I.:"
        )
        try:
            output = llm_brain(
                prompt_sistema,
                max_tokens=400,
                temperature=0.7,
                stop=["Usuario:", "\n\n"]
            )
            respuesta_modelo = output['choices'][0]['text'].strip()
            clasificar_y_organizar_memoria(f"Interaccion_{query[:15]}", query)
            return respuesta_modelo, "", ""
        except Exception as e:
            print(f"Error en inferencia LLM: {e}")

    # Fallback clásico por si el modelo no está cargado
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
        clasificar_y_organizar_memoria(file.filename, extracted_text)
        return jsonify({"message": f"Documento '{file.filename}' asimilado y categorizado en la biblioteca del Canvas 3."}), 200
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


if __name__ == '__main__':
    init_db()
    app.run(port=3000, debug=True)
