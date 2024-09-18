from flask import Flask, request, jsonify
from flask_cors import CORS  # Solo si quieres habilitar CORS para permitir conexiones externas

app = Flask(__name__)
CORS(app)  # Esto permite que cualquier dispositivo se conecte al servidor

@app.route('/sensor-data', methods=['POST'])
def recibir_datos():
    data = request.json  # Recibe los datos en formato JSON
    print(f"Datos recibidos: {data}")
    
    # Aquí puedes procesar los datos (por ejemplo, guardarlos en una base de datos o archivo)
    
    return jsonify({"status": "datos recibidos"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Asegúrate de que tu servidor escuche en todas las interfaces de red
