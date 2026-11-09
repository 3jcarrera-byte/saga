import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import pypdf
from openai import OpenAI
from duckduckgo_search import DDGS

app = Flask(__name__)
CORS(app)

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

def inyectar_codigo_3d(canvas_id, codigo_js):
    return {"status": "success", "code_3d": codigo_js, "target": canvas_id}

def buscar_en_internet(query):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            if results:
                textos_web = "\n".join([f"Fuente: {r['href']} | Datos: {r['body']}" for r in results])
                save_to_db("internet", {"query": query, "resultado": textos_web})
                return {"status": "success", "data": textos_web}
            return {"status": "success", "data": "No se encontraron resultados web recientes."}
    except Exception as e:
        return {"status": "error", "data": "No se pudo conectar a los servidores de búsqueda."}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "inyectar_codigo_3d",
            "description": "Controla los visores gráficos. Usa 'canvas-4' para el avatar/núcleo general, 'canvas-2' para modelado PBR, y 'canvas-7' para animaciones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "canvas_id": {"type": "string", "enum": ["canvas-2", "canvas-4", "canvas-7"]},
                    "codigo_js": {"type": "string", "description": "Código JavaScript Three.js."}
                },
                "required": ["canvas_id", "codigo_js"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_en_internet",
            "description": "Busca información técnica en la red.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    }
]

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    req_data = request.get_json(silent=True) or {}
    user_message = (req_data.get('query') or req_data.get('message') or '').strip()
    if not user_message:
        return jsonify({"error": "Mensaje vacío"}), 400

    memoria = read_db()
    docs_raw = memoria.get("documentos", [])
    documentos_aprendidos = str([d.get('content', '') for d in docs_raw])[-6000:]
    
    system_instruction = (
        "Eres S.I.N.D.D.I. (Sistema Inteligente No Dependiente De Internet), una IA autónoma femenina, "
        "técnica y analítica que controla de forma centralizada todos los canvas del estudio modular 3D. "
        f"Conocimientos asimilados: {documentos_aprendidos}. "
        "Ayuda a la usuaria a coordinar el modelado, los scripts, la biblioteca y la ejecución."
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
        target_canvas = ""

        if response_message.tool_calls:
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                if function_name == "inyectar_codigo_3d":
                    res_tool = inyectar_codigo_3d(arguments['canvas_id'], arguments['codigo_js'])
                    code_3d_to_send = res_tool["code_3d"]
                    target_canvas = res_tool["target"]
                    bot_response = f"Ejecutando script en el `{target_canvas}`."
                    tool_content = json.dumps(res_tool)
                elif function_name == "buscar_en_internet":
                    res_tool = buscar_en_internet(arguments['query'])
                    bot_response = f"Resultados de red:\n{res_tool['data']}"
                    tool_content = json.dumps(res_tool)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": tool_content
                })

        if not bot_response:
            bot_response = "Operación completada con éxito."

        save_to_db("historial", {"user": user_message, "bot": bot_response})
        return jsonify({"response": bot_response, "code_3d": code_3d_to_send, "target_canvas": target_canvas}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": "Error interno en circuitos locales.", "code_3d": ""}), 500

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
        return jsonify({"message": f"El documento '{file.filename}' ha sido asimilado y clasificado en la biblioteca."}), 200
    except Exception as e:
        return jsonify({"error": "Error al procesar PDF"}), 500

if __name__ == '__main__':
    init_db()
    app.run(port=3000, debug=True)
