import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import pypdf
from duckduckgo_search import DDGS

app = Flask(__name__)
CORS(app)

DB_PATH = "memorie.json"

def init_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({"documentos": [], "internet": [], "historial": []}, f, indent=4)

def save_to_db(key, entry):
    with open(DB_PATH, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        data[key].append(entry)
        f.seek(0)
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.truncate()

def read_db():
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

# --- MÓDULO DE BÚSQUEDA WEB LOCAL (DuckDuckGo) ---
def buscar_en_internet(query):
    """Busca en la web mediante órdenes del chat de forma gratuita y autónoma."""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            if results:
                textos_web = "\n".join([f"• Fuente: {r['href']}\n  Dato: {r['body']}" for r in results])
                save_to_db("internet", {"query": query, "resultado": textos_web})
                return textos_web
            return "No se encontraron resultados web recientes para esa orden."
    except Exception as e:
        print(f"Error en buscador web: {e}")
        return "No se pudo conectar a los servidores de búsqueda web en este momento."

# --- MOTOR DE COINCIDENCIA SEMÁNTICA Y RAZONAMIENTO NATIVO ---
def calcular_relevancia(texto_consulta, texto_documento):
    palabras_consulta = set(re.findall(r'\w+', texto_consulta.lower()))
    palabras_doc = re.findall(r'\w+', texto_documento.lower())
    if not palabras_consulta or not palabras_doc:
        return 0.0
    coincidencias = sum(1 for p in palabras_doc if p in palabras_consulta)
    return coincidencias / len(palabras_consulta)

def procesar_respuesta_inteligente(query, memoria):
    query_lower = query.lower()
    documentos = memoria.get("documentos", [])
    
    # 1. Orden explícita de buscar en internet a través del chat
    if any(palabra in query_lower for palabra in ["busca en internet", "investiga", "busca", "googlea", "red"]):
        # Extraer el término de búsqueda limpiando la orden
        termino = query_lower
        for p in ["busca en internet sobre", "busca en internet", "investiga sobre", "investiga", "busca", "googlea"]:
            termino = termino.replace(p, "")
        termino = termino.strip() or query
        
        resultados_web = buscar_en_internet(termino)
        return (
            f"🌐 [Exploración Web Autómata]\n"
            f"He consultado la red sobre: '{termino}'\n\n"
            f"{resultados_web}\n\n"
            f"*(Datos guardados en la memoria de internet de S.I.N.D.D.I.)*"
        )

    # 2. Búsqueda en documentos locales asimilados (Canvas 3)
    mejores_fragmentos = []
    for doc in documentos:
        contenido = doc.get("content", "")
        for frag in contenido.split('\n'):
            if len(frag.strip()) > 20:
                score = calcular_relevancia(query, frag)
                if score > 0.2:
                    mejores_fragmentos.append((score, frag))
    
    mejores_fragmentos.sort(key=lambda x: x[0], reverse=True)
    
    if mejores_fragmentos:
        contexto = "\n".join([f"- {f[1]}" for f in mejores_fragmentos[:3]])
        return (
            f"🧠 [Memoria Interna / Biblioteca]\n"
            f"Encontré estos registros relevantes en mis documentos asimilados:\n\n{contexto}"
        )
    
    # 3. Respuestas base del sistema y feedback interactivo
    if "hola" in query_lower:
        return "Hola. Soy S.I.N.D.D.I., lista para coordinar el estudio 3D, analizar PDFs o buscar en la red cuando lo ordenes."
    elif "canvas" in query_lower:
        return "Los canvas operan interconectados: Canvas 1 (Ramal), Canvas 2/7 (3D y Rigging), Canvas 3 (Biblioteca), Canvas 5 (Chat autómata) y Canvas 8 (Depurador)."
    else:
        return (
            f"He procesado tu mensaje ('{query}'), pero no hallé coincidencias exactas en mis documentos locales. "
            "Puedes ordenarme escribir **'busca en internet sobre [tema]'** para expandir mi conocimiento autónomamente."
        )

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    req_data = request.get_json(silent=True) or {}
    user_message = (req_data.get('query') or req_data.get('message') or '').strip()
    if not user_message:
        return jsonify({"error": "Mensaje vacío"}), 400

    memoria = read_db()
    bot_response = procesar_respuesta_inteligente(user_message, memoria)

    # Guardar feedback e historial de interacción
    save_to_db("historial", {"user": user_message, "bot": bot_response})
    
    return jsonify({"response": bot_response, "code_3d": "", "target_canvas": ""}), 200

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
        return jsonify({"message": f"El documento '{file.filename}' ha sido asimilado y clasificado con éxito."}), 200
    except Exception as e:
        return jsonify({"error": "Error al procesar PDF"}), 500

if __name__ == '__main__':
    init_db()
    app.run(port=3000, debug=True)
