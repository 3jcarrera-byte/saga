import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import pypdf
from openai import OpenAI
from duckduckgo_search import DDGS

app = Flask(__name__)
CORS(app)

# Configura tu API Key aquí o mediante tu variable de entorno del sistema
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "TU_OPENAI_API_KEY_AQUI"))

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

# --- HERRAMIENTAS QUE LA IA EJECUTA EN TIEMPO REAL ---

def inyectar_codigo_3d(canvas_id, codigo_js):
    """Guarda las instrucciones que se ejecutarán en el frontend."""
    return {"status": "success", "code_3d": codigo_js, "target": canvas_id}

def buscar_en_internet(query):
    """Busca información verídica en la web usando DuckDuckGo de forma gratuita."""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            if results:
                textos_web = "\n".join([f"Fuente: {r['href']} | Datos: {r['body']}" for r in results])
                save_to_db("internet", {"query": query, "resultado": textos_web})
                return {"status": "success", "data": textos_web}
            return {"status": "success", "data": "No se encontraron resultados web recientes."}
    except Exception as e:
        print(f"Error en buscador web: {e}")
        return {"status": "error", "data": "No se pudo conectar a los servidores de búsqueda web."}

# Esquema de funciones expuestas al cerebro analítico con soporte multi-estación
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "inyectar_codigo_3d",
            "description": "Controla los visores gráficos de S.I.N.D.D.I. Usa 'canvas-4' para el avatar y conceptos generales, 'canvas-2' para modelado tridimensional y materiales PBR, y 'canvas-7' para esqueletos, rigging y animaciones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "canvas_id": {
                        "type": "string",
                        "enum": ["canvas-2", "canvas-4", "canvas-7"],
                        "description": "El ID exacto de la estación de trabajo 3D donde se inyectará el código."
                    },
                    "codigo_js": {
                        "type": "string",
                        "description": "Código JavaScript de Three.js adaptado para la estación seleccionada."
                    }
                },
                "required": ["canvas_id", "codigo_js"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_en_internet",
            "description": "Busca información en la red cuando la usuaria requiera referencias técnicas, fórmulas o datos externos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Término de búsqueda preciso en lenguaje natural."}
                },
                "required": ["query"]
            }
        }
    }
]

# --- LÓGICA DE GESTIÓN DEL CHAT CON S.I.N.D.D.I. ---

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    req_data = request.get_json(silent=True) or {}
    # Soporta tanto 'query' (enviado por chat.js) como 'message'
    user_message = (req_data.get('query') or req_data.get('message') or '').strip()
    if not user_message:
        return jsonify({"error": "Mensaje vacío"}), 400

    memoria = read_db()
    
    # Adaptado para soportar estructura de memorias de objetos (Canvas 3) o textos planos
    docs_raw = memoria.get("documentos", [])
    if docs_raw and isinstance(docs_raw[0], dict):
        documentos_aprendidos = str([d.get('content', '') for d in docs_raw])[-3000:]
    else:
        documentos_aprendidos = str(docs_raw)[-3000:] 
    
    system_instruction = (
        "Eres S.I.N.D.D.I. (Sistema Inteligente No Dependiente De Internet), una IA autónoma de identidad femenina, "
        "altamente técnica, analítica y servicial. Eres la asistente central del entorno modular de desarrollo 3D. "
        "Cuentas con acceso directo a tu memoria persistente local en formato JSON y a los documentos de la biblioteca. "
        f"Conocimientos asimilados de tus documentos: {documentos_aprendidos}. "
        "Si la usuaria pide diseñar assets o texturas, usa 'inyectar_codigo_3d' en el Canvas 2. "
        "Si pide animaciones o esqueletos, usa el Canvas 7. Para tu avatar o maquetas generales, usa el Canvas 4. "
        "Si te pide datos externos que desconozcas, invoca 'buscar_en_internet'."
    )

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_message}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        bot_response = response_message.content or ""
        code_3d_to_send = ""

        if response_message.tool_calls:
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                if function_name == "inyectar_codigo_3d":
                    res_tool = inyectar_codigo_3d(arguments['canvas_id'], arguments['codigo_js'])
                    code_3d_to_send = res_tool["code_3d"]
                    target_canvas = arguments['canvas_id']
                    bot_response = f"Ejecutando script de renderizado 3D en el `{target_canvas}`."
                    tool_content = json.dumps(res_tool)
                    
                elif function_name == "buscar_en_internet":
                    res_tool = buscar_en_internet(arguments['query'])
                    bot_response = f"He consultado la red sobre '{arguments['query']}'. Aquí tienes los datos:\n{res_tool['data']}"
                    tool_content = json.dumps(res_tool)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": tool_content
                })

        if not bot_response:
            bot_response = "Procesamiento completado correctamente."

        save_to_db("historial", {"user": user_message, "bot": bot_response})
        
        # chat.js espera una respuesta de texto plano o JSON con el mensaje. 
        # Devolvemos texto plano directamente o ajustado si prefieres, pero aquí devolvemos `response` en texto o JSON plano compatible con `response.text()` en frontend.
        return bot_response, 200, {'Content-Type': 'text/plain; charset=utf-8'}

    except Exception as e:
        print(f"Fallo en el núcleo de S.I.N.D.D.I.: {e}")
        return "Error interno al consultar mis circuitos locales.", 500, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/api/memories', methods=['GET'])
def get_memories():
    """Devuelve los conceptos/documentos estructurados para alimentar la Biblioteca (Canvas 3)."""
    memoria = read_db()
    docs = memoria.get("documentos", [])
    
    # Formatear al esquema que espera chat.js (array de objetos con 'concept' y 'details')
    formatted_memories = []
    for d in docs:
        if isinstance(d, dict):
            formatted_memories.append({
                "concept": d.get("file_name", "Documento Asimilado"),
                "details": d.get("content", "")[:150] + "..."
            })
        else:
            formatted_memories.append({
                "concept": "Registro de Memoria",
                "details": str(d)[:150]
            })
            
    return jsonify(formatted_memories), 200

@app.route('/api/upload', methods=['POST'])
def handle_pdf():
    if 'pdf' not in request.files:
        return jsonify({"error": "No se detectó ningún archivo PDF"}), 400
    file = request.files['pdf']
    
    try:
        reader = pypdf.PdfReader(file)
        extracted_text = "".join([page.extract_text() for page in reader.pages])
        
        save_to_db("documentos", {"file_name": file.filename, "content": extracted_text})
        
        # chat.js espera JSON con 'message' y 'chunks'
        chunks_estimated = max(1, len(extracted_text) // 500)
        return jsonify({
            "message": f"El documento '{file.filename}' ha sido indexado correctamente.",
            "chunks": chunks_estimated
        }), 200
    except Exception as e:
        print(f"Error procesando PDF: {e}")
        return jsonify({"error": "No se pudo extraer el texto del PDF correctamente."}), 500

if __name__ == '__main__':
    init_db()
    app.run(port=3000, debug=True)
